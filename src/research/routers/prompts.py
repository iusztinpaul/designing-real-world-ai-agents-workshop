"""MCP Prompts registration for workflow instructions."""

import opik
from fastmcp import FastMCP

from research.utils.opik_utils import opik_context


WORKFLOW_INSTRUCTIONS = """
You are a deep research agent. Use the available tools to thoroughly research a topic.

**Available Tools:**

1. `deep_research(working_dir, query)` — Searches the web using Gemini with Google Search
   grounding. Returns a detailed answer with cited sources. Call this multiple times with
   different queries to build comprehensive coverage.

2. `analyze_youtube_video(working_dir, youtube_url)` — Analyzes a YouTube video using
   Gemini's native video understanding (FileData). Returns a detailed transcript with
   timestamps and key insights. Use when the user provides YouTube URLs.

3. `compile_research(working_dir)` — Aggregates all collected research (search results
   and YouTube transcripts) into a single structured research.md file. Call this once
   at the end.

**Workflow:**

1. Break the user's topic into multiple specific research queries.
2. Call `deep_research` for each query. Review the results and identify gaps.
3. If the user provided YouTube URLs, call `analyze_youtube_video` for each.
4. If needed, run additional `deep_research` calls to fill knowledge gaps.
5. Call `compile_research` to generate the final research.md file.

**Notes:**
- The `working_dir` should be the current working directory.
- All intermediate data is stored in `.memory/` within the working directory.
- You decide what to research and how many queries to run — use your judgment.
""".strip()


def register_mcp_prompts(mcp: FastMCP) -> None:
    """Register all MCP prompts with the server instance."""

    @mcp.prompt()
    @opik.track(type="general")
    async def research_workflow() -> str:
        """Research workflow instructions.

        Returns instructions for conducting deep research using the available
        tools. Guides the agent on how to use deep_research,
        analyze_youtube_video, and compile_research in sequence.
        """

        opik_context.initialize_thread_id()

        return WORKFLOW_INSTRUCTIONS
