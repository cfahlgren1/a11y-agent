"""Typer CLI entry point for the accessibility agent."""

from __future__ import annotations

import asyncio
import os
from typing import Annotated, Optional

import typer
from dotenv import load_dotenv
from langchain_tavily import TavilyMap, TavilySearch
from rich.console import Console
from rich.panel import Panel

from .agent import build_agent
from .browser import browser_tools, check_agent_browser
from .rendering import StreamRenderer

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
        Optional[str],
        typer.Option(help="Model name (defaults to A11Y_AGENT_MODEL env var, then a built-in default)"),
    ] = None,
) -> None:
    """Drive a browser-equipped agent with a prompt to inspect and audit web pages."""
    load_dotenv()
    require_env()
    require_agent_browser()

    question_text = " ".join(question)

    console.print(Panel.fit(question_text, title="Prompt", border_style="cyan"))
    console.rule("[bold blue]Agent stream")

    try:
        asyncio.run(_run(question_text, model))
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted.[/red]")
        raise typer.Exit(code=130) from None
    except Exception as exc:
        console.print(f"\n[bold red]Agent run failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from None


async def _run(question_text: str, model: Optional[str]) -> None:
    """Load browser tools over MCP, build the agent, and stream the run."""
    async with browser_tools() as browser:
        tools = [TavilySearch(), TavilyMap(), *browser]
        agent = build_agent(tools, model=model)
        stream = agent.astream(
            {"messages": [{"role": "user", "content": question_text}]},
            stream_mode=["messages", "updates"],
        )
        await StreamRenderer(console).arender(stream)


if __name__ == "__main__":
    app()
