"""LinkedIn post generation tool with evaluate-optimize loop."""

import json
import logging
from pathlib import Path
from typing import Any

from writing.app.dataset_loader import load_examples
from writing.app.post_reviewer_handler import review_post
from writing.app.post_writer_handler import edit_post, write_post
from writing.app.profile_loader import load_profiles
from writing.config.constants import (
    GUIDELINE_FILE,
    MEMORY_FOLDER,
    POST_FILE,
    RESEARCH_FILE,
)
from writing.config.settings import get_settings

logger = logging.getLogger(__name__)


async def generate_post_tool(working_dir: str) -> dict[str, Any]:
    """Generate a LinkedIn post with an evaluate-optimize loop.

    Reads guideline.md and research.md, generates an initial post, then runs
    N rounds of review + edit to refine it. All intermediate versions are
    saved in .memory/.

    Args:
        working_dir: Path to the working directory with guideline.md and research.md.

    Returns:
        Dict with status, message, and output file path.
    """

    settings = get_settings()
    working_path = Path(working_dir)

    # Validate inputs
    guideline_path = working_path / GUIDELINE_FILE
    research_path = working_path / RESEARCH_FILE
    if not guideline_path.exists():
        msg = f"{GUIDELINE_FILE} not found in {working_dir}"
        raise FileNotFoundError(msg)
    if not research_path.exists():
        msg = f"{RESEARCH_FILE} not found in {working_dir}"
        raise FileNotFoundError(msg)

    guideline = guideline_path.read_text(encoding="utf-8")
    research = research_path.read_text(encoding="utf-8")
    profiles = load_profiles()
    examples = load_examples()
    post_examples_text = examples.format_post_examples()

    # Create .memory/ for intermediate files
    memory_path = working_path / MEMORY_FOLDER
    memory_path.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate initial post
    logger.info("Generating initial LinkedIn post...")
    post = await write_post(guideline, research, profiles, post_examples_text)

    # Save initial version (version 0)
    version = 0
    version_path = working_path / f"post_{version}.md"
    version_path.write_text(post.content, encoding="utf-8")
    logger.info(f"Initial post saved to post_{version}.md")

    # Step 2: Review/edit loop
    for i in range(settings.num_reviews):
        iteration = i + 1
        logger.info(f"Review/edit iteration {iteration}/{settings.num_reviews}...")

        # Review
        reviews_result = await review_post(post, guideline, profiles)
        reviews = reviews_result.reviews

        if not reviews:
            logger.info(f"Iteration {iteration}: No issues found. Skipping edit.")
            continue

        logger.info(f"Iteration {iteration}: {len(reviews)} review(s) found.")

        # Save reviews to .memory/
        reviews_data = [r.model_dump() for r in reviews]
        (memory_path / f"reviews_{iteration}.json").write_text(
            json.dumps(reviews_data, indent=2), encoding="utf-8"
        )

        # Edit
        post = await edit_post(
            post, reviews, guideline, research, profiles, post_examples_text
        )

        # Save new version
        version = iteration
        version_path = working_path / f"post_{version}.md"
        version_path.write_text(post.content, encoding="utf-8")
        logger.info(f"Edited post saved to post_{version}.md")

    # Save final version as post.md
    output_path = working_path / POST_FILE
    output_path.write_text(post.content, encoding="utf-8")
    logger.info(f"Final post saved to {output_path}")

    return {
        "status": "success",
        "review_iterations": settings.num_reviews,
        "output_path": str(output_path.resolve()),
        "message": (
            f"Generated LinkedIn post with {settings.num_reviews} review/edit iterations. "
            f"Final post saved to {POST_FILE}"
        ),
        "post": post.content,
    }
