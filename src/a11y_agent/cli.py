"""Typer CLI entry point for the accessibility agent."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from langchain_tavily import TavilyMap, TavilySearch
from rich.console import Console
from rich.panel import Panel

from .agent import build_agent, compose_system_prompt
from .browser import browser_tools, check_agent_browser
from .rendering import StreamRenderer
from .report import build_report_tool
from .skills import build_load_skill_tool, load_skills, render_listing

app = typer.Typer(add_completion=False)
console = Console()

# Environment variables the agent needs, with setup instructions shown when missing.
REQUIRED_ENV = {
    "TAVILY_API_KEY": (
        "Create one at https://app.tavily.com, then run: export TAVILY_API_KEY='tvly-...'"
    ),
    "NEBIUS_API_KEY": (
        "Create one at https://tokenfactory.nebius.com, then run: export NEBIUS_API_KEY='...'"
    ),
}


def require_env() -> None:
    """Exit early with guidance if any required environment variable is missing."""
    for name, instructions in REQUIRED_ENV.items():
        if os.getenv(name):
            continue
        console.print(f"[bold red]Missing {name}[/bold red]")
        console.print(instructions)
        raise typer.Exit(code=1)


def require_agent_browser() -> None:
    """Exit early with an install hint if the agent-browser binary is missing/too old."""
    error = check_agent_browser()
    if error:
        console.print(f"[bold red]{error}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def main(
    question: Annotated[list[str], typer.Argument(help="What to look at / ask")],
    model: Annotated[
        str | None,
        typer.Option(
            help="Model name (defaults to A11Y_AGENT_MODEL env var, then a built-in default)"
        ),
    ] = None,
    auto_connect: Annotated[
        bool,
        typer.Option(
            "--auto-connect",
            help="Attach to your already-running Chrome (reuse its cookies/login) instead "
            "of launching a fresh browser. Start Chrome with --remote-debugging-port first.",
        ),
    ] = False,
) -> None:
    """Drive a browser-equipped agent with a prompt to inspect and audit web pages."""
    load_dotenv()
    require_env()
    require_agent_browser()

    if auto_connect:
        # Downstream: browser.py forwards this to the MCP subprocess and skips the
        # session close so we never shut down the user's own Chrome.
        os.environ["AGENT_BROWSER_AUTO_CONNECT"] = "1"

    question_text = " ".join(question)
    output_dir = _prepare_output_dir()

    console.print(Panel.fit(question_text, title="Prompt", border_style="cyan"))
    console.rule("[bold blue]Agent stream")

    try:
        asyncio.run(_run(question_text, model, output_dir))
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted.[/red]")
        raise typer.Exit(code=130) from None
    except Exception as exc:  # noqa: BLE001 - top-level CLI boundary
        console.print(f"\n[bold red]Agent run failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from None
    finally:
        report = output_dir / "report.md"
        if report.exists():
            console.print()
            console.print(Panel.fit(str(report), title="Report saved", border_style="green"))


def _prepare_output_dir() -> Path:
    """Resolve the output directory (default ./results), create it, and point
    agent-browser's screenshots there unless the user overrode the location."""
    override = os.environ.get("AGENT_BROWSER_SCREENSHOT_DIR")
    output_dir = (Path(override) if override else Path("results")).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    os.environ["AGENT_BROWSER_SCREENSHOT_DIR"] = str(output_dir)
    return output_dir


async def _run(question_text: str, model: str | None, output_dir: Path) -> None:
    """Load skills + browser tools, build the agent, and stream the run."""
    skills = load_skills()
    output_note = (
        "# Output directory\n"
        f"Screenshots are saved into this absolute directory: {output_dir}\n"
        "Save the final report with the save_report tool (writes report.md there) and "
        "reference screenshots by their bare filename."
    )
    system_prompt = compose_system_prompt(render_listing(skills), output_note)

    async with browser_tools() as browser:
        tools = [TavilySearch(), TavilyMap(), *browser, build_report_tool(output_dir)]
        if skills:
            tools.append(build_load_skill_tool(skills))
        agent = build_agent(tools, model=model, system_prompt=system_prompt)
        stream = agent.astream(
            {"messages": [{"role": "user", "content": question_text}]},
            stream_mode=["messages", "updates"],
        )
        await StreamRenderer(console).arender(stream)


if __name__ == "__main__":
    app()
