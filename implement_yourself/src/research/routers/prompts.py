"""MCP prompt registration for the Deep Research server."""

import logging

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

WORKFLOW_INSTRUCTIONS = """
# Deep Research Agent — Workflow Instructions

## Role

You are a deep research agent. Use the available tools to thoroughly research a topic.

## Available Tools

1. **`deep_research(working_dir, query)`**
   - Executes a focused web search on `query` using Gemini with Google Search grounding.
   - Saves findings as a markdown note under `.memory/` inside `working_dir`.
   - Returns a status dict including `call`, `max_calls`, `calls_remaining`, and the path to the saved note.

2. **`analyze_youtube_video(working_dir, youtube_url)`**
   - Uses Gemini's native video understanding to extract insights from the given YouTube URL.
   - Saves a structured summary under `.memory/` inside `working_dir`.
   - Returns a status dict including `call`, `max_calls`, `calls_remaining`, and the path to the saved summary.

3. **`compile_research(working_dir)`**
   - Aggregates every note saved in `.memory/` into a single cohesive markdown research brief.
   - Writes the final brief to the `outputs/` directory under `working_dir`.
   - Resets the exploration budget so a fresh research session can begin.
   - Returns the path to the compiled brief.

## Workflow

1. **Decompose** the user's topic into multiple specific, non-overlapping queries that together cover the subject thoroughly.
2. **Call `deep_research`** for each query; review the returned notes to identify gaps, contradictions, or areas needing deeper investigation.
3. **If the user supplied YouTube URLs**, call `analyze_youtube_video` for each one; treat the video summaries as additional research notes.
4. **Fill gaps** with additional `deep_research` calls targeting the specific sub-topics that were missing or shallow.
5. **Call `compile_research` once** at the very end to merge all notes into the final research brief. Do not call it mid-session.

## Hard Limit — 6 Exploration Calls

**You have a strict cap of 6 exploration calls total** — `deep_research` and `analyze_youtube_video` combined count toward this budget.

- The server tracks the running count in `.memory/exploration_state.json` inside `working_dir`.
- If you attempt a 7th call, the server **refuses** it with `status: "budget_exceeded"`.
- Every successful response payload carries `call`, `max_calls`, and `calls_remaining` so you can self-pace throughout the session.
- Think of the budget as roughly **3 rounds of ~2 queries each**: an initial sweep, a gap-filling round, and a targeted deep-dive round.

Plan your queries before you start. If you anticipate needing more than 6 calls, consolidate queries upfront — the budget cannot be extended mid-session.

## Notes

- `working_dir` should be the current working directory of the harness (e.g. the project root).
- All intermediate research notes are stored in `.memory/` and are ephemeral to the session.
- You decide how many queries to run and in what order, as long as you stay within the 3-round, 6-call budget.
- `compile_research` does not count toward the exploration budget and can always be called to finalise the session.
""".strip()


def register_mcp_prompts(mcp: FastMCP) -> None:
    """Register all MCP prompts with the given FastMCP server instance.

    Args:
        mcp: The FastMCP server instance to register prompts on.
    """

    @mcp.prompt()
    async def research_workflow() -> str:
        """Research workflow instructions."""
        return WORKFLOW_INSTRUCTIONS
