"""Gemini grounded research tool implementation."""

import asyncio
import logging
from typing import Any

from research.app.research_handler import run_grounded_search
from research.config.constants import NOVA_FOLDER, RESEARCH_RESULTS_FILE
from research.utils.file_utils import (
    ensure_nova_dir,
    load_json,
    save_json,
    validate_directory,
)

logger = logging.getLogger(__name__)


async def run_research_tool(working_dir: str, queries: list[str]) -> dict[str, Any]:
    """Run Gemini grounded search for a list of research queries.

    Executes each query using Gemini with Google Search grounding and appends
    results to .nova/research_results.json.

    Args:
        working_dir: Path to the working directory.
        queries: List of research queries to execute.

    Returns:
        Dict with status, processing results, and output file path.
    """

    validate_directory(working_dir)
    nova_path = ensure_nova_dir(working_dir)

    if not queries:
        return {
            "status": "success",
            "message": "No queries provided — nothing to research.",
            "queries_processed": 0,
        }

    results_path = nova_path / RESEARCH_RESULTS_FILE

    # Load existing results
    existing_results = load_json(results_path, default=[])

    # Execute all queries concurrently
    logger.info(f"Executing {len(queries)} research queries...")
    tasks = [run_grounded_search(query) for query in queries]
    search_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    successful = 0
    total_sources = 0
    for result in search_results:
        if isinstance(result, Exception):
            logger.error(f"Research query failed: {result}", exc_info=True)
            continue
        existing_results.append(result.model_dump())
        successful += 1
        total_sources += len(result.sources)

    # Save updated results
    save_json(results_path, existing_results)

    return {
        "status": "success",
        "queries_processed": successful,
        "queries_failed": len(queries) - successful,
        "total_sources": total_sources,
        "output_path": str(results_path.resolve()),
        "message": (
            f"Completed {successful}/{len(queries)} research queries. "
            f"Found {total_sources} sources. "
            f"Results saved to {NOVA_FOLDER}/{RESEARCH_RESULTS_FILE}"
        ),
    }
