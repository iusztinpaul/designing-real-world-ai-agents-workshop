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

    validate_directory(working_dir)
    memory_path = ensure_memory_dir(working_dir)

    results_path = memory_path / RESEARCH_RESULTS_FILE

    # Load existing results
    existing_results = load_json(results_path, default=[])

    logger.info(f"Executing research query: {query}")
    result = await run_grounded_search(query)

    existing_results.append(result.model_dump())
    save_json(results_path, existing_results)

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
