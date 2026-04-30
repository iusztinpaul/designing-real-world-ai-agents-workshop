"""Gemini LLM client utilities for the LinkedIn Writer MCP server."""

import io
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import google.genai as genai
import google.genai.types as types
from PIL import Image
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


async def call_gemini_image(
    prompt: str,
    output_path: Path,
    reference_images: list[Path] | None = None,
) -> Path:
    """Generate an image using Gemini Flash Image and save it to disk.

    Uses ``response_modalities=["IMAGE"]`` for native image generation.
    Optional reference images are sent as inline_data parts before the prompt
    to act as few-shot style examples.

    Args:
        prompt: The image generation prompt.
        output_path: Path where the generated image will be saved.
        reference_images: Optional list of image paths to include as style references.

    Returns:
        The path to the saved image.

    Raises:
        RuntimeError: If Gemini returns no image in the response.
    """
    settings = get_settings()
    client = get_client()

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
    )

    # Build contents list: optional reference images first, then the prompt text
    contents: list[types.Part] = []
    if reference_images:
        for img_path in reference_images:
            if img_path.exists():
                img_bytes = img_path.read_bytes()
                suffix = img_path.suffix.lower()
                mime = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                }.get(suffix, "image/png")
                contents.append(
                    types.Part(inline_data=types.Blob(mime_type=mime, data=img_bytes))
                )
    contents.append(types.Part(text=prompt))

    logger.debug("Calling Gemini image model=%s", settings.image_model)

    response = await client.aio.models.generate_content(
        model=settings.image_model,
        contents=contents,
        config=config,
    )

    if not response.candidates or not response.candidates[0].content.parts:
        raise RuntimeError("Gemini returned no image content.")

    # Find the first part that contains an image
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pil_image = Image.open(io.BytesIO(part.inline_data.data))
            pil_image = pil_image.resize((1200, 1200))
            pil_image.save(str(output_path))
            logger.info("Image saved to %s", output_path)
            return output_path

    raise RuntimeError("Gemini returned no image content.")
