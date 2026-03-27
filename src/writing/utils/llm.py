"""Gemini client helpers for LLM interactions."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from writing.config.settings import get_settings
from writing.utils.opik_utils import track_genai_client

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
        model: Model name override. Defaults to settings.writer_model.
        response_schema: If provided, Gemini returns JSON matching this Pydantic model.
        system_instruction: Optional system instruction for the model.

    Returns:
        The response text from Gemini.
    """

    settings = get_settings()
    client = get_client()
    model_name = model or settings.writer_model

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


async def call_gemini_image(
    prompt: str,
    output_path: Path,
    reference_images: list[Path] | None = None,
) -> Path:
    """Generate an image using Gemini Flash Image (native generation) and save to disk.

    Uses the gemini-2.5-flash-image model with response_modalities=["IMAGE"]
    for native image generation. Optionally includes reference images as
    few-shot style examples.

    Args:
        prompt: The image generation prompt.
        output_path: Path to save the generated image.
        reference_images: Optional list of image paths to include as reference.

    Returns:
        The path to the saved image.
    """

    settings = get_settings()
    client = get_client()

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
    )

    # Build contents with optional reference images
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

    response = await client.aio.models.generate_content(
        model=settings.image_model,
        contents=contents,
        config=config,
    )

    if not response.candidates or not response.candidates[0].content.parts:
        msg = "Gemini returned no image content."
        raise RuntimeError(msg)

    # Find the image part in the response
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image = part.as_image()
            image.save(str(output_path))
            logger.info(f"Image saved to {output_path}")
            return output_path

    msg = "Gemini response contained no image data."
    raise RuntimeError(msg)
