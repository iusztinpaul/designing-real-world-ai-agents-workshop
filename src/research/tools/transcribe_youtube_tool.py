"""YouTube video transcription tool implementation."""

import asyncio
import logging
from typing import Any

from research.app.youtube_handler import process_youtube_url
from research.config.constants import (
    MEMORY_FOLDER,
    TRANSCRIPTS_FOLDER,
    YOUTUBE_TRANSCRIPTION_MAX_CONCURRENT_REQUESTS,
)
from research.utils.file_utils import ensure_memory_dir, validate_directory

logger = logging.getLogger(__name__)


async def transcribe_youtube_tool(
    working_dir: str, youtube_urls: list[str]
) -> dict[str, Any]:
    """Transcribe YouTube videos using Gemini.

    Processes each YouTube URL and saves the transcription as a markdown file
    in .memory/transcripts/.

    Args:
        working_dir: Path to the working directory.
        youtube_urls: List of YouTube video URLs to transcribe.

    Returns:
        Dict with status, processing results, and output directory.
    """

    validate_directory(working_dir)
    memory_path = ensure_memory_dir(working_dir)

    if not youtube_urls:
        return {
            "status": "success",
            "videos_processed": 0,
            "message": "No YouTube URLs provided — nothing to transcribe.",
        }

    dest_folder = memory_path / TRANSCRIPTS_FOLDER
    dest_folder.mkdir(parents=True, exist_ok=True)

    logger.info(f"Processing {len(youtube_urls)} YouTube URL(s)...")

    semaphore = asyncio.Semaphore(YOUTUBE_TRANSCRIPTION_MAX_CONCURRENT_REQUESTS)
    tasks = [process_youtube_url(url, dest_folder, semaphore) for url in youtube_urls]
    await asyncio.gather(*tasks)

    return {
        "status": "success",
        "videos_processed": len(youtube_urls),
        "output_directory": str(dest_folder.resolve()),
        "message": (
            f"Processed {len(youtube_urls)} YouTube URL(s). "
            f"Transcriptions saved to {MEMORY_FOLDER}/{TRANSCRIPTS_FOLDER}/"
        ),
    }
