"""Typer CLI entry point for the research agent."""

from __future__ import annotations

import os
from typing import Annotated, Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from .agent import build_agent
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


@app.command()
def main(
    question: Annotated[list[str], typer.Argument(help="Question")],
    model: Annotated[
        Optional[str],
        typer.Option(help="Model name (defaults to A11Y_AGENT_MODEL env var, then a built-in default)"),
    ] = None,
) -> None:
    """Ask a question and stream a small LangChain agent that searches with Tavily."""
    load_dotenv()
    require_env()

    question_text = " ".join(question)
    agent = build_agent(model=model)

    console.print(Panel.fit(question_text, title="Question", border_style="cyan"))
    console.rule("[bold blue]Agent stream")

    try:
        stream = agent.stream(
            {"messages": [{"role": "user", "content": question_text}]},
            stream_mode=["messages", "updates"],
        )
        StreamRenderer(console).render(stream)
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted.[/red]")
        raise typer.Exit(code=130) from None
    except Exception as exc:
        console.print(f"\n[bold red]Agent run failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    app()
