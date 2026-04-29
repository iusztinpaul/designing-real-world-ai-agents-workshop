"""Gemini LLM client utilities for the LinkedIn Writer MCP server."""

import logging
from functools import lru_cache
from typing import Any

import google.genai as genai
import google.genai.types as types
from pydantic import BaseModel

from writing.config.settings import get_settings

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
        model: The Gemini model name to use. Defaults to settings.writer_model.
        response_schema: Optional Pydantic model for structured JSON output.
        system_instruction: Optional system-level instruction prepended to the request.

    Returns:
        The text content of the Gemini response.
    """
    settings = get_settings()
    client = get_client()
    resolved_model = model or settings.writer_model

    config_kwargs: dict[str, Any] = {}
    if response_schema is not None:
        config_kwargs["response_mime_type"] = "application/json"
        config_kwargs["response_schema"] = response_schema
    if system_instruction is not None:
        config_kwargs["system_instruction"] = system_instruction

    config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

    logger.debug("Calling Gemini model=%s", resolved_model)

    response = await client.aio.models.generate_content(
        model=resolved_model,
        contents=prompt,
        config=config,
    )

    return response.text
