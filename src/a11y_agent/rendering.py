"""Rich-based rendering of the agent's streamed output."""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def message_text(message: Any) -> str:
    """Extract streamed text from a LangChain message or message chunk."""
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)
    return ""


def truncate(value: Any, limit: int = 900) -> str:
    text = str(value).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def format_tool_result(content: Any) -> str:
    """Render a Tavily tool result into a readable, ranked list of sources."""
    try:
        payload = json.loads(content) if isinstance(content, str) else content
    except json.JSONDecodeError:
        return truncate(content)

    if not isinstance(payload, dict) or "results" not in payload:
        return truncate(payload)

    lines = [f"Query: {payload.get('query', '')}", ""]
    for index, result in enumerate(payload.get("results", [])[:5], start=1):
        title = result.get("title", "Untitled")
        url = result.get("url", "")
        snippet = " ".join(result.get("content", "").split())
        lines.append(f"{index}. {title}")
        lines.append(f"   {url}")
        if snippet:
            lines.append(f"   {truncate(snippet, limit=220)}")
        lines.append("")
    return "\n".join(lines).strip()


class StreamRenderer:
    """Consume an agent stream and render tool calls, results, and text to the console."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self._tool_buffers: dict[str, dict[str, str]] = {}
        self._printed_tool_calls: set[str] = set()
        self._assistant_started = False
        self._last_event_was_text = False

    def _flush(self) -> None:
        self.console.file.flush()

    def render(self, stream: Any) -> None:
        """Iterate a sync agent stream (`.stream`) and render each event."""
        for mode, data in stream:
            self._render_event(mode, data)
        self._finish()

    async def arender(self, stream: Any) -> None:
        """Iterate an async agent stream (`.astream`, needed for MCP-backed tools)."""
        async for mode, data in stream:
            self._render_event(mode, data)
        self._finish()

    def _render_event(self, mode: str, data: Any) -> None:
        if mode == "messages":
            self._render_message_chunk(data)
        elif mode == "updates":
            self._render_update(data)

    def _finish(self) -> None:
        if self._last_event_was_text:
            self.console.print()

    def _render_message_chunk(self, data: Any) -> None:
        message, _metadata = data

        # Full tool messages arrive via the "updates" stream; skip them here.
        if getattr(message, "type", None) == "tool":
            return

        tool_call_chunks = getattr(message, "tool_call_chunks", []) or []
        if tool_call_chunks:
            self._render_tool_call_chunks(tool_call_chunks)
            return

        text = message_text(message)
        if text:
            self._render_assistant_text(text)

    def _render_tool_call_chunks(self, tool_call_chunks: list[dict[str, Any]]) -> None:
        if self._last_event_was_text:
            self.console.print()
            self._last_event_was_text = False

        for chunk in tool_call_chunks:
            key = str(chunk.get("id") or chunk.get("index") or "tool_call")
            buffer = self._tool_buffers.setdefault(key, {"name": "", "args": ""})

            if chunk.get("name"):
                buffer["name"] += chunk["name"]
            if chunk.get("args"):
                buffer["args"] += chunk["args"]

            if key not in self._printed_tool_calls and buffer["name"]:
                self._printed_tool_calls.add(key)
                self.console.print(
                    f"\n[bold yellow]Tool call[/bold yellow] [yellow]{buffer['name']}[/yellow]",
                    highlight=False,
                )
                self.console.print("[dim yellow]args: [/dim yellow]", end="")

            if chunk.get("args"):
                self.console.print(chunk["args"], style="yellow", end="", highlight=False)
                self._flush()

    def _render_assistant_text(self, text: str) -> None:
        if not self._assistant_started:
            if self._printed_tool_calls:
                self.console.print()
            self.console.print("\n[bold green]Assistant[/bold green]")
            self._assistant_started = True
        self.console.print(text, end="", highlight=False, markup=False)
        self._flush()
        self._last_event_was_text = True

    def _render_update(self, data: Any) -> None:
        for node_update in data.values():
            for message in node_update.get("messages", []):
                if getattr(message, "type", None) == "ai":
                    self._render_tool_calls(message)
                elif getattr(message, "type", None) == "tool":
                    self._print_tool_result(message)

    def _render_tool_calls(self, message: Any) -> None:
        for tool_call in getattr(message, "tool_calls", []) or []:
            key = str(tool_call.get("id") or tool_call.get("name") or "tool_call")
            if key in self._printed_tool_calls:
                continue
            self._printed_tool_calls.add(key)
            self._print_tool_call(
                tool_call.get("name", "tool"),
                tool_call.get("args", {}),
            )

    def _print_tool_call(self, name: str, args: Any) -> None:
        self.console.print()
        self.console.print(
            Panel(
                Text(truncate(args, limit=700)),
                title=f"Tool call: {name}",
                border_style="yellow",
            )
        )

    def _print_tool_result(self, message: Any) -> None:
        if self._last_event_was_text:
            self.console.print()
            self._last_event_was_text = False
        name = getattr(message, "name", None) or "tool"
        content = format_tool_result(getattr(message, "content", ""))
        self.console.print()
        self.console.print(
            Panel(
                Text(content),
                title=f"Tool result: {name}",
                border_style="yellow",
            )
        )
