"""Gemini LLM client utilities for the Deep Research MCP server."""

import logging
from functools import lru_cache

import google.genai as genai
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
