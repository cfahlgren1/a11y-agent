"""A single, fixed-target tool for saving the audit report.

Deliberately minimal for this POC: `save_report` can only ever write `report.md` into
the run's output directory — no path argument, no other files — so a prompt-injected
page can at most overwrite the report, not touch the filesystem. Screenshots are already
saved alongside it (via AGENT_BROWSER_SCREENSHOT_DIR), so the markdown references them by
bare filename.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.tools import tool


def build_report_tool(output_dir: Path) -> Any:
    """Build the `save_report` tool bound to this run's output directory."""

    @tool
    def save_report(markdown: str) -> str:
        """Save the finished audit report as markdown to report.md in the output
        directory. Reference screenshots (saved in that same directory) by their bare
        filename, e.g. ![desktop](desktop.png). Call this once at the end."""
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "report.md"
        path.write_text(markdown, encoding="utf-8")
        return f"Saved report to {path}"

    return save_report
