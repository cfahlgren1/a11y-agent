# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "langchain>=1.0.0",
#   "langchain-mcp-adapters>=0.3.0",
#   "langchain-nebius>=0.1.0",
#   "langchain-tavily>=0.2.0",
#   "python-dotenv>=1.0.0",
#   "python-frontmatter>=1.1.0",
#   "rich>=13.0.0",
#   "typer>=0.12.0",
# ]
# ///
"""Runnable entry point: `uv run main.py "your question"`.

Keeps the single-file `uv run` workflow from the original starter while the real
implementation lives in the `a11y_agent` package under `src/`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from a11y_agent.cli import app

if __name__ == "__main__":
    app()
