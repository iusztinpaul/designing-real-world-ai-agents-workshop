"""Gemini LLM client utilities for the Deep Research MCP server."""

import logging
from functools import lru_cache

import google.genai as genai
import google.genai.types as types
from pydantic import BaseModel

from research.config.settings import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_client() -> genai.Client:
    """Return a cached singleton Gemini client.

    Returns:
        A configured google.genai.Client instance.
    """
    settings = get_settings()
    return genai.Client(api_key=settings.google_api_key.get_secret_value())


async def call_gemini(
    prompt: str,
    model: str | None = None,
    response_schema: type[BaseModel] | None = None,
    system_instruction: str | None = None,
) -> str:
    """Call the Gemini API with a text prompt.

    Args:
        prompt: The user prompt to send.
        model: The Gemini model name to use. Defaults to settings.gemini_model.
        response_schema: Optional Pydantic model for structured JSON output.
        system_instruction: Optional system-level instruction prepended to the request.

    Returns:
        The text content of the Gemini response.
    """
    settings = get_settings()
    client = get_client()
    resolved_model = model or settings.gemini_model

    generate_kwargs: dict = {}
    if system_instruction:
        generate_kwargs["system_instruction"] = system_instruction

    config_kwargs: dict = {}
    if response_schema is not None:
        config_kwargs["response_mime_type"] = "application/json"
        config_kwargs["response_schema"] = response_schema

    if config_kwargs:
        generate_kwargs["config"] = genai.types.GenerateContentConfig(**config_kwargs)

    logger.debug("Calling Gemini model=%s", resolved_model)

    response = await client.aio.models.generate_content(
        model=resolved_model,
        contents=prompt,
        **generate_kwargs,
    )

    return response.text


async def call_gemini_search(
    prompt: str,
    model: str | None = None,
) -> tuple[str, list[dict[str, str]]]:
    """Call the Gemini API with Google Search grounding enabled.

    Grounding and response_schema are mutually exclusive — this function
    never uses response_schema.

    Args:
        prompt: The user prompt to send.
        model: The Gemini model name to use. Defaults to settings.gemini_model.

    Returns:
        A tuple of (answer_text, grounding_sources) where grounding_sources is
        a list of dicts with "url" and "title" keys deduplicated by URL.
    """
    settings = get_settings()
    client = get_client()
    resolved_model = model or settings.gemini_model

    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
    )

    logger.debug("Calling Gemini with grounded search, model=%s", resolved_model)

    response = await client.aio.models.generate_content(
        model=resolved_model,
        contents=prompt,
        config=config,
    )

    answer_text = response.text or ""
    sources = extract_grounding_sources(response)

    return answer_text, sources


def extract_grounding_sources(response: object) -> list[dict[str, str]]:
    """Extract and deduplicate grounding sources from a Gemini response.

    Walks response.candidates[0].grounding_metadata.grounding_chunks[*].web
    defensively — each layer may be None. Deduplicates by URL.

    Args:
        response: The raw Gemini API response object.

    Returns:
        A list of dicts with "url" and "title" keys, deduplicated by URL.
        Returns [] if no grounding metadata is present.
    """
    sources: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    try:
        candidates = getattr(response, "candidates", None)
        if not candidates:
            return sources

        candidate = candidates[0]
        grounding_metadata = getattr(candidate, "grounding_metadata", None)
        if grounding_metadata is None:
            return sources

        grounding_chunks = getattr(grounding_metadata, "grounding_chunks", None)
        if not grounding_chunks:
            return sources

        for chunk in grounding_chunks:
            web = getattr(chunk, "web", None)
            if web is None:
                continue

            url = getattr(web, "uri", None) or ""
            title = getattr(web, "title", None) or ""

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)
            sources.append({"url": url, "title": title})

    except Exception as exc:
        logger.warning("Failed to extract grounding sources: %s", exc)

    return sources
