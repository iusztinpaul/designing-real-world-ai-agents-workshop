"""Edit post tool implementation for the LinkedIn Writer MCP server."""

import json
import logging
from pathlib import Path
from typing import Any

from writing.app.dataset_loader import load_examples
from writing.app.post_reviewer_handler import review_post
from writing.app.post_writer_handler import edit_post
from writing.app.profile_loader import load_profiles
from writing.config.constants import (
    GUIDELINE_FILE,
    MEMORY_FOLDER,
    POST_FILE,
    RESEARCH_FILE,
)
from writing.models.schemas import Post

logger = logging.getLogger(__name__)


async def edit_post_tool(
    working_dir: str, human_feedback: str, delete_iterations: bool = False
) -> dict[str, Any]:
    """Edit an existing LinkedIn post based on human feedback.

    Args:
        working_dir: Directory containing the existing post.md.
        human_feedback: Feedback from the human on how to edit the post.
        delete_iterations: Whether to delete intermediate post versions and reviews.

    Returns:
        A dict with status, reviews_count, output_path, message, and post.

    Raises:
        FileNotFoundError: If post.md or guideline.md is missing.
    """
    working_path = Path(working_dir)

    # Step 1: Resolve and validate paths
    post_path = working_path / POST_FILE
    guideline_path = working_path / GUIDELINE_FILE
    research_path = working_path / RESEARCH_FILE

    if not post_path.exists():
        msg = f"{POST_FILE} not found in {working_dir}. Run generate_post first."
        raise FileNotFoundError(msg)

    if not guideline_path.exists():
        msg = f"{GUIDELINE_FILE} not found in {working_dir}"
        raise FileNotFoundError(msg)

    # Read files (research.md is optional)
    post_content = post_path.read_text(encoding="utf-8")
    guideline = guideline_path.read_text(encoding="utf-8")
    research = (
        research_path.read_text(encoding="utf-8") if research_path.exists() else ""
    )

    # Step 2: Load profiles and few-shot examples
    profiles = load_profiles()
    examples = load_examples()
    post_examples_text = examples.format_post_examples()

    # Step 3: Construct Post object
    post = Post(content=post_content)

    # Step 4: Run one review pass with human feedback
    reviews_result = await review_post(
        post, guideline, profiles, human_feedback=human_feedback
    )

    # Step 5: Write reviews to .memory/reviews_edit.json (unless delete_iterations=True)
    if not delete_iterations:
        memory_path = working_path / MEMORY_FOLDER
        memory_path.mkdir(parents=True, exist_ok=True)
        reviews_data = [r.model_dump() for r in reviews_result.reviews]
        reviews_edit_path = memory_path / "reviews_edit.json"
        reviews_edit_path.write_text(
            json.dumps(reviews_data, indent=2), encoding="utf-8"
        )
        logger.info("Saved edit reviews to %s", reviews_edit_path.name)

    # Step 6: Handle empty reviews case
    if not reviews_result.reviews:
        logger.info("No issues found. Post unchanged.")
        return {
            "status": "success",
            "reviews_count": 0,
            "output_path": str(post_path.resolve()),
            "message": "No issues found based on feedback. Post unchanged.",
            "post": post.content,
        }

    # Step 7: Edit the post based on reviews
    edited_post = await edit_post(
        post,
        reviews_result.reviews,
        guideline,
        research,
        profiles,
        post_examples_text,
    )

    # Step 8: Write versioned post_N.md (unless delete_iterations=True)
    if not delete_iterations:
        next_version = len(sorted(working_path.glob("post_*.md")))
        versioned_path = working_path / f"post_{next_version}.md"
        versioned_path.write_text(edited_post.content, encoding="utf-8")
        logger.info("Saved versioned post to %s", versioned_path.name)

    # Step 9: Always overwrite post.md with the edited post
    post_path.write_text(edited_post.content, encoding="utf-8")
    logger.info("Updated post.md with edited content")

    # Step 10: Return success dict
    reviews_summary = "\n".join(
        f"- [{r.profile}] {r.location}: {r.comment}" for r in reviews_result.reviews
    )
    count = len(reviews_result.reviews)

    return {
        "status": "success",
        "reviews_count": count,
        "output_path": str(post_path.resolve()),
        "message": (
            f"Applied {count} review(s) based on feedback. "
            f"Updated post saved to {POST_FILE}\n\nReviews addressed:\n{reviews_summary}"
        ),
        "post": edited_post.content,
    }
