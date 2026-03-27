"""Core evaluate-optimize loop for LinkedIn post generation.

This is the single source of truth for the generate → [review → edit] × N
pipeline. Used by both MCP tools and the evals harness.
"""

import logging

from writing.app.dataset_loader import load_examples
from writing.app.post_reviewer_handler import review_post
from writing.app.post_writer_handler import edit_post, write_post
from writing.app.profile_loader import load_profiles
from writing.config.settings import get_settings
from writing.models.schemas import Post

logger = logging.getLogger(__name__)


async def generate_post(
    guideline: str,
    research: str,
) -> Post:
    """Generate a LinkedIn post with the full evaluate-optimize loop.

    Generates an initial post, then runs N rounds of review + edit to
    refine it. Text only — no image generation.

    Args:
        guideline: The post guideline content.
        research: The research material content.

    Returns:
        The final Post after all review/edit iterations.
    """

    settings = get_settings()
    profiles = load_profiles()
    examples = load_examples()
    post_examples_text = examples.format_post_examples()

    # Step 1: Generate initial post
    logger.info("Generating initial LinkedIn post...")
    post = await write_post(guideline, research, profiles, post_examples_text)

    # Step 2: Review/edit loop
    for i in range(settings.num_reviews):
        iteration = i + 1
        logger.info(f"Review/edit iteration {iteration}/{settings.num_reviews}...")

        reviews_result = await review_post(post, guideline, profiles)
        reviews = reviews_result.reviews

        if not reviews:
            logger.info(f"Iteration {iteration}: No issues found. Skipping edit.")
            continue

        logger.info(f"Iteration {iteration}: {len(reviews)} review(s) found.")

        post = await edit_post(
            post, reviews, guideline, research, profiles, post_examples_text
        )

    return post
