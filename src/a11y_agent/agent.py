"""Construction of the LangChain agent."""

from __future__ import annotations

import os
from typing import Any

from langchain.agents import create_agent
from langchain_nebius import ChatNebius

# Kimi K2.6 is vision-capable, so one model both orchestrates tools and looks at
# screenshots — no separate vision model needed.
DEFAULT_MODEL = "moonshotai/Kimi-K2.6"

SYSTEM_PROMPT = """You are a web agent. You can search the web and drive a real \
headless browser to inspect pages and accomplish what the user asks.

Your tools:
- Tavily search to look up context or documentation.
- Tavily map to enumerate the URLs of a site when asked to look at "a site" or multiple \
pages.
- agent-browser tools to drive a real Chromium: open pages, take an accessibility-tree \
snapshot, take screenshots, run an axe-core accessibility audit, read element bounding \
boxes and computed styles, emulate devices, and inspect network requests and Core Web \
Vitals.

Work by taking concrete actions with these tools rather than guessing. Look at \
screenshots you capture, and prefer measured evidence (a selector, a bounding box, an \
audit result) over speculation. Be concise.
"""


def resolve_model(model: str | None = None) -> str:
    """Pick the model: explicit argument > A11Y_AGENT_MODEL env var > default."""
    return model or os.getenv("A11Y_AGENT_MODEL") or DEFAULT_MODEL


def compose_system_prompt(*sections: str) -> str:
    """Join the base prompt with extra sections (e.g. the skills listing)."""
    parts = [SYSTEM_PROMPT, *(s.strip() for s in sections if s and s.strip())]
    return "\n\n".join(parts)


def build_agent(tools: list[Any], model: str | None = None, system_prompt: str = SYSTEM_PROMPT):
    """Create a streaming agent over the given tools (Tavily + agent-browser + skills)."""
    chat_model = ChatNebius(model=resolve_model(model), streaming=True)
    return create_agent(
        model=chat_model,
        tools=tools,
        system_prompt=system_prompt,
    )
