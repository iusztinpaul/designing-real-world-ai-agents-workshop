"""LinkedIn post generation logic."""

import logging

from writing.config.prompts import PROMPT_WRITE_POST
from writing.models.schemas import Post, Profiles
from writing.utils.llm import call_gemini

logger = logging.getLogger(__name__)


async def write_post(
    guideline: str,
    research: str,
    profiles: Profiles,
    post_examples: str = "<none>",
) -> Post:
    """Generate a LinkedIn post from guideline, research, profiles, and examples.

    Args:
        guideline: The post guideline content.
        research: The research material content.
        profiles: The writing profiles to follow.
        post_examples: Formatted few-shot post examples.

    Returns:
        A Post with the generated content.
    """
    prompt = PROMPT_WRITE_POST.format(
        guideline=guideline,
        research=research,
        structure_profile=profiles.structure.content,
        terminology_profile=profiles.terminology.content,
        character_profile=profiles.character.content,
        post_examples=post_examples,
    )

    logger.info("Generating LinkedIn post via Gemini...")
    response = await call_gemini(prompt)

    return Post(content=response)
