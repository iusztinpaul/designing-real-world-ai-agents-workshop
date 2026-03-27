"""YouTube transcription operations using Gemini."""

import asyncio
import logging
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from google.genai import errors, types
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from research.config.constants import (
    YOUTUBE_TRANSCRIPTION_MAX_RETRIES,
    YOUTUBE_TRANSCRIPTION_RETRY_WAIT_MAX_SECONDS,
    YOUTUBE_TRANSCRIPTION_RETRY_WAIT_MIN_SECONDS,
)
from research.config.prompts import PROMPT_YOUTUBE_TRANSCRIPTION
from research.config.settings import get_settings
from research.utils.llm import get_client

logger = logging.getLogger(__name__)


@retry(
    retry=retry_if_exception_type(errors.ServerError),
    wait=wait_exponential(
        multiplier=1,
        min=YOUTUBE_TRANSCRIPTION_RETRY_WAIT_MIN_SECONDS,
        max=YOUTUBE_TRANSCRIPTION_RETRY_WAIT_MAX_SECONDS,
    ),
    stop=stop_after_attempt(YOUTUBE_TRANSCRIPTION_MAX_RETRIES),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def transcribe_youtube(
    url: str,
    output_path: Path,
    timestamp: int = 30,
) -> None:
    """Transcribe a public YouTube video using Gemini and save to a file.

    Args:
        url: The public URL of the YouTube video.
        output_path: The path to save the transcription markdown file.
        timestamp: The interval in seconds for inserting timestamps.
    """

    settings = get_settings()
    client = get_client()
    model_name = settings.youtube_transcription_model

    prompt = PROMPT_YOUTUBE_TRANSCRIPTION.format(timestamp=timestamp)

    parts: list[types.Part] = [
        types.Part(file_data=types.FileData(file_uri=url)),
        types.Part(text=prompt),
    ]

    logger.info(f"Processing transcription request for {url}, it may take a while.")
    start_time = time.monotonic()
    try:
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=types.Content(parts=parts),
        )
    except errors.ServerError:
        logger.warning(f"Server error for {url}, re-raising to trigger retry.")
        raise
    except errors.APIError as e:
        msg = f"API Error during transcription for {url}: {e}"
        logger.error(msg, exc_info=True)
        output_path.write_text(msg, encoding="utf-8")
        return
    except Exception as e:
        msg = f"Unexpected error for {url}: {e}"
        logger.error(msg, exc_info=True)
        output_path.write_text(msg, encoding="utf-8")
        return

    elapsed = time.monotonic() - start_time
    logger.info(f"Transcription for {url} finished in {elapsed:.2f} seconds.")

    if not response.text:
        msg = f"Could not generate transcription for {url}.\n\n{response}"
        logger.error(msg)
        output_path.write_text(msg, encoding="utf-8")
        return

    output_path.write_text(response.text, encoding="utf-8")
    logger.info(f"Transcription saved to {output_path}")


def get_video_id(url: str) -> str | None:
    """Extract the YouTube video ID from various URL formats."""

    parsed_url = urlparse(url)
    if "youtube.com" in parsed_url.netloc:
        return parse_qs(parsed_url.query).get("v", [None])[0]
    if "youtu.be" in parsed_url.netloc:
        return parsed_url.path.lstrip("/")

    return None


async def process_youtube_url(
    url: str,
    dest_folder: Path,
    semaphore: asyncio.Semaphore,
) -> None:
    """Process a single YouTube URL by generating a filename and transcribing.

    Args:
        url: The YouTube URL to process.
        dest_folder: The directory where the transcription file should be saved.
        semaphore: Asyncio semaphore to limit concurrency.
    """

    video_id = get_video_id(url)
    if not video_id:
        sanitized = url.replace("https://", "").replace("http://", "").replace("/", "_")
        logger.warning(f"Could not extract video ID from URL: {url}")
        video_id = sanitized

    output_path = dest_folder / f"{video_id}.md"

    async with semaphore:
        await transcribe_youtube(url=url, output_path=output_path)
