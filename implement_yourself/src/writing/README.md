# LinkedIn Writer MCP Server

A FastMCP server that generates LinkedIn posts via an evaluator-optimizer loop powered by Google Gemini. Given a `guideline.md` (topic and angle) and a `research.md` (factual material), it drafts an initial post, runs multiple reviewer-writer cycles to refine it, and optionally generates a professional image with Gemini Flash Image. Human-in-the-loop editing is supported via a dedicated `edit_post` tool. The server is transport-agnostic and speaks the MCP stdio protocol.

## Prerequisites

- Python 3.12 or later (see [`.python-version`](../../.python-version))
- `uv` for virtual environment and dependency management ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- GNU Make (pre-installed on macOS/Linux; `choco install make` on Windows)
- Google AI Studio API key ([aistudio.google.com/apikey](https://aistudio.google.com/apikey))
- (Optional) Opik account and workspace for observability ([comet.com/site/products/opik](https://www.comet.com/site/products/opik/))
- An MCP-compatible harness: Claude Code, Cursor, or similar
- A `research.md` file in the working directory — produced by `make test-research-workflow` (see [`../research/README.md`](../research/README.md)) or supplied from any other source

## Installation

From the `implement_yourself/` project root, run:

```bash
uv sync
```

This resolves all dependencies declared in `pyproject.toml` and creates an isolated `.venv/` virtual environment under the project root. All subsequent `make` and `uv run` commands automatically use that environment. Install steps are identical to those described in [`../research/README.md`](../research/README.md).

## Configuration

Copy the template and fill in your keys:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | Yes | — | Google AI Studio API key. Used for all Gemini calls (writing, reviewing, and image generation). |
| `OPIK_API_KEY` | No | — | Enables Opik observability tracing. Wired in task #020; leave blank until then. |
| `OPIK_WORKSPACE` | No | — | Opik workspace name (only used when `OPIK_API_KEY` is set). |
| `OPIK_PROJECT_NAME` | No | `writing-workflow` | Opik project label for grouping traces. |
| `LOG_LEVEL` | No | `20` (INFO) | Python integer logging level: `10`=DEBUG, `20`=INFO, `30`=WARNING. |

Settings are loaded by `src/writing/config/settings.py` via Pydantic Settings. Unknown keys in `.env` are silently ignored.

## Architecture Overview

The MCP harness (Claude Code, Cursor, etc.) drives the workflow. The LinkedIn Writer server exposes three tools and a prompt that guide the harness through draft → review loop → image generation → optional human edits.

**Call chain:** `routers/ → tools/ → app/ → utils/`

- **`routers/`** — Registers tools, prompts, and resources with FastMCP.
- **`tools/`** — Validate inputs, invoke business logic, read/write working-dir files.
- **`app/`** — Business logic: Gemini API calls for writing, reviewing, and image generation.
- **`utils/`** — Shared helpers (Gemini client, logging).
- **`profiles/`** — Four shipped markdown profiles (structure, terminology, character, branding) that anchor the writer's voice and style.

```
src/writing/
├── server.py                          # FastMCP entry point
├── routers/                           # MCP registration layer
│   ├── tools.py                       #   registers 3 tools
│   ├── prompts.py                     #   registers 1 prompt
│   └── resources.py                   #   registers 2 resources
├── tools/                             # Tool implementations
│   ├── generate_post_tool.py
│   ├── edit_post_tool.py
│   └── generate_image_tool.py
├── app/                               # Business logic
│   ├── generate_post.py
│   ├── post_writer_handler.py
│   ├── post_reviewer_handler.py
│   ├── image_handler.py
│   ├── profile_loader.py
│   └── dataset_loader.py
├── config/
│   ├── settings.py                    # Pydantic Settings (env vars, model names)
│   ├── constants.py                   # File/folder name constants
│   └── prompts.py                     # LLM prompt templates
├── models/                            # Pydantic schemas (Post, Review, Profiles)
├── profiles/                          # Shipped markdown writing profiles
│   ├── structure_profile.md
│   ├── terminology_profile.md
│   ├── character_profile.md
│   └── branding_profile.md
└── utils/
    ├── llm.py                         # Gemini client helpers (text + Imagen)
    └── logging.py
```

## MCP Primitives

| Type | Name | Purpose |
|---|---|---|
| **Tool** | `generate_post` | Generates an initial post then runs the evaluator-optimizer loop (`num_reviews` rounds). Saves intermediate versions to `.memory/` and `post_N.md`; writes final post to `post.md`. |
| **Tool** | `edit_post` | Runs one reviewer-writer pass guided by explicit human feedback. Human feedback takes highest priority over all other constraints. Overwrites `post.md`. |
| **Tool** | `generate_image` | Generates a professional LinkedIn-appropriate image with Gemini Flash Image based on the current `post.md`. Saves result as `post_image.png`. |
| **Prompt** | `linkedin_post_workflow` | Guides the harness through the four-step workflow: setup → generate post → generate image → edit (optional). |
| **Resource** | `config://settings` | Exposes server config: model names, version, feature flags. |
| **Resource** | `profiles://all` | Returns the full markdown content of all four shipped writing profiles. |

All tools accept a `working_dir` parameter that scopes all file I/O to the writing session directory.

## Running the Server

**Start via Make (stdio transport, for harness integration):**

```bash
make run-writing-server
```

The server speaks the MCP stdio protocol. A connected harness (Claude Code, Cursor) communicates through stdin/stdout.

**Run the e2e smoke test directly (bypasses MCP transport):**

```bash
make test-writing-workflow
```

This copies the dataset's `_guideline.md` to `test_logic/guideline.md` and (if not already present) `_research.md` to `test_logic/research.md`, then calls the same handlers the MCP tools call. Output lands in `test_logic/`.

**Run research + writing end-to-end:**

```bash
make test-end-to-end
```

Chains `test-research-workflow` then `test-writing-workflow` on the same `test_logic/` directory.

**Auto-launch from harness via `.mcp.json`:**

The `implement_yourself/.mcp.json` file registers the server under the name `linkedin-writer`:

```json
{
  "mcpServers": {
    "linkedin-writer": {
      "command": "uv",
      "args": ["run", "fastmcp", "run", "src/writing/server.py"],
      "env": { "ENV_FILE_PATH": ".env" }
    }
  }
}
```

Open the harness with `implement_yourself/` as the working directory and it picks up this file automatically.

## Using the `/write-post` Skill

The `/write-post` skill is a high-level slash command available inside the harness. It orchestrates `generate_post`, `generate_image`, and optionally `edit_post` end-to-end without requiring you to call each tool manually.

Invoke it with a guideline or let the harness detect a writing intent:

```
/write-post
```

The skill asks for the working directory, verifies that `guideline.md` and `research.md` are present, then runs the full workflow. Output lands in the working directory under the name `post.md` (plus `post_image.png` for the image).

For a full pipeline starting from research, use `/research-and-write`. See [`../../README.md`](../../README.md) for the complete skill catalogue.

## Make Targets

| Target | Description |
|---|---|
| `run-writing-server` | Boot the LinkedIn Writer MCP server (stdio transport). Use for harness integration. |
| `test-writing-workflow` | Run the writing pipeline on the dataset guideline + research. Output: `test_logic/post.md`. |
| `test-end-to-end` | Chain `test-research-workflow` then `test-writing-workflow` on the same `test_logic/` directory. |
| `run-dataset-writing` | Run the full research + writing workflow on all dataset posts (output to `test_all/`). |
| `run-dataset-writing-no-image` | Same as `run-dataset-writing` but skips image generation. |
| `format-fix` | Auto-format Python source with ruff formatter. |
| `lint-fix` | Auto-fix linting issues with ruff linter. |
| `format-check` | Check formatting without modifying files. Exits non-zero on any violation. |
| `lint-check` | Check for linting issues without fixing. Exits non-zero on any violation. |

## Output Layout

After a writing session the working directory contains:

```
working_dir/
├── guideline.md
├── research.md
├── .memory/
│   ├── reviews_1.json
│   └── reviews_2.json
├── post_0.md
├── post_1.md
├── post.md
└── post_image.png
```

The `.memory/` directory holds one `reviews_N.json` file per evaluator-optimizer round. The `post_N.md` files are intermediate drafts; `post.md` is the final output.

## Profiles

The writer's voice and style are anchored by four markdown profiles shipped in `src/writing/profiles/`:

- `structure_profile.md` — how a post is structured (hook, body, CTA).
- `terminology_profile.md` — preferred vocabulary and phrasing conventions.
- `character_profile.md` — persona, tone, and authorial voice.
- `branding_profile.md` — brand guidelines and positioning.

They are loaded at runtime by `app/profile_loader.py` and injected into every generation and review prompt. To customize the writer's voice, edit these files directly — they are intentionally exposed as part of the package. Rerun `make test-writing-workflow` after editing to verify the change takes effect.

## Observability (Optional)

Setting `OPIK_API_KEY` enables Opik tracing of every Gemini call made by the server. Traces are grouped by project under `OPIK_PROJECT_NAME` (default: `writing-workflow`) and show full LLM input/output, latency, and token usage. This integration is wired in task #020; without that task complete the variable is read but no tracing occurs. See [comet.com/site/products/opik](https://www.comet.com/site/products/opik/) to create a free account.
