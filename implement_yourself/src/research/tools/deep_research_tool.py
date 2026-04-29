"""Deep research tool implementation for the Deep Research MCP server."""

import logging
from typing import Any

from research.app.exploration_budget import BudgetExceededError, record_exploration_call
from research.app.research_handler import run_grounded_search
from research.config.constants import (
    MAX_EXPLORATION_CALLS,
    MEMORY_FOLDER,
    RESEARCH_RESULTS_FILE,
)
from research.utils.file_utils import (
    ensure_memory_dir,
    load_json,
    save_json,
    validate_directory,
)

logger = logging.getLogger(__name__)


async def deep_research_tool(working_dir: str, query: str) -> dict[str, Any]:
    """Research a topic using Gemini with Google Search grounding.

    Args:
        working_dir: Directory where research outputs are stored.
        query: The research query or topic to investigate.

    Returns:
        A dict with the tool result. On success the dict includes status,
        query, answer, sources, call index, budget metadata, and output_path.
        On budget exceeded the dict includes status="budget_exceeded" and
        error details.
    """
    # Step 1: Validate the working directory and ensure .memory exists.
    validate_directory(working_dir)
    memory_path = ensure_memory_dir(working_dir)

    # Step 2: Record this call against the shared exploration budget.
    try:
        call_index, calls_remaining = record_exploration_call(
            memory_path, tool="deep_research", query=query
        )
    except BudgetExceededError as exc:
        logger.warning("Exploration budget exceeded for deep_research: %s", exc)
        return {
            "status": "budget_exceeded",
            "query": query,
            "used_calls": exc.used_calls,
            "max_calls": exc.max_calls,
            "message": str(exc),
        }

    # Step 3: Determine the results file path.
    results_path = memory_path / RESEARCH_RESULTS_FILE

    # Step 4: Load any existing results.
    existing = load_json(results_path, default=[])

    # Step 5: Run the grounded search.
    result = await run_grounded_search(query)

    # Step 6: Append and persist results.
    existing.append(result.model_dump())
    save_json(results_path, existing)

    # Step 7: Return success payload.
    return {
        "status": "success",
        "query": query,
        "answer": result.answer,
        "sources": [src.model_dump() for src in result.sources],
        "total_sources": len(result.sources),
        "output_path": str(results_path.resolve()),
        "call": call_index,
        "max_calls": MAX_EXPLORATION_CALLS,
        "calls_remaining": calls_remaining,
        "message": (
            f"Researched: '{query}'. Found {len(result.sources)} sources. "
            f"Results saved to {MEMORY_FOLDER}/{RESEARCH_RESULTS_FILE}. "
            f"Call {call_index}/{MAX_EXPLORATION_CALLS} ({calls_remaining} remaining "
            f"before compile_research is required)."
        ),
    }
