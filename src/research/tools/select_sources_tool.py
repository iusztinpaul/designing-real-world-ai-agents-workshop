"""Source selection tool implementation."""

import logging
from typing import Any

from research.app.source_selection_handler import merge_selected_sources, select_sources
from research.config.constants import (
    MEMORY_FOLDER,
    RESEARCH_RESULTS_FILE,
    SEED_EXTRACTION_FILE,
    SELECTED_SOURCES_FILE,
)
from research.utils.file_utils import (
    ensure_memory_dir,
    load_json,
    save_json,
    validate_directory,
)

logger = logging.getLogger(__name__)


async def select_sources_tool(working_dir: str) -> dict[str, Any]:
    """Filter and select high-quality sources from research results.

    Uses Gemini to evaluate sources for trustworthiness, authority, and
    relevance. Results are saved to .memory/selected_sources.json.

    Args:
        working_dir: Path to the working directory.

    Returns:
        Dict with status, selection results, and output file path.
    """

    validate_directory(working_dir)
    memory_path = ensure_memory_dir(working_dir)

    # Load context
    seed_data = load_json(memory_path / SEED_EXTRACTION_FILE)
    seed_context = seed_data.get("raw_context", "")

    research_results = load_json(memory_path / RESEARCH_RESULTS_FILE, default=[])
    if not research_results:
        return {
            "status": "success",
            "sources_selected": 0,
            "message": "No research results found to select from.",
        }

    selection = await select_sources(seed_context, research_results)

    # Merge with existing selected sources (from previous iterations)
    existing_selected = load_json(memory_path / SELECTED_SOURCES_FILE, default=[])
    merged = merge_selected_sources(existing_selected, selection)

    output_path = memory_path / SELECTED_SOURCES_FILE
    save_json(output_path, merged)

    return {
        "status": "success",
        "sources_selected": len(selection.selected_sources),
        "total_selected": len(merged),
        "reasoning": selection.reasoning,
        "output_path": str(output_path.resolve()),
        "message": (
            f"Selected {len(selection.selected_sources)} new source(s) "
            f"({len(merged)} total). "
            f"Saved to {MEMORY_FOLDER}/{SELECTED_SOURCES_FILE}\n"
            f"Reasoning: {selection.reasoning}"
        ),
    }
