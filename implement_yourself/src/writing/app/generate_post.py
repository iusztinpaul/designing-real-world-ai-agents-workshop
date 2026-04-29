"""Core post generation pipeline (no evaluator-optimizer loop yet).

The evaluate-optimize loop lands in #013. For now this runs one Gemini call
and returns the result with stable GeneratePostResult shape.
"""

import logging

from writing.app.dataset_loader import load_examples
from writing.app.post_writer_handler import write_post
from writing.app.profile_loader import load_profiles
from writing.models.schemas import GeneratePostResult

logger = logging.getLogger(__name__)


async def generate_post(
    guideline: str,
    research: str,
) -> GeneratePostResult:
    """Generate a LinkedIn post (single shot, no review loop yet).

    Loads writing profiles and few-shot examples, then calls Gemini once
    via write_post. The review/edit loop is added in ticket #013.

    Args:
        guideline: The post guideline content.
        research: The research material content.

    Returns:
        GeneratePostResult with the final post, initial version in versions list,
        and an empty reviews list (populated in #013).
    """
    profiles = load_profiles()
    examples = load_examples()
    post_examples_text = examples.format_post_examples()

    logger.info("Generating initial LinkedIn post...")
    post = await write_post(guideline, research, profiles, post_examples_text)

    return GeneratePostResult(post=post, versions=[post], reviews=[])
