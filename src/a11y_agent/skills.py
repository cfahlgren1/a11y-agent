"""Discover and load markdown-defined skills.

A skill is a directory under `skills/` with a `SKILL.md` file: YAML frontmatter
(`name`, `description`) plus a markdown body describing a repeatable flow. Following
progressive disclosure, only the name + description are injected into the system prompt
(cheap, always present); the full body is loaded on demand when the model calls the
`load_skill` tool. This is the SKILL.md open standard, so skills authored here also work
in Claude Code / claude.ai.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter
from langchain_core.tools import tool

# Built-in skills ship inside the package so installed wheels aren't skill-less.
BUILTIN_SKILLS_DIR = Path(__file__).resolve().parent / "builtin_skills"


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    body: str
    path: Path


def skill_roots() -> list[Path]:
    """Directories to scan: packaged built-ins, then an optional user dir that can add
    to or override them via A11Y_AGENT_SKILLS_DIR (later roots win on name clash)."""
    roots = [BUILTIN_SKILLS_DIR]
    override = os.getenv("A11Y_AGENT_SKILLS_DIR")
    if override:
        roots.append(Path(override))
    return roots


def load_skills(roots: list[Path] | None = None) -> dict[str, Skill]:
    """Discover `*/SKILL.md` across `roots` and parse each into a Skill, keyed by name."""
    skills: dict[str, Skill] = {}
    for root in roots or skill_roots():
        if not root.is_dir():
            continue
        for skill_md in sorted(root.glob("*/SKILL.md")):
            post = frontmatter.load(str(skill_md))
            name = str(post.get("name") or skill_md.parent.name).strip()
            description = str(post.get("description") or "").strip()
            skills[name] = Skill(name, description, post.content.strip(), skill_md)
    return skills


def render_listing(skills: dict[str, Skill]) -> str:
    """Render the always-on `name: description` listing for the system prompt."""
    if not skills:
        return ""
    lines = "\n".join(f"- {s.name}: {s.description}" for s in skills.values())
    return (
        "# Available skills\n"
        f"{lines}\n\n"
        "When a skill matches the request, call load_skill(name) to load its full "
        "instructions before proceeding."
    )


def build_load_skill_tool(skills: dict[str, Skill]) -> Any:
    """Build the `load_skill` tool the model calls to pull in a skill's full body."""

    @tool
    def load_skill(name: str) -> str:
        """Load the full instructions for a skill by name. Call this when a skill from
        the available-skills list matches the user's request, before proceeding."""
        skill = skills.get(name)
        if skill is None:
            available = ", ".join(skills) or "(none)"
            return f"No skill named {name!r}. Available skills: {available}."
        return skill.body

    return load_skill
