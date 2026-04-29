"""Compile research tool implementation for the Deep Research MCP server."""

import logging
from pathlib import Path
from typing import Any

from research.app.exploration_budget import reset_exploration_budget
from research.app.research_file_handler import compile_research_file
from research.config.constants import MEMORY_FOLDER, RESEARCH_MD_FILE
from research.utils.file_utils import validate_directory, write_file

logger = logging.getLogger(__name__)


async def compile_research_tool(working_dir: str) -> dict[str, Any]:
    """Aggregate all collected research into a single markdown research brief.

    Reads ``.memory/research_results.json`` and every ``*.md`` file under
    ``.memory/transcripts/``, merges them into a single Markdown document,
    writes it to ``<working_dir>/research.md``, and resets the exploration
    budget so any follow-up session starts fresh.

    Args:
        working_dir: Directory where research outputs are stored.

    Returns:
        A dict with ``status``, ``output_path``, and ``message`` on success.

    Raises:
        ValueError: If ``working_dir`` does not exist or is not a directory.
    """
    # Step 1: Validate the working directory.
    validate_directory(working_dir)

    # Step 2: Compile the research file from accumulated data.
    final_md = compile_research_file(working_dir)

    # Step 3: Write research.md into the working directory.
    output_path = Path(working_dir) / RESEARCH_MD_FILE
    write_file(output_path, final_md)
    logger.info("research.md written to %s (%d bytes)", output_path, len(final_md))

    # Step 4: Reset the exploration budget for the next session.
    reset_exploration_budget(Path(working_dir) / MEMORY_FOLDER)

    # Step 5: Return the success payload.
    return {
        "status": "success",
        "output_path": str(output_path.resolve()),
        "message": f"Generated {RESEARCH_MD_FILE} at {output_path.resolve()}",
    }
