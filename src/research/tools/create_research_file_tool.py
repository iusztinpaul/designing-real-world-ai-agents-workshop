"""Research file creation tool implementation."""

import logging
from pathlib import Path
from typing import Any

from research.app.research_file_handler import compile_research_file
from research.config.constants import RESEARCH_MD_FILE
from research.utils.file_utils import validate_directory, write_file

logger = logging.getLogger(__name__)


def create_research_file_tool(working_dir: str) -> dict[str, Any]:
    """Generate the final comprehensive research.md file.

    Combines all research data from .memory/ into a structured markdown file
    with collapsible sections for easy navigation.

    Args:
        working_dir: Path to the working directory containing .memory/ data.

    Returns:
        Dict with status, generated file path, and summary.
    """

    validate_directory(working_dir)

    final_md = compile_research_file(working_dir)

    output_path = Path(working_dir) / RESEARCH_MD_FILE
    write_file(output_path, final_md)

    logger.info(f"Generated research file: {output_path.resolve()}")

    return {
        "status": "success",
        "output_path": str(output_path.resolve()),
        "message": f"Generated {RESEARCH_MD_FILE} at {output_path.resolve()}",
    }
