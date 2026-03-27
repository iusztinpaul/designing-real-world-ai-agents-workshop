"""MCP Prompts registration for workflow instructions."""

from fastmcp import FastMCP


WORKFLOW_INSTRUCTIONS = """
Your job is to execute the deep research workflow below.

All the tools require a `working_dir` parameter — the path to the research directory.
If the user doesn't provide it, ask for it before executing any tool.

**Workflow:**

1. **Setup:**

    1.1. Explain the numbered steps of the workflow to the user. Be concise.

    1.2. Ask the user for the working directory path, if not provided. Ask if any
    modifications are needed (e.g., running from a specific step, changing the number
    of research iterations).

    1.3. Call the `extract_seed` tool with the working_dir (and optionally a custom
    seed_filename). This reads the seed file and extracts YouTube URLs, topics, and
    research questions. Results are saved to .nova/seed_extraction.json.

2. **Transcribe YouTube videos (if applicable):**

    If Step 1 found YouTube URLs, call the `transcribe_youtube` tool with the
    working_dir and the list of YouTube URLs. Transcriptions are saved to
    .nova/transcripts/.

    Note: Video transcription can be time-consuming. A 30-minute video may take
    approximately 4 minutes.

3. **Research loop (repeat for 3 rounds):**

    For each iteration:

    3.1. Call `generate_next_queries` with the working_dir and optionally n_queries
    (default: 3). This analyzes the seed context, past research, and YouTube
    transcripts to identify knowledge gaps and propose new search queries.

    3.2. Call `run_research` with the working_dir and the list of query strings
    from step 3.1. This executes Gemini grounded search for each query and appends
    results to .nova/research_results.json.

    3.3. Call `select_sources` with the working_dir. This filters the research
    sources for quality, trustworthiness, and relevance. Selected sources are saved
    to .nova/selected_sources.json.

4. **Create the final research file:**

    Call `create_research_file` with the working_dir. This compiles all research
    data (research results, selected sources, YouTube transcripts) into a structured
    research.md file with collapsible sections.

**File Structure After Completion:**

```
working_dir/
├── seed.md                             # Input: Seed document
├── .nova/                              # Working directory for intermediate files
│   ├── seed_extraction.json            # Extracted topics, questions, YouTube URLs
│   ├── transcripts/                    # YouTube video transcripts
│   │   └── [video_id].md
│   ├── queries.json                    # Latest generated research queries
│   ├── research_results.json           # All research results from all rounds
│   └── selected_sources.json           # Quality-filtered sources
└── research.md                         # Final comprehensive research output
```

**Critical Failure Policy:**

If a tool reports a complete failure (0 items processed successfully), halt the
workflow immediately:
1. State the exact tool that failed and quote the output message.
2. Announce that you are stopping the workflow.
3. Ask the user for guidance on how to proceed.

Depending on results, you may skip a tool if not necessary (e.g., skip YouTube
transcription if no YouTube URLs were found).
""".strip()


def register_mcp_prompts(mcp: FastMCP) -> None:
    """Register all MCP prompts with the server instance."""

    @mcp.prompt()
    async def deep_research_workflow() -> str:
        """Complete deep research agent workflow instructions.

        Returns the full workflow instructions for conducting a deep research
        session using the available tools.
        """

        return WORKFLOW_INSTRUCTIONS
