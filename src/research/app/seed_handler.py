"""Seed file parsing logic."""

import logging
import re

from research.config.prompts import PROMPT_EXTRACT_SEED
from research.models.schemas import SeedExtraction
from research.utils.llm import call_gemini

logger = logging.getLogger(__name__)


def extract_urls_regex(text: str) -> list[str]:
    """Extract all HTTP/HTTPS URLs from the given text."""

    url_pattern = re.compile(r"https?://[^\s)>\"',]+")

    return url_pattern.findall(text)


def filter_youtube_urls(urls: list[str]) -> list[str]:
    """Filter URLs to only YouTube links."""

    return [u for u in urls if "youtube.com" in u or "youtu.be" in u]


async def extract_seed_content(seed_text: str) -> SeedExtraction:
    """Parse a seed document and extract structured research information.

    Uses Gemini with structured output to extract topics, questions,
    and YouTube URLs. Also uses regex to reliably catch all URLs.

    Args:
        seed_text: The raw text content of the seed file.

    Returns:
        A SeedExtraction with extracted information.
    """

    prompt = PROMPT_EXTRACT_SEED.format(seed_text=seed_text)

    response_text = await call_gemini(prompt, response_schema=SeedExtraction)
    extraction = SeedExtraction.model_validate_json(response_text)

    # Also extract YouTube URLs via regex to ensure none are missed
    regex_urls = extract_urls_regex(seed_text)
    regex_youtube = filter_youtube_urls(regex_urls)
    for url in regex_youtube:
        if url not in extraction.youtube_urls:
            extraction.youtube_urls.append(url)

    return extraction
