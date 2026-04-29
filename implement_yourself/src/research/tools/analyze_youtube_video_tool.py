"""Analyze YouTube video tool implementation for the Deep Research MCP server."""

import logging
from typing import Any

from research.app.youtube_handler import analyze_youtube_video, get_video_id
from research.config.constants import MEMORY_FOLDER, TRANSCRIPTS_FOLDER
from research.utils.file_utils import ensure_memory_dir, validate_directory

logger = logging.getLogger(__name__)


async def analyze_youtube_video_tool(
    working_dir: str, youtube_url: str
) -> dict[str, Any]:
    """Analyze a YouTube video using Gemini's native video understanding.

    Args:
        working_dir: Directory where research outputs are stored.
        youtube_url: The URL of the YouTube video to analyze.

    Returns:
        A dict with status, transcript, and output_path on success.
    """
    # Step 1: Validate the working directory
    validate_directory(working_dir)

    # Step 2: Ensure the .memory directory exists
    memory_path = ensure_memory_dir(working_dir)

    # Step 3: Create the transcripts/ subfolder
    dest_folder = memory_path / TRANSCRIPTS_FOLDER
    dest_folder.mkdir(parents=True, exist_ok=True)

    # Step 4: Extract the video ID, fall back to sanitized URL if not found
    video_id = get_video_id(youtube_url)
    if video_id is None:
        logger.warning("Could not extract video ID from URL: %s", youtube_url)
        # Strip scheme and replace slashes to make a safe filename
        sanitized = youtube_url.replace("https://", "").replace("http://", "")
        video_id = sanitized.replace("/", "_")

    # Step 5: Build the output path
    output_path = dest_folder / f"{video_id}.md"

    # Step 6: Analyze the video
    transcript = await analyze_youtube_video(url=youtube_url, output_path=output_path)

    # Step 7: Return the result dict
    return {
        "status": "success",
        "youtube_url": youtube_url,
        "video_id": video_id,
        "transcript": transcript,
        "output_path": str(output_path.resolve()),
        "message": (
            f"Analyzed video: {youtube_url}. "
            f"Transcript saved to {MEMORY_FOLDER}/{TRANSCRIPTS_FOLDER}/{video_id}.md."
        ),
    }
