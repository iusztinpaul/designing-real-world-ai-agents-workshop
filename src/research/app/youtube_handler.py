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
    # Use a dedicated model for video transcription (may differ from the
    # default research model, e.g. a model with better multimodal support)
    model_name = settings.youtube_transcription_model

    # Format the transcription prompt with the desired timestamp interval
    # (e.g. insert [MM:SS] markers every 30 seconds)
    prompt = PROMPT_YOUTUBE_TRANSCRIPTION.format(timestamp=timestamp)

    # Build a multimodal request with two parts:
    # 1. The video itself — passed as a FileData URI so Gemini can watch it natively
    # 2. The text prompt — instructions for how to transcribe and annotate the video
    parts: list[types.Part] = [
        types.Part(file_data=types.FileData(file_uri=url)),
        types.Part(text=prompt),
    ]

    # Make the async API call. Video analysis can be slow depending on
    # video length, so we measure elapsed time for logging.
    logger.info(f"Analyzing video: {url} (this may take a while)")
    start_time = time.monotonic()

    response = await client.aio.models.generate_content(
        model=model_name,
        contents=types.Content(parts=parts),
    )

    elapsed = time.monotonic() - start_time
    logger.info(f"Video analysis for {url} finished in {elapsed:.2f} seconds.")

    # Extract the transcript text from the response
    transcript = response.text or ""
    if not transcript:
        # If Gemini returned nothing (e.g. video was inaccessible or too long),
        # write an error message to the output file and return it
        msg = f"Could not generate transcript for {url}."
        logger.error(msg)
        output_path.write_text(msg, encoding="utf-8")
        return msg

    # Persist the transcript as a markdown file for later compilation
    output_path.write_text(transcript, encoding="utf-8")
    logger.info(f"Transcript saved to {output_path}")

    return transcript


def get_video_id(url: str) -> str | None:
    """Extract the YouTube video ID from various URL formats."""

    parsed_url = urlparse(url)
    # Standard format: https://www.youtube.com/watch?v=VIDEO_ID
    if "youtube.com" in parsed_url.netloc:
        return parse_qs(parsed_url.query).get("v", [None])[0]
    # Short format: https://youtu.be/VIDEO_ID
    if "youtu.be" in parsed_url.netloc:
        return parsed_url.path.lstrip("/")

    return None
