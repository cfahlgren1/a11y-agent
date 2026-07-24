"""Construction of the LangChain research agent."""

from __future__ import annotations

import os

from langchain.agents import create_agent
from langchain_nebius import ChatNebius
from langchain_tavily import TavilySearch

DEFAULT_MODEL = "moonshotai/Kimi-K2.6"

SYSTEM_PROMPT = """You are a concise research assistant.
Use Tavily search when you need current or factual web information.
Answer the user's question directly and include source URLs when available.
"""


def resolve_model(model: str | None = None) -> str:
    """Pick the model: explicit argument > A11Y_AGENT_MODEL env var > default."""
    return model or os.getenv("A11Y_AGENT_MODEL") or DEFAULT_MODEL


def build_agent(model: str | None = None):
    """Create a streaming LangChain agent backed by Nebius and the Tavily search tool."""
    chat_model = ChatNebius(model=resolve_model(model), streaming=True)
    search_tool = TavilySearch()

    return create_agent(
        model=chat_model,
        tools=[search_tool],
        system_prompt=SYSTEM_PROMPT,
    )
