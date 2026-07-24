"""Typer CLI entry point for the research agent."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from .agent import build_agent
from .config import DEFAULT_MODEL, load_environment, require_env
from .rendering import StreamRenderer

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(
    question: Annotated[list[str], typer.Argument(help="Question")],
    model: Annotated[str, typer.Option(help="Model name")] = DEFAULT_MODEL,
) -> None:
    """Ask a question and stream a small LangChain agent that searches with Tavily."""
    load_environment()
    require_env(console)

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
