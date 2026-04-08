"""Gemini grounded research tool implementation."""

import logging
from typing import Any

from research.app.research_handler import run_grounded_search
from research.config.constants import MEMORY_FOLDER, RESEARCH_RESULTS_FILE
from research.utils.file_utils import (
    ensure_memory_dir,
    load_json,
    save_json,
    validate_directory,
)

logger = logging.getLogger(__name__)


async def deep_research_tool(working_dir: str, query: str) -> dict[str, Any]:
    """Run Gemini grounded search for a single research query.

    Executes the query using Gemini with Google Search grounding and appends
    the result to .memory/research_results.json.

    Args:
        working_dir: Path to the working directory.
        query: The research query to execute.

    Returns:
        Dict with status, research result, and output file path.
    """

    # Step 1: Ensure the working directory is valid and .memory/ exists
    validate_directory(working_dir)
    memory_path = ensure_memory_dir(working_dir)

    # Step 2: Build the path to the cumulative results JSON file
    results_path = memory_path / RESEARCH_RESULTS_FILE

    # Step 3: Load any previously saved results so we can append to them.
    # If this is the first query, starts with an empty list.
    existing_results = load_json(results_path, default=[])

    # Step 4: Send the query to Gemini with Google Search grounding.
    # This performs a live web search and returns a structured ResearchResult
    # containing the answer text and cited sources.
    logger.info(f"Executing research query: {query}")
    result = await run_grounded_search(query)

    # Step 5: Append the new result (as a dict) and persist back to disk.
    # This accumulates results across multiple tool invocations so that
    # compile_research_tool can later merge them all into research.md.
    existing_results.append(result.model_dump())
    save_json(results_path, existing_results)

    # Step 6: Return a response dict to the MCP caller with the answer,
    # sources, and metadata about where results were saved.
    return {
        "status": "success",
        "query": query,
        "answer": result.answer,
        "sources": [src.model_dump() for src in result.sources],
        "total_sources": len(result.sources),
        "output_path": str(results_path.resolve()),
        "message": (
            f"Researched: '{query}'. "
            f"Found {len(result.sources)} sources. "
            f"Results saved to {MEMORY_FOLDER}/{RESEARCH_RESULTS_FILE}"
        ),
    }
