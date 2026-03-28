"""YouTube video analysis using Gemini's native video understanding."""

import logging
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from google.genai import types

from research.config.prompts import PROMPT_YOUTUBE_TRANSCRIPTION
from research.config.settings import get_settings
from research.utils.llm import get_client

logger = logging.getLogger(__name__)


async def analyze_youtube_video(
    url: str,
    output_path: Path,
    timestamp: int = 30,
) -> str:
    """Analyze a YouTube video using Gemini's native video understanding.

    Passes the YouTube URL directly to Gemini using FileData(file_uri=url)
    for native video understanding, returning a transcript with key insights.

    Args:
        url: The public URL of the YouTube video.
        output_path: The path to save the transcript markdown file.
        timestamp: The interval in seconds for inserting timestamps.

    Returns:
        The transcript text.
    """

    settings = get_settings()
    client = get_client()
    model_name = settings.youtube_transcription_model

    prompt = PROMPT_YOUTUBE_TRANSCRIPTION.format(timestamp=timestamp)

    parts: list[types.Part] = [
        types.Part(file_data=types.FileData(file_uri=url)),
        types.Part(text=prompt),
    ]

    logger.info(f"Analyzing video: {url} (this may take a while)")
    start_time = time.monotonic()

    response = await client.aio.models.generate_content(
        model=model_name,
        contents=types.Content(parts=parts),
    )

    elapsed = time.monotonic() - start_time
    logger.info(f"Video analysis for {url} finished in {elapsed:.2f} seconds.")

    transcript = response.text or ""
    if not transcript:
        msg = f"Could not generate transcript for {url}."
        logger.error(msg)
        output_path.write_text(msg, encoding="utf-8")
        return msg

    output_path.write_text(transcript, encoding="utf-8")
    logger.info(f"Transcript saved to {output_path}")

    return transcript


def get_video_id(url: str) -> str | None:
    """Extract the YouTube video ID from various URL formats."""

    parsed_url = urlparse(url)
    if "youtube.com" in parsed_url.netloc:
        return parse_qs(parsed_url.query).get("v", [None])[0]
    if "youtu.be" in parsed_url.netloc:
        return parsed_url.path.lstrip("/")

    return None
