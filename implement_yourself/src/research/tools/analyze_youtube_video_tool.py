"""Analyze YouTube video tool implementation for the Deep Research MCP server."""

import logging
from typing import Any

from research.app.exploration_budget import BudgetExceededError, record_exploration_call
from research.app.youtube_handler import analyze_youtube_video, get_video_id
from research.config.constants import (
    MAX_EXPLORATION_CALLS,
    MEMORY_FOLDER,
    TRANSCRIPTS_FOLDER,
)
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
        On budget exceeded returns status="budget_exceeded" with error details.
    """
    # Step 1: Validate the working directory
    validate_directory(working_dir)

    # Step 2: Ensure the .memory directory exists
    memory_path = ensure_memory_dir(working_dir)

    # Step 3: Record this call against the shared exploration budget
    try:
        call_index, calls_remaining = record_exploration_call(
            memory_path, tool="analyze_youtube_video", query=youtube_url
        )
    except BudgetExceededError as exc:
        logger.warning("Exploration budget exceeded for analyze_youtube_video: %s", exc)
        return {
            "status": "budget_exceeded",
            "youtube_url": youtube_url,
            "used_calls": exc.used_calls,
            "max_calls": exc.max_calls,
            "message": str(exc),
        }

    # Step 4: Create the transcripts/ subfolder
    dest_folder = memory_path / TRANSCRIPTS_FOLDER
    dest_folder.mkdir(parents=True, exist_ok=True)

    # Step 5: Extract the video ID, fall back to sanitized URL if not found
    video_id = get_video_id(youtube_url)
    if video_id is None:
        logger.warning("Could not extract video ID from URL: %s", youtube_url)
        # Strip scheme and replace slashes to make a safe filename
        sanitized = youtube_url.replace("https://", "").replace("http://", "")
        video_id = sanitized.replace("/", "_")

    # Step 6: Build the output path
    output_path = dest_folder / f"{video_id}.md"

    # Step 7: Analyze the video
    transcript = await analyze_youtube_video(url=youtube_url, output_path=output_path)

    # Step 8: Return the result dict with budget metadata
    return {
        "status": "success",
        "youtube_url": youtube_url,
        "video_id": video_id,
        "transcript": transcript,
        "output_path": str(output_path.resolve()),
        "call": call_index,
        "max_calls": MAX_EXPLORATION_CALLS,
        "calls_remaining": calls_remaining,
        "message": (
            f"Analyzed video: {youtube_url}. "
            f"Transcript saved to {MEMORY_FOLDER}/{TRANSCRIPTS_FOLDER}/{video_id}.md. "
            f"Call {call_index}/{MAX_EXPLORATION_CALLS} ({calls_remaining} remaining "
            f"before compile_research is required)."
        ),
    }
