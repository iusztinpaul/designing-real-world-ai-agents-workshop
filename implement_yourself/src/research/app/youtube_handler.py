"""YouTube video analysis handler for the Deep Research MCP server."""

import logging
import time
import urllib.parse
from pathlib import Path

import google.genai.types as types

from research.config.prompts import PROMPT_YOUTUBE_TRANSCRIPTION
from research.config.settings import get_settings
from research.utils.file_utils import write_file
from research.utils.llm import get_client

logger = logging.getLogger(__name__)


def get_video_id(url: str) -> str | None:
    """Extract the YouTube video ID from a URL.

    Handles both long-form (youtube.com/watch?v=...) and short (youtu.be/...) URLs.

    Args:
        url: The YouTube URL to parse.

    Returns:
        The video ID string, or None if extraction fails.
    """
    parsed = urllib.parse.urlparse(url)

    # Long-form: https://www.youtube.com/watch?v=VIDEO_ID
    if parsed.netloc in ("www.youtube.com", "youtube.com") and parsed.path == "/watch":
        params = urllib.parse.parse_qs(parsed.query)
        video_ids = params.get("v")
        if video_ids:
            return video_ids[0]

    # Short-form: https://youtu.be/VIDEO_ID
    if parsed.netloc in ("youtu.be",):
        # Path is "/VIDEO_ID" — strip leading slash
        video_id = parsed.path.lstrip("/")
        if video_id:
            return video_id

    return None


async def analyze_youtube_video(
    url: str,
    output_path: Path,
    timestamp: int = 30,
) -> str:
    """Analyze a YouTube video using Gemini's native video understanding.

    Sends the video URL directly to Gemini via FileData and saves the resulting
    timestamped transcript Markdown to output_path.

    Args:
        url: The public YouTube URL to analyze.
        output_path: Where to save the generated transcript Markdown file.
        timestamp: Interval in seconds between transcript timestamp markers.

    Returns:
        The transcript text returned by Gemini. If Gemini returns empty/None,
        an error message string is returned (and also written to output_path).
    """
    settings = get_settings()
    client = get_client()

    prompt = PROMPT_YOUTUBE_TRANSCRIPTION.format(timestamp=timestamp)

    contents = types.Content(
        parts=[
            types.Part(file_data=types.FileData(file_uri=url)),
            types.Part(text=prompt),
        ]
    )

    logger.info("Analyzing YouTube video: %s", url)
    start = time.monotonic()

    try:
        response = await client.aio.models.generate_content(
            model=settings.youtube_transcription_model,
            contents=contents,
        )
    except Exception as exc:
        logger.warning("Gemini YouTube analysis failed for %s: %s", url, exc)
        fallback = f"Could not generate transcript for {url}. Error: {exc}"
        write_file(output_path, fallback)
        return fallback

    elapsed = time.monotonic() - start
    logger.info("Gemini YouTube analysis completed in %.2fs", elapsed)

    transcript = response.text
    if not transcript:
        error_message = (
            f"Could not generate transcript for video: {url}. "
            "Gemini returned an empty response."
        )
        logger.warning(error_message)
        write_file(output_path, error_message)
        return error_message

    write_file(output_path, transcript)
    logger.info("Transcript saved to %s (%d bytes)", output_path, len(transcript))

    return transcript
