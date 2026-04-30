"""Image generation logic using Gemini Flash Image."""

import logging
from pathlib import Path

from writing.config.prompts import PROMPT_GENERATE_IMAGE, PROMPT_IMAGE_SCENE
from writing.models.schemas import Profiles
from writing.utils.llm import call_gemini, call_gemini_image

logger = logging.getLogger(__name__)


async def _extract_visual_scene(post_content: str) -> str:
    """Distill a text-free abstract visual scene from the post.

    Sends the post to the text Gemini model and asks it to describe ONE
    abstract visual scene using only geometric shapes and color — no text,
    no people, no diagrams.

    Args:
        post_content: The full LinkedIn post text.

    Returns:
        A 2-3 sentence scene description (no preamble).
    """
    prompt = PROMPT_IMAGE_SCENE.format(post=post_content)
    scene = await call_gemini(prompt)

    logger.info("Extracted visual scene: %s", scene)

    return scene


async def generate_post_image(
    post_content: str,
    profiles: Profiles,
    output_path: Path,
    reference_images: list[Path] | None = None,
) -> Path:
    """Generate a LinkedIn post image using Gemini Flash Image.

    First extracts a text-free visual scene description from the post via a
    text LLM call, then renders that scene with Gemini Flash Image anchored
    to the branding and character profiles, with optional reference images as
    few-shot style examples.

    Args:
        post_content: The post text to base the image on.
        profiles: Writing profiles (uses character and branding profiles).
        output_path: Path where the generated image will be saved.
        reference_images: Optional list of image paths as style references.

    Returns:
        The path to the saved image.
    """
    scene = await _extract_visual_scene(post_content)

    prompt = PROMPT_GENERATE_IMAGE.format(
        branding_profile=profiles.branding.content,
        character_profile=profiles.character.content,
        scene=scene,
    )

    return await call_gemini_image(prompt, output_path, reference_images)
