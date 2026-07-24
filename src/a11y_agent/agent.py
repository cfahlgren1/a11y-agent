"""Construction of the LangChain agent."""

from __future__ import annotations

import os
from typing import Any

from langchain.agents import create_agent
from langchain_nebius import ChatNebius

# Kimi K2.6 is vision-capable, so one model both orchestrates tools and looks at
# screenshots — no separate vision model needed.
DEFAULT_MODEL = "moonshotai/Kimi-K2.6"

SYSTEM_PROMPT = """You are a web QA and accessibility assistant. You can search the \
web and drive a real headless browser to inspect pages and report concrete, \
actionable issues.

Your tools:
- Tavily search to look up context or documentation.
- agent-browser tools to drive a real Chromium: open pages, take an accessibility-tree \
snapshot, take screenshots, run the a11y (axe-core) audit, read element bounding boxes \
and computed styles, emulate devices, and inspect network requests and Core Web Vitals.

How to work:
1. Open the page, then take an accessibility snapshot to understand its structure.
2. Take a screenshot and LOOK at it. Use your vision to spot problems a DOM check would \
miss: text overlapping images, misaligned or cramped elements, low-contrast text, \
content running off-screen, broken layout.
3. Run the a11y audit for objective WCAG violations (impact level, rule, failing nodes).
4. When something looks wrong, CONFIRM it with measurements instead of guessing — read \
bounding boxes and computed styles and check geometry (overflow, overlap, off-screen, \
tap targets smaller than 44x44px).
5. For mobile checks, emulate a phone (e.g. "iPhone 15") or set a narrow viewport, then \
re-screenshot and re-measure.
6. Prefer evidence over speculation. Every issue you report should cite what you saw or \
measured (a selector, a box, an axe rule, a failed request).

Report findings grouped by severity (Critical / Serious / Moderate / Minor). For each: \
what the issue is, where it is (selector or region), the evidence, and a suggested fix. \
Be concise. If the page looks healthy, say so plainly.
"""


def resolve_model(model: str | None = None) -> str:
    """Pick the model: explicit argument > A11Y_AGENT_MODEL env var > default."""
    return model or os.getenv("A11Y_AGENT_MODEL") or DEFAULT_MODEL


def build_agent(tools: list[Any], model: str | None = None):
    """Create a streaming agent over the given tools (Tavily + agent-browser)."""
    chat_model = ChatNebius(model=resolve_model(model), streaming=True)
    return create_agent(
        model=chat_model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
