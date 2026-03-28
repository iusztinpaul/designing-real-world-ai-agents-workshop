# Designing Real-World AI Agents Workshop

A hands-on workshop building a hybrid AI system with two MCP servers: a **Deep Research Agent** and a **LinkedIn Writing Workflow** — both connected to a harness like Claude Code or Cursor.

Built as a lightweight companion to the [Agentic AI Engineering Course](https://github.com/decodingml/agentic-ai-engineering-course). The course covers ~40 hours of material; this workshop distills the core patterns into ~2 hours of building.

## What You'll Build

**Deep Research Agent** — An MCP server that runs deep research using Gemini with Google Search grounding and native YouTube video analysis:

```
user topic → [deep_research queries] × N → analyze_youtube_video → compile_research → research.md
```

**LinkedIn Writing Workflow** — An MCP server that generates LinkedIn posts with an evaluator-optimizer loop:

```
research.md + guideline → generate post → [review → edit] × N → post.md → generate image
```

Both servers expose tools, resources, and prompts via the [Model Context Protocol](https://modelcontextprotocol.io/), letting any MCP-compatible harness orchestrate the workflow.

## Tech Stack

| Component | Tool |
|-----------|------|
| LLM API | Google Gemini (via `google-genai` SDK) |
| MCP Framework | FastMCP |
| Data Validation | Pydantic |
| Settings | Pydantic Settings |
| Observability | Opik |
| Image Generation | Gemini Flash Image |
| QA | Ruff |
| Package Manager | uv |

## Setup

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager
- [GNU Make](https://www.gnu.org/software/make/) (pre-installed on macOS/Linux; if unavailable, just copy the commands from the [Makefile](Makefile) directly)
- A [Google AI Studio](https://aistudio.google.com/) API key

### Install

```bash
git clone https://github.com/decodingml/designing-real-world-ai-agents-workshop.git
cd designing-real-world-ai-agents-workshop
cp .env.example .env   # Fill in your API keys
uv sync
```

### Environment Variables

Edit `.env` with your keys:

```bash
# Mandatory
GOOGLE_API_KEY=...          # Google AI Studio API key (Gemini)

# Optional
OPIK_API_KEY=...            # Opik API key for observability
```

## Running

All commands go through `make`. Run `make` to see available targets.

### Connect to a Harness (Claude Code / Cursor)

The `.mcp.json` file is pre-configured with both servers. In Cursor or Claude Code, the servers will be available automatically:

- **deep-research** — 3 tools, 1 resource, 1 prompt
- **linkedin-writer** — 3 tools, 2 resources, 1 prompt

To use: invoke the MCP prompt (`research_workflow` or `linkedin_post_workflow`) and let the harness orchestrate the tools.

### Run Servers Standalone

```bash
make run-research-server    # Deep Research Agent (stdio)
make run-writing-server     # LinkedIn Writer (stdio)
```

### Test Workflows

```bash
# Run research workflow (uses inputs/seed.md)
make test-research-workflow

# Run writing workflow (uses inputs/guideline.md + research.md from above)
make test-writing-workflow

# Run both end-to-end
make test-end-to-end
```

### Dataset

```bash
# Run research + writing workflow on all dataset posts
make run-dataset-writing

# Same as above but skip image generation
make run-dataset-writing-no-image
```

### Evaluation

```bash
# Upload all evaluation splits (dev, test, online) to Opik
make upload-eval-dataset

# Run LLM judge on dev split (alignment check, reports F1)
make eval-dev

# Run LLM judge on test split (final evaluation, reports F1)
make eval-test

# Run online evaluation: generate posts on the fly + judge them (no F1)
make eval-online
```

### QA

```bash
make format-fix             # Auto-format with ruff
make lint-fix               # Auto-fix lint issues
make format-check           # Check formatting
make lint-check             # Check linting
```

## Project Structure

```
├── src/
│   ├── research/              # Deep Research Agent MCP server
│   │   ├── server.py          # FastMCP entry point
│   │   ├── config/            # Settings, constants, prompt templates
│   │   ├── models/            # Pydantic schemas for structured LLM output
│   │   ├── app/               # Business logic handlers
│   │   ├── tools/             # MCP tool implementations
│   │   ├── routers/           # MCP tool, resource, and prompt registration
│   │   └── utils/             # Gemini client, file I/O, Opik, markdown helpers
│   └── writing/               # LinkedIn Writer MCP server
│       ├── server.py          # FastMCP entry point
│       ├── profiles/          # Shipped markdown profiles (structure, terminology, character, branding)
│       ├── config/            # Settings, constants, prompt templates
│       ├── models/            # Pydantic schemas (Post, Review, Profiles)
│       ├── app/               # Business logic handlers
│       ├── evals/             # LLM judge metric, dataset upload, evaluation harness
│       ├── tools/             # MCP tool implementations
│       ├── routers/           # MCP tool, resource, and prompt registration
│       └── utils/             # Gemini client, Imagen, Opik helpers
├── datasets/                  # LinkedIn posts dataset with labels and splits
├── inputs/                    # Seed and guideline files
├── scripts/                   # Entrypoints and test scripts
├── .mcp.json                  # MCP server configuration for harnesses
├── Makefile                   # Command center
└── .env.example               # Environment variable template
```

## Next Steps

<!-- TODO: Add links -->
- **Full Course** — *Coming soon*
- **Decoding AI Magazine** — *Coming soon*
- **Community** — *Coming soon*

## License

MIT License. See [LICENSE](LICENSE) for details.

Copyright (c) 2026 Paul Iusztin, Towards AI Inc
