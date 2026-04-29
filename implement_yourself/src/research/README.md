# Deep Research MCP Server

A FastMCP server that provides any MCP-compatible agent (Claude Code, Cursor, etc.) with deep web research capabilities and YouTube video analysis. It uses Google Gemini with Google Search grounding for factual queries and Gemini's native video understanding for YouTube URLs. All results are accumulated on disk so a final `compile_research` call can assemble them into a structured `research.md` brief.

## Prerequisites

- Python 3.12 or later (see [`.python-version`](../../.python-version))
- `uv` for virtual environment and dependency management ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- GNU Make (pre-installed on macOS/Linux; `choco install make` on Windows)
- Google AI Studio API key ([aistudio.google.com/apikey](https://aistudio.google.com/apikey))
- (Optional) Opik account and workspace for observability ([comet.com/site/products/opik](https://www.comet.com/site/products/opik/))
- An MCP-compatible harness: Claude Code, Cursor, or similar

## Installation

From the `implement_yourself/` project root, run:

```bash
uv sync
```

This resolves all dependencies declared in `pyproject.toml` and creates an isolated `.venv/` virtual environment under the project root. All subsequent `make` and `uv run` commands automatically use that environment.

## Configuration

Copy the template and fill in your keys:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | Yes | — | Google AI Studio API key. Used for all Gemini calls (grounded search and video analysis). |
| `OPIK_API_KEY` | No | — | Enables Opik observability tracing. Wired in task #020; leave blank until then. |
| `OPIK_WORKSPACE` | No | — | Opik workspace name (only used when `OPIK_API_KEY` is set). |
| `OPIK_PROJECT_NAME` | No | `research-agent` | Opik project label for grouping traces. |
| `LOG_LEVEL` | No | `20` (INFO) | Python integer logging level: `10`=DEBUG, `20`=INFO, `30`=WARNING. |

Settings are loaded by `src/research/config/settings.py` via Pydantic Settings. Unknown keys in `.env` are silently ignored.

## Architecture Overview

The agent (running in the MCP harness) holds the ReAct loop. The MCP server only provides tool capabilities.

```
User prompt
    │
    ▼
┌──────────────────────────────────────┐
│          Agent (Claude Code)          │
│  1. Breaks topic into queries         │
│  2. Calls tools, reads results        │
│  3. Identifies gaps, digs deeper      │
│  4. Calls compile_research            │
└────────────┬──────────┬──────────────┘
             │          │          │
             ▼          ▼          ▼
   ┌──────────────┐ ┌──────────┐ ┌───────────────┐
   │deep_research │ │analyze_  │ │compile_       │
   │Gemini +      │ │youtube_  │ │research       │
   │Google Search │ │video     │ │               │
   │grounding     │ │Gemini +  │ │Assembles all  │
   │              │ │native    │ │results into   │
   │answer+sources│ │video     │ │research.md    │
   └──────────────┘ └──────────┘ └───────────────┘
```

**Call chain:** `routers/ → tools/ → app/ → utils/`

- **`routers/`** — Registers tools, prompts, and resources with FastMCP.
- **`tools/`** — Validate inputs, invoke business logic, read/write working-dir files.
- **`app/`** — Business logic: the actual Gemini API calls.
- **`utils/`** — Shared helpers (Gemini client, file I/O, markdown, logging, Opik).

```
src/research/
├── server.py                          # FastMCP entry point
├── routers/                           # MCP registration layer
│   ├── tools.py                       #   registers 3 tools
│   ├── prompts.py                     #   registers 1 prompt
│   └── resources.py                   #   registers 1 resource
├── tools/                             # Tool implementations
│   ├── deep_research_tool.py
│   ├── analyze_youtube_video_tool.py
│   └── compile_research_tool.py
├── app/                               # Business logic
│   ├── research_handler.py
│   ├── youtube_handler.py
│   └── research_file_handler.py
├── config/
│   ├── settings.py                    # Pydantic Settings (env vars, model names)
│   ├── constants.py                   # File/folder name constants
│   └── prompts.py                     # LLM prompt templates
├── models/
│   └── schemas.py                     # ResearchSource, ResearchResult
└── utils/
    ├── llm.py                         # Gemini client helpers
    ├── file_utils.py
    ├── markdown_utils.py
    ├── logging.py
    └── opik_utils.py
```

## MCP Primitives

| Type | Name | Purpose |
|---|---|---|
| **Tool** | `deep_research` | Calls Gemini with Google Search grounding. Returns answer + sources; appends to `.memory/research_results.json`. |
| **Tool** | `analyze_youtube_video` | Passes a YouTube URL to Gemini via native `FileData` video understanding. Saves transcript to `.memory/transcripts/{video_id}.md`. |
| **Tool** | `compile_research` | Reads all accumulated `.memory/` data and writes the final `research.md`. Resets the exploration budget. |
| **Prompt** | `research_workflow` | Guides the agent through the three-tool sequence with sensible defaults. |
| **Resource** | `resource://config/research` | Exposes server config: model names, version, feature flags. |

All tools accept a `working_dir` parameter that scopes all file I/O to the research session directory.

## Running the Server

**Start via Make (stdio transport, for harness integration):**

```bash
make run-research-server
```

The server speaks the MCP stdio protocol. A connected harness (Claude Code, Cursor) communicates through stdin/stdout.

**Run the e2e smoke test directly (bypasses MCP transport):**

```bash
make test-research-workflow
```

This copies a dataset seed to `test_logic/`, then calls the same handlers the MCP tools call, and writes results to `test_logic/research.md`.

**Auto-launch from harness via `.mcp.json`:**

The `implement_yourself/.mcp.json` file registers the server under the name `deep-research`:

```json
{
  "mcpServers": {
    "deep-research": {
      "command": "uv",
      "args": ["run", "fastmcp", "run", "src/research/server.py"],
      "env": { "ENV_FILE_PATH": ".env" }
    }
  }
}
```

Open the harness with `implement_yourself/` as the working directory and it picks up this file automatically.

## Using the `/research` Skill

The `/research` skill is a high-level slash command available inside the harness. It orchestrates `deep_research`, `analyze_youtube_video`, and `compile_research` end-to-end without requiring you to call each tool manually.

Invoke it with a topic or let the harness detect a research intent:

```
/research <topic>
```

Output lands in `outputs/{slug}/research.md` where `{slug}` is a kebab-case slug derived from the topic string (spaces replaced with hyphens, lowercased). For example, researching "AI agent architectures" produces `outputs/ai-agent-architectures/research.md`.

For a full pipeline that continues to a LinkedIn post, use `/research-and-write`. See [`../../README.md`](../../README.md) for the skill catalogue.

## Make Targets

| Target | Description |
|---|---|
| `run-research-server` | Boot the Deep Research MCP server (stdio transport). Use for harness integration. |
| `test-research-workflow` | Run the research pipeline on a dataset seed. Output: `test_logic/research.md`. |
| `format-fix` | Auto-format Python source with ruff formatter. |
| `lint-fix` | Auto-fix linting issues with ruff linter. |
| `format-check` | Check formatting without modifying files. Exits non-zero on any violation. |
| `lint-check` | Check for linting issues without fixing. Exits non-zero on any violation. |

## Output Layout

After a research session the working directory contains:

```
working_dir/
├── .memory/
│   ├── exploration_state.json         # Tracks call count against the budget
│   ├── research_results.json          # Accumulated results from deep_research calls
│   └── transcripts/
│       └── {video_id}.md              # One file per analyzed YouTube video
└── research.md                        # Final compiled output (created by compile_research)
```

## Exploration Budget

The agent may run at most 6 exploration calls (`deep_research` + `analyze_youtube_video` combined) per session before being forced to call `compile_research`. The cap is enforced server-side via `.memory/exploration_state.json` and reset by `compile_research`. Each successful response carries `call`, `max_calls`, and `calls_remaining` fields so the agent can self-pace and avoid hitting the ceiling unexpectedly.

## Observability (Optional)

Setting `OPIK_API_KEY` enables Opik tracing of every Gemini call made by the server. Traces are grouped by project under `OPIK_PROJECT_NAME` (default: `research-agent`) and show full LLM input/output, latency, and token usage. This integration is wired in task #020; without that task complete the variable is read but no tracing occurs. See [comet.com/site/products/opik](https://www.comet.com/site/products/opik/) to create a free account.
