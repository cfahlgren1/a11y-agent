# a11y-agent

A streaming CLI agent that inspects and audits web pages for accessibility, layout,
and mobile issues. Drive it with a prompt — it searches the web (Tavily) and drives a
real headless Chromium ([agent-browser](https://github.com/vercel-labs/agent-browser))
to open pages, run axe-core audits, take and *look at* screenshots, measure elements,
emulate devices, and inspect the network, then streams a report to your terminal.

## Setup

1. Create a [Tavily API key](https://app.tavily.com).
2. Create a [Nebius API key](https://tokenfactory.nebius.com).
3. Copy `.env.example` to `.env` and fill in both keys:

   ```sh
   cp .env.example .env
   ```

4. Install `agent-browser` (an external Rust CLI, **>= 0.33.0** for the a11y audit):

   ```sh
   npm install -g agent-browser   # or: brew install agent-browser / cargo install agent-browser
   ```

   The CLI checks for it on startup and prints an install hint if it's missing or too old.

## Run

With [uv](https://docs.astral.sh/uv/) (no install step needed):

```sh
uv run main.py "take a look at example.com/pricing and show me some accessibility issues"
```

The agent chooses its own tools based on your prompt — auditing a single page, or
mapping a site and auditing a few representative pages:

```sh
uv run main.py "map the pages on example.com and audit a couple of them on mobile"
```

Or install the package and use the console script:

```sh
uv pip install -e .
a11y-agent "open example.com and run an accessibility audit"
```

Pick a different model with `--model`, or set `A11Y_AGENT_MODEL` in `.env`
(the default, Kimi K2.6, is vision-capable so it can look at screenshots):

```sh
uv run main.py --model "moonshotai/Kimi-K2.6" "..."
```

Model resolution order: `--model` flag → `A11Y_AGENT_MODEL` env var → built-in default.

## Skills

The agent itself is general — search + drive a browser. Task-specific workflows live as
**skills**: a `skills/<name>/SKILL.md` file with YAML frontmatter (`name`, `description`)
and a markdown body. At startup the agent lists each skill's name + description in its
prompt and, when a request matches, calls a `load_skill` tool to pull in the full
instructions (progressive disclosure — bodies only cost tokens when used). This is the
[SKILL.md](https://agentskills.io) open standard, so skills also work in Claude Code.

Ships with `accessibility-audit`. Add your own by dropping a new folder under `skills/`;
point elsewhere with `A11Y_AGENT_SKILLS_DIR`.

## Layout

```
skills/accessibility-audit/SKILL.md   # the a11y audit workflow (a loadable skill)
src/a11y_agent/
├── agent.py       # model + general system prompt + builds the LangChain agent
├── browser.py     # agent-browser preflight + loads its MCP tools into LangChain
├── skills.py      # discover / parse SKILL.md files + the load_skill tool
├── rendering.py   # rich rendering of the streamed tool calls / results / text
└── cli.py         # typer command, env/binary checks, wires the tools together
main.py            # thin `uv run` entry point
```
