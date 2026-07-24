"""Construction of the LangChain research agent."""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_nebius import ChatNebius
from langchain_tavily import TavilySearch

from .config import DEFAULT_MODEL, SYSTEM_PROMPT


def build_agent(model: str = DEFAULT_MODEL):
    """Create a streaming LangChain agent backed by Nebius and the Tavily search tool."""
    chat_model = ChatNebius(model=model, streaming=True)
    search_tool = TavilySearch()

    return create_agent(
        model=chat_model,
        tools=[search_tool],
        system_prompt=SYSTEM_PROMPT,
    )
