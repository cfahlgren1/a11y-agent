# a11y-agent

A small streaming research agent CLI built on LangChain, Nebius, and Tavily. Ask a
question and watch the agent search the web and stream its answer to the terminal.

## Setup

1. Create a [Tavily API key](https://app.tavily.com).
2. Create a [Nebius API key](https://tokenfactory.nebius.com).
3. Copy `.env.example` to `.env` and fill in both keys:

   ```sh
   cp .env.example .env
   ```

## Run

With [uv](https://docs.astral.sh/uv/) (no install step needed):

```sh
uv run main.py "What are the latest trends in agent evaluation?"
```

Or install the package and use the console script:

```sh
uv pip install -e .
a11y-agent "What are the latest trends in agent evaluation?"
```

Pick a different model with `--model`, or set `A11Y_AGENT_MODEL` in `.env`:

```sh
uv run main.py --model "moonshotai/Kimi-K2.6" "..."
```

Model resolution order: `--model` flag → `A11Y_AGENT_MODEL` env var → built-in default.

## Layout

```
src/a11y_agent/
├── agent.py       # model + system prompt + builds the LangChain agent
├── rendering.py   # rich rendering of the streamed tool calls / results / text
└── cli.py         # typer command, env loading/validation, wires it together
main.py            # thin `uv run` entry point
```
