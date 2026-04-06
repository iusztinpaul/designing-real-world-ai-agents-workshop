# Designing Real-World AI Agents Workshop

A hands-on workshop building a multi-agent AI system with two MCP servers: a **Deep Research Agent** and a **LinkedIn Writing Workflow**. Both connected to a harness like Claude Code or Cursor.

Built as a lightweight companion to the [Agentic AI Engineering Course](https://academy.towardsai.net/courses/agent-engineering), which covers 34 lessons and three end-to-end portfolio projects. This workshop distills the core agentic patterns into ~2 hours of building.

## What You'll Build

<img src="media/architecture.png" alt="End-to-end workflow architecture" width="800"/>

**Deep Research Agent** — An MCP server that runs deep research using Gemini with Google Search grounding and native YouTube video analysis:

```
user topic → [deep_research queries] × N → analyze_youtube_video → compile_research → research.md
```

**LinkedIn Writing Workflow** — An MCP server that generates LinkedIn posts with an evaluator-optimizer loop:

```
research.md + guideline → generate post → [review → edit] × N → post.md → generate image
```

Both servers expose tools, resources, and prompts via the [Model Context Protocol](https://modelcontextprotocol.io/), letting any MCP-compatible harness orchestrate the workflow.

## Example: End-to-End Workflow

Here's a real run through the full pipeline — from a topic seed to a published-ready LinkedIn post with an AI-generated image.

### Final output

<!-- LinkedIn-style post card -->
<div align="center">
<table>
<tr>
<td>

<div>
<strong>Paul Iusztin</strong><br/>
<sub>AI Engineer | I ship AI products and teach you about the process.</sub>
</div>

---

We planned 12 AI agents and shipped 1. It worked better.
Sounds crazy, right? But it's a common story.

A client built an AI marketing chatbot. Their initial design had dozens of agents: orchestrator, validators, spam prevention. It failed.

A single agent with tools won. Tasks were tightly coupled. One brain maintained context. Tools were still specialized.

This is the core mistake. People jump to complex multi-agent setups too fast.

Think AI system design as a spectrum:
*   Workflows: You control steps.
*   Single Agent + Tools: Model decides flow.
*   Multi-Agent: Multiple decision-makers.

...

A single agent works for most cases. But it has limits.
Too many tools? You hit "context rot."
Past ~10-20 tools, LLMs degrade at tool selection. They get overwhelmed. Information gets lost in the middle.

So, when do you actually need multi-agent?

...

**The simplest system that reliably solves the problem is always the best system.**
Don't overengineer your AI agents. Build simple first.

What's the most complex agent architecture you've simplified? Tell me below.

<sub><a href="media/post_3.md">Read the full post</a></sub>

<img src="media/post_image.png" width="500"/>

</td>
</tr>
</table>
</div>

<details>
<summary><strong>Step-by-step breakdown</strong> (seed → research → guideline → drafts)</summary>

<br/>

#### 1. Start with a seed

A short research brief with 2-3 questions and reference links:

```markdown
# Research Topic: AI Agent Architecture — When Less Is More

## Key Questions
1. Why do single-agent architectures with smart tools outperform multi-agent systems?
2. What are the only legitimate reasons to adopt a multi-agent architecture?

## References
- Stop Overengineering: Workflows vs AI Agents Explained (YouTube)
- From 12 Agents to 1 (DecodingAI article)
```

#### 2. Deep Research Agent produces `research.md`

The agent runs multiple Gemini-grounded search queries and analyzes YouTube videos, then compiles everything into a structured research brief with sources.

> The full research.md for this example is ~20k tokens across 2 queries and 1 video transcript.

#### 3. Write a guideline

A short brief describing the post angle, audience, and key points:

```markdown
# LinkedIn Post Guideline

## Topic
Why most AI teams should use 1 agent instead of 12.

## Angle
Open with the counterintuitive "12 agents → 1" hook. Introduce the complexity
spectrum. End with a clear mental model.

## Target Audience
AI engineers and technical leads building LLM-powered applications.

## Key Points
- A team planned 12 agents but shipped 1 — it worked better.
- The spectrum: workflows → single agent + tools → multi-agent. Stay left.
- "Context rot": past ~10-20 tools, LLMs degrade at tool selection.
- Only 4 valid reasons for multi-agent.

## Tone
Direct, opinionated, engineer-to-engineer. No fluff.
```

#### 4. Writing Workflow refines the post

The evaluator-optimizer loop generates a draft, then runs 3 rounds of review + edit:

<table>
<tr>
<td width="50%">

**v0 — Initial draft**

> We planned 12 AI agents. We shipped 1.
>
> Sounds crazy, right? But it's a common story.
>
> A client wanted an AI chatbot for marketing content: emails, SMS, promos. Their initial design had dozens of specialized agents: orchestrator, analyzers, validators, spam prevention.
>
> In practice? A single agent with tools won. Tasks were tightly coupled, sequential. Splitting it created information silos and handoff errors. [...]
>
> **The simplest system that reliably solves the problem is always the best system.**

</td>
<td width="50%">

**v3 — After 3 review/edit cycles**

> We planned 12 AI agents and shipped 1. It worked better.
>
> A client built an AI marketing chatbot. Their initial design had dozens of agents: orchestrator, validators, spam prevention. It failed.
>
> A single agent with tools won. Tasks were tightly coupled. One brain maintained context. Tools were still specialized.
>
> **Stay as far left as possible.** Move right only when forced. [...]
>
> **The simplest system that reliably solves the problem is always the best system.**

</td>
</tr>
<tr>
<td align="center"><em>Verbose, redundant phrasing, weak hook</em></td>
<td align="center"><em>Tighter, punchier, stronger structure</em></td>
</tr>
</table>

</details>

> Browse more full examples (seed, research, post drafts, reviews, final post + image) in the [`examples/`](examples/) directory.

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

## Quick Start

Already have Python 3.14+, uv, and Make installed? Get running in 60 seconds:

```bash
git clone https://github.com/decodingml/designing-real-world-ai-agents-workshop.git
cd designing-real-world-ai-agents-workshop
cp .env.example .env          # add your GOOGLE_API_KEY
uv sync
make test-end-to-end          # verify everything works
```

## Prerequisites

### 1. Python 3.14+

```bash
python --version   # should print 3.14.x
```

> **Note:** Python 3.14 is required (not 3.13 or earlier). If using pyenv: `pyenv install 3.14.0`. Download from [python.org](https://www.python.org/downloads/) if needed.

### 2. uv package manager

```bash
uv --version   # should print 0.7.x or later
```

Install: `curl -LsSf https://astral.sh/uv/install.sh | sh` — see [uv docs](https://docs.astral.sh/uv/getting-started/installation/) for other methods.

### 3. GNU Make

```bash
make --version   # pre-installed on macOS/Linux
```

Windows users: install via [chocolatey](https://chocolatey.org/) (`choco install make`) or copy the commands from the [Makefile](Makefile) directly.

### 4. Google AI Studio API Key

Get one at [aistudio.google.com/apikey](https://aistudio.google.com/apikey). This is **required** — all LLM calls use Gemini.

### 5. Opik Account (optional)

For observability and evaluation tracking. Create an account at [comet.com/site/products/opik](https://www.comet.com/site/products/opik/) and get your API key from the settings page.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/decodingml/designing-real-world-ai-agents-workshop.git
   cd designing-real-world-ai-agents-workshop
   ```

2. **Configure environment variables:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set at minimum:

   ```bash
   GOOGLE_API_KEY=your-key-here
   ```

   Optional (for observability and evals):

   ```bash
   OPIK_API_KEY=your-key-here
   OPIK_WORKSPACE=your-workspace-name
   ```

3. **Install dependencies:**

   ```bash
   uv sync
   ```

4. **Verify the setup:**

   ```bash
   make test-research-workflow
   ```

   This runs a research query using Gemini. If it completes without errors, you're good to go.

## Running the Code

There are three ways to run the workflows:

| Mode | Best for | Requires |
|------|----------|----------|
| **Scripts** | Verify setup works, quick smoke tests | Terminal only |
| **MCP Servers** | Interactive use with AI harness | Claude Code or Cursor |
| **Skills** | Guided slash-command workflows | Claude Code only |

### Scripts

Run workflows directly from the terminal via `make`. Useful for verifying your setup works and running quick smoke tests. See [`examples/`](examples/) for full end-to-end output samples.

**Test workflows:**

```bash
make test-research-workflow    # Research on a sample topic → test_logic/research.md
make test-writing-workflow     # Generate post from research → test_logic/post.md
make test-end-to-end           # Both steps sequentially
```

> **Note:** `test-writing-workflow` requires `test_logic/research.md` to exist. Run `test-research-workflow` first, or use `test-end-to-end`.

**Full dataset run:**

The [`datasets/`](datasets/) directory contains a pre-built LinkedIn posts dataset with seeds, guidelines, research documents, ground truth posts, and generated outputs — used for both batch runs and evaluation.

```bash
make run-dataset-writing           # Research + write for all dataset posts (with images)
make run-dataset-writing-no-image  # Same, skip image generation (faster)
```

**Evaluation (requires Opik):**

```bash
make upload-eval-dataset    # Upload evaluation splits to Opik
make eval-dev               # LLM judge on dev split
make eval-test              # LLM judge on test split
make eval-online            # Generate + judge posts on the fly
```

### MCP Servers

Connect the servers to an MCP-compatible harness (Claude Code, Cursor) for interactive use.

**Setup:** The `.mcp.json` file is pre-configured. Both servers start automatically when you open the project in Claude Code or Cursor.

| Server | Tools | Prompt |
|--------|-------|--------|
| `deep-research` | `deep_research`, `analyze_youtube_video`, `compile_research` | `research_workflow` |
| `linkedin-writer` | `generate_post`, `edit_post`, `generate_image` | `linkedin_post_workflow` |

**Usage:**

1. Open the project in Claude Code or Cursor
2. Invoke an MCP prompt (e.g., `research_workflow`) to get guided through the full workflow
3. Or call individual tools directly for fine-grained control

**Manual server start (advanced):**

```bash
make run-research-server    # stdio transport
make run-writing-server     # stdio transport
```

### Skills (Claude Code only)

Pre-built slash commands that orchestrate the MCP tools with sensible defaults. All output goes to `outputs/{topic-slug}/`.

| Command | What it does |
|---------|-------------|
| `/research` | Deep research on a topic → `research.md` |
| `/write-post` | Generate LinkedIn post from existing research → `post.md` + `post_image.png` |
| `/research-and-write` | Full pipeline: research a topic, then write a post from it |

Example:

```
/research-and-write
```

The skill will ask you for a topic and guideline, then run the full pipeline end-to-end. Check [`examples/`](examples/) to see what each step produces.

## QA

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
├── examples/                  # Full end-to-end output samples (seed → research → posts → image)
├── inputs/                    # Seed and guideline files
├── scripts/                   # Entrypoints and test scripts
├── .mcp.json                  # MCP server configuration for harnesses
├── Makefile                   # Command center
└── .env.example               # Environment variable template
```

## Next Steps

| Resource | Description |
|----------|-------------|
| [Agentic AI Engineering Course](https://academy.towardsai.net/courses/agent-engineering) | Our full course. 34 lessons. Three end-to-end portfolio projects. A certificate. And a Discord community. |
| [Agentic AI Engineering Guide](https://email-course.towardsai.net/) | Free 6-day email course on the mistakes that silently break AI agents in production. |
| [AI Engineering Cheatsheets](https://github.com/louisfb01/ai-engineering-cheatsheets) | Quick-reference sheets for agents, RAG, fine-tuning, and more. Ready to be plugged into Claude Code as context. |

## License

MIT License. See [LICENSE](LICENSE) for details.

Copyright (c) 2026 Paul Iusztin, Towards AI Inc
