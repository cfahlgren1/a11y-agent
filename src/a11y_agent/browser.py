"""Bridge to the `agent-browser` MCP server.

`agent-browser` is a Rust CLI that drives a real headless Chromium and exposes its
capabilities (accessibility snapshots, screenshots, axe-core audits, bounding boxes,
device emulation, network/HAR, Core Web Vitals) as MCP tools. We run it as a
subprocess over stdio and load its tools into LangChain.

The server talks to a persistent daemon that holds the browser session open, so a
single MCP session keeps page state (navigation, viewport, cookies) across tool
calls within one run.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import re
import shutil
import subprocess
from collections.abc import AsyncIterator
from typing import Any

from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import get_default_environment, stdio_client

# The `a11y` (axe-core) MCP tool was introduced in this release; older binaries would
# silently lack it, so we gate on it.
MINIMUM_VERSION = (0, 33, 0)

# Tool profile agent-browser exposes over MCP. "all" is the full typed surface
# (~150 tools across paginated pages) including a11y, network, vitals, and device
# emulation. See the profile tradeoff note in the plan if tool selection degrades.
DEFAULT_TOOL_PROFILE = "all"

# A tool that only appears on a later pagination page of the "all" profile — used to
# confirm the MCP client actually followed `nextCursor` and loaded the full surface.
SENTINEL_TOOL = "agent_browser_a11y"

_INSTALL_HINT = (
    "Install it with one of:\n"
    "  npm install -g agent-browser\n"
    "  brew install agent-browser\n"
    "  cargo install agent-browser"
)


def _server_env() -> dict[str, str]:
    """Environment for the MCP subprocess.

    The MCP stdio client otherwise passes only a minimal safe env (PATH, HOME, ...),
    which would drop agent-browser's own configuration. Forward every `AGENT_BROWSER_*`
    variable so users can configure the browser — e.g. `AGENT_BROWSER_AUTO_CONNECT=1`
    to reuse a logged-in Chrome — without us leaking unrelated secrets (API keys).
    """
    env = get_default_environment()
    env.update({k: v for k, v in os.environ.items() if k.startswith("AGENT_BROWSER_")})
    return env


def _parse_version(text: str) -> tuple[int, ...] | None:
    """Extract a (major, minor, patch) tuple from `agent-browser --version` output."""
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def check_agent_browser() -> str | None:
    """Return an error+hint string if agent-browser is missing or too old, else None.

    Kept free of typer/console coupling so it stays easy to test and reuse.
    """
    if shutil.which("agent-browser") is None:
        return f"agent-browser not found on PATH.\n{_INSTALL_HINT}"

    try:
        result = subprocess.run(
            ["agent-browser", "--version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"Could not run 'agent-browser --version': {exc}\n{_INSTALL_HINT}"

    version = _parse_version(result.stdout or result.stderr)
    if version is None:
        return f"Could not parse agent-browser version from: {result.stdout!r}"

    if version < MINIMUM_VERSION:
        need = ".".join(map(str, MINIMUM_VERSION))
        have = ".".join(map(str, version))
        return (
            f"agent-browser {have} is too old; the accessibility audit tool needs "
            f">= {need}.\nUpgrade with: npm install -g agent-browser@latest"
        )
    return None


def _expects_sentinel(profile: str) -> bool:
    """Whether SENTINEL_TOOL should be present for this profile.

    The a11y tool lives in the `debug` profile (and thus in `all`); only those span
    enough tools that pagination matters. Narrower profiles legitimately omit it.
    """
    parts = {part.strip() for part in profile.split(",")}
    return "all" in parts or "debug" in parts


def _is_autoconnect() -> bool:
    """True when attached to the user's own Chrome — we must not close their browser."""
    return bool(os.getenv("AGENT_BROWSER_AUTO_CONNECT"))


async def _close_browser(session: ClientSession) -> None:
    """Best-effort close of the browser session so Chromium/page state don't leak.

    Skipped under autoconnect (that's the user's Chrome). Bounded by a timeout and
    swallows errors — cleanup must never mask the original outcome."""
    if _is_autoconnect():
        return
    with contextlib.suppress(Exception):
        await asyncio.wait_for(session.call_tool("agent_browser_close", {}), timeout=10)


@contextlib.asynccontextmanager
async def browser_tools(profile: str = DEFAULT_TOOL_PROFILE) -> AsyncIterator[list[Any]]:
    """Start `agent-browser mcp` and yield its tools as LangChain tools.

    Usage:
        async with browser_tools() as tools:
            agent = build_agent([*other_tools, *tools])
            ...

    On exit — success, error, or interrupt — the browser session is closed and the MCP
    subprocess is torn down.
    """
    server = StdioServerParameters(
        command="agent-browser",
        args=["mcp", "--tools", profile],
        env=_server_env(),
    )
    async with stdio_client(server) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = await load_mcp_tools(session)

        names = {tool.name for tool in tools}
        if _expects_sentinel(profile) and SENTINEL_TOOL not in names:
            raise RuntimeError(
                f"agent-browser MCP loaded {len(tools)} tools but '{SENTINEL_TOOL}' "
                "is missing — the client likely did not follow tool-list pagination. "
                "Upgrade langchain-mcp-adapters so it pages through nextCursor."
            )
        try:
            yield tools
        finally:
            await _close_browser(session)
