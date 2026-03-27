"""Gemini client helpers for LLM interactions."""

import logging
from functools import lru_cache
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from research.config.settings import get_settings
from research.utils.opik_utils import track_genai_client

logger = logging.getLogger(__name__)


@lru_cache
def get_client() -> genai.Client:
    """Create and cache a Gemini client, with Opik tracking if configured."""

    settings = get_settings()
    client = genai.Client(api_key=settings.google_api_key.get_secret_value())

    return track_genai_client(client)


async def call_gemini(
    prompt: str,
    model: str | None = None,
    response_schema: type[BaseModel] | None = None,
    system_instruction: str | None = None,
) -> str:
    """Call Gemini with optional structured output.

    Args:
        prompt: The prompt to send to Gemini.
        model: Model name override. Defaults to settings.gemini_model.
        response_schema: If provided, Gemini returns JSON matching this Pydantic model.
        system_instruction: Optional system instruction for the model.

    Returns:
        The response text from Gemini.
    """

    settings = get_settings()
    client = get_client()
    model_name = model or settings.gemini_model

    config_kwargs: dict[str, Any] = {}
    if response_schema is not None:
        config_kwargs["response_mime_type"] = "application/json"
        config_kwargs["response_schema"] = response_schema
    if system_instruction is not None:
        config_kwargs["system_instruction"] = system_instruction

    config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

    response = await client.aio.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )

    return response.text


async def call_gemini_search(
    prompt: str,
    model: str | None = None,
) -> tuple[str, list[dict[str, str]]]:
    """Call Gemini with Google Search grounding.

    Google Search grounding and structured output cannot be used simultaneously,
    so this function returns raw text + programmatically extracted sources.

    Args:
        prompt: The search prompt to send to Gemini.
        model: Model name override. Defaults to settings.gemini_model.

    Returns:
        A tuple of (answer_text, sources_list) where sources_list contains
        dicts with 'url' and 'title' keys.
    """

    settings = get_settings()
    client = get_client()
    model_name = model or settings.gemini_model

    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
    )

    response = await client.aio.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )

    answer_text = response.text or ""
    sources = extract_grounding_sources(response)

    return answer_text, sources


def extract_grounding_sources(
    response: types.GenerateContentResponse,
) -> list[dict[str, str]]:
    """Extract source URLs and titles from grounding metadata.

    Args:
        response: The Gemini response object.

    Returns:
        A list of dicts with 'url' and 'title' keys.
    """

    sources: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    if not response.candidates:
        return sources

    candidate = response.candidates[0]
    grounding_metadata = getattr(candidate, "grounding_metadata", None)
    if grounding_metadata is None:
        return sources

    grounding_chunks = getattr(grounding_metadata, "grounding_chunks", None)
    if grounding_chunks is None:
        return sources

    for chunk in grounding_chunks:
        web = getattr(chunk, "web", None)
        if web is None:
            continue
        url = getattr(web, "uri", "") or ""
        title = getattr(web, "title", "") or ""
        if url and url not in seen_urls:
            seen_urls.add(url)
            sources.append({"url": url, "title": title})

    return sources
