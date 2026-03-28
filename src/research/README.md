# Deep Research MCP Server

A FastMCP server that gives any MCP-compatible agent (Claude Code, Cursor, etc.) the ability to conduct deep web research and analyze YouTube videos using Google Gemini.

## How It Works

```
User: "Research how AI agents work in production"
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              Agent (Claude Code)                     │
│                                                      │
│  The agent decides WHAT to research and WHEN.        │
│  It has the ReAct loop — the MCP server just         │
│  provides capabilities.                              │
│                                                      │
│  1. Breaks topic into queries                        │
│  2. Calls tools, reads results                       │
│  3. Identifies gaps, researches more                 │
│  4. Compiles final output                            │
└──────────┬──────────────┬──────────────┬─────────────┘
           │              │              │
           ▼              ▼              ▼
   ┌──────────────┐ ┌───────────┐ ┌────────────────┐
   │deep_research │ │analyze_   │ │compile_        │
   │              │ │youtube_   │ │research        │
   │ Gemini +     │ │video      │ │                │
   │ Google Search│ │           │ │ Aggregates all │
   │ grounding    │ │ Gemini +  │ │ results into   │
   │              │ │ FileData  │ │ research.md    │
   │ Returns:     │ │ (native   │ │                │
   │ answer +     │ │ video     │ │                │
   │ sources      │ │ analysis) │ │                │
   └──────────────┘ └───────────┘ └────────────────┘
```

## MCP Primitives

| Type | Name | Purpose |
|------|------|---------|
| **Tool** | `deep_research` | Calls Gemini with Google Search grounding. Returns answer + sources |
| **Tool** | `analyze_youtube_video` | Passes YouTube URL to Gemini via `FileData(file_uri=url)` for native video understanding |
| **Tool** | `compile_research` | Aggregates all results from `.memory/` into `research.md` |
| **Prompt** | `research_workflow` | Guides the agent on how to use the 3 tools in sequence |
| **Resource** | `resource://config/research` | Exposes server config: model names, version, feature flags |

All tools also take a `working_dir` parameter (the research session directory).

## Architecture

**Call chain:** `routers/ → tools/ → app/ → utils/`

- **`routers/`** — Registers tools/prompts/resources with FastMCP (the MCP interface layer)
- **`tools/`** — Tool implementations: validate inputs, call business logic, save/load files
- **`app/`** — Business logic: the actual Gemini API calls
- **`utils/`** — Shared helpers used by `app/` and `tools/` (Gemini client, file I/O, markdown, logging, Opik)

```
src/research/
├── server.py                      # FastMCP entry point
│
├── routers/                       # MCP registration layer
│   ├── tools.py                   #   registers 3 tools
│   ├── prompts.py                 #   registers 1 prompt
│   └── resources.py               #   registers 1 resource
│
├── tools/                         # Tool implementations (thin wrappers)
│   ├── deep_research_tool.py      #   orchestrates grounded search
│   ├── analyze_youtube_video_tool.py  #   orchestrates video analysis
│   └── compile_research_tool.py   #   orchestrates markdown compilation
│
├── app/                           # Business logic
│   ├── research_handler.py        #   Gemini grounded search call
│   ├── youtube_handler.py         #   Gemini video understanding call
│   └── research_file_handler.py   #   markdown assembly
│
├── config/                        # Configuration
│   ├── settings.py                #   Pydantic Settings (env vars, models)
│   ├── constants.py               #   file/folder name constants
│   └── prompts.py                 #   LLM prompt templates
│
├── models/
│   └── schemas.py                 #   ResearchSource, ResearchResult
│
└── utils/
    ├── llm.py                     #   Gemini client (call_gemini, call_gemini_search)
    ├── file_utils.py              #   file I/O helpers
    ├── markdown_utils.py          #   collapsible sections, markdown assembly
    ├── logging.py                 #   logging setup
    └── opik_utils.py              #   Opik observability integration
```

## Tool Response Pattern

Tools both **return results to the agent** and **write to disk** for accumulation:

```
deep_research("How do AI agents work?")
  │
  ├─→ Returns to agent:  { answer: "...", sources: [...], output_path: "..." }
  │   (agent sees the content immediately and can reason about it)
  │
  └─→ Writes to disk:    .memory/research_results.json  (appends)
      (so compile_research can later read ALL results)
```

- `deep_research` — returns the answer + sources AND appends to `.memory/research_results.json`
- `analyze_youtube_video` — returns the transcript AND saves to `.memory/transcripts/{id}.md`
- `compile_research` — reads everything from `.memory/`, assembles `research.md`

The agent gets results immediately to reason about gaps. The files are for accumulation so `compile_research` can combine everything at the end.

## Data Flow

During a research session, intermediate data is stored in `.memory/` within the working directory:

```
working_dir/
├── .memory/
│   ├── research_results.json      # Accumulated results from deep_research calls
│   └── transcripts/
│       └── {video_id}.md          # One file per analyzed YouTube video
└── research.md                    # Final output (created by compile_research)
```

## Configuration

Set via environment variables (or `.env` file):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes | — | Google AI Studio API key for Gemini |
| `OPIK_API_KEY` | No | — | Enables LLM observability via Opik |
| `OPIK_WORKSPACE` | No | — | Opik workspace name |
| `OPIK_PROJECT_NAME` | No | `research-agent` | Opik project name |

## Observability

When `OPIK_API_KEY` is set, every Gemini call and tool invocation is traced via [Opik](https://www.comet.com/site/products/opik/). You can see:

- Full LLM input/output for each call
- Latency per tool and per Gemini request
- Tool call sequence (thread grouping)
- Token usage
