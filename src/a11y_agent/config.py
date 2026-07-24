"""Configuration, defaults, and environment validation."""

from __future__ import annotations

import os

import typer
from dotenv import load_dotenv
from rich.console import Console

DEFAULT_MODEL = "moonshotai/Kimi-K2.6"

SYSTEM_PROMPT = """You are a concise research assistant.
Use Tavily search when you need current or factual web information.
Answer the user's question directly and include source URLs when available.
"""

# Environment variables the agent needs, with setup instructions shown when missing.
REQUIRED_ENV = {
    "TAVILY_API_KEY": (
        "Create one at https://app.tavily.com, then run: export TAVILY_API_KEY='tvly-...'"
    ),
    "NEBIUS_API_KEY": (
        "Create one at https://tokenfactory.nebius.com, then run: export NEBIUS_API_KEY='...'"
    ),
}


def load_environment() -> None:
    """Load variables from a local .env file, if present."""
    load_dotenv()


def require_env(console: Console) -> None:
    """Exit early with guidance if any required environment variable is missing."""
    for name, instructions in REQUIRED_ENV.items():
        if os.getenv(name):
            continue
        console.print(f"[bold red]Missing {name}[/bold red]")
        console.print(instructions)
        raise typer.Exit(code=1)
