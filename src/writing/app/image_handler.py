"""Image generation logic using Gemini Flash Image."""

import logging
from pathlib import Path

from writing.config.prompts import PROMPT_GENERATE_IMAGE
from writing.models.schemas import Profiles
from writing.utils.llm import call_gemini_image

logger = logging.getLogger(__name__)


async def generate_post_image(
    post_content: str,
    profiles: Profiles,
    output_path: Path,
    reference_images: list[Path] | None = None,
) -> Path:
    """Generate a LinkedIn post image using Gemini Flash Image.

    The image is anchored to the character and branding profiles for
    consistent visual identity, with optional reference images as
    few-shot style examples.

    Args:
        post_content: The post text to base the image on.
        profiles: Writing profiles (uses character and branding).
        output_path: Path to save the generated image.
        reference_images: Optional list of image paths as style references.

    Returns:
        The path to the saved image.
    """

    prompt = PROMPT_GENERATE_IMAGE.format(
        branding_profile=profiles.branding.content,
        character_profile=profiles.character.content,
        post=post_content,
    )

    return await call_gemini_image(prompt, output_path, reference_images)
