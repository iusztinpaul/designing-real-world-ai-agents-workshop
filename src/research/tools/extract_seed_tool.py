"""Seed file extraction tool implementation."""

import logging
from pathlib import Path
from typing import Any

from research.app.seed_handler import extract_seed_content
from research.config.constants import MEMORY_FOLDER, SEED_EXTRACTION_FILE, SEED_FILE
from research.utils.file_utils import ensure_memory_dir, save_json, validate_directory

logger = logging.getLogger(__name__)


async def extract_seed_tool(
    working_dir: str, seed_filename: str = SEED_FILE
) -> dict[str, Any]:
    """Extract topics, questions, and YouTube URLs from a seed file.

    Reads the seed file in the working directory and uses Gemini to extract
    structured research information. Results are saved to .memory/seed_extraction.json.

    Args:
        working_dir: Path to the working directory containing the seed file.
        seed_filename: Name of the seed file (default: seed.md).

    Returns:
        Dict with status, extraction results, and output file path.
    """

    validate_directory(working_dir)
    memory_path = ensure_memory_dir(working_dir)

    seed_path = Path(working_dir) / seed_filename
    if not seed_path.exists():
        msg = f"Seed file not found: {seed_path}"
        raise FileNotFoundError(msg)

    seed_text = seed_path.read_text(encoding="utf-8")
    if not seed_text.strip():
        msg = f"Seed file is empty: {seed_path}"
        raise ValueError(msg)

    extraction = await extract_seed_content(seed_text)

    # Save with the raw seed text included for downstream tools
    extraction_data = extraction.model_dump()
    extraction_data["raw_context"] = seed_text

    output_path = memory_path / SEED_EXTRACTION_FILE
    save_json(output_path, extraction_data)

    return {
        "status": "success",
        "youtube_urls_count": len(extraction.youtube_urls),
        "topics_count": len(extraction.topics),
        "research_questions_count": len(extraction.research_questions),
        "output_path": str(output_path.resolve()),
        "message": (
            f"Extracted from seed file '{seed_filename}': "
            f"{len(extraction.youtube_urls)} YouTube URLs, "
            f"{len(extraction.topics)} topics, "
            f"{len(extraction.research_questions)} research questions. "
            f"Results saved to {MEMORY_FOLDER}/{SEED_EXTRACTION_FILE}"
        ),
    }
