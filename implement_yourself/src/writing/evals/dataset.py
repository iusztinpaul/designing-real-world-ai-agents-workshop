"""Dataset upload and management for Opik evaluation."""

import logging

import opik

from writing.app.dataset_loader import DATASET_DIR, load_by_scope

logger = logging.getLogger(__name__)

DATASET_NAME = "linkedin-posts"
DATASET_DESCRIPTION = "LinkedIn posts dataset for LLM judge evaluation"


def upload_dataset_to_opik(split: str) -> opik.Dataset:
    """Upload a dataset split to Opik with flat fields.

    Each item has flat top-level keys for easy reading in the Opik UI.

    Args:
        split: The scope/split to upload (e.g., 'dev_evaluator', 'test_evaluator').

    Returns:
        The Opik Dataset object.

    Raises:
        ValueError: If no entries are found for the given split.
    """
    entries = load_by_scope(split)
    if not entries:
        msg = f"No entries found for split '{split}'"
        raise ValueError(msg)

    items: list[dict] = []
    for entry in entries:
        if entry.label is None or entry.critique is None:
            continue

        generated = entry.generated_content(DATASET_DIR)
        guideline = entry.guideline_content(DATASET_DIR)
        research = entry.research_content(DATASET_DIR)

        if not generated:
            logger.warning("Skipping %s: missing generated post", entry.slug)
            continue

        items.append(
            {
                "name": entry.slug,
                "slug": entry.slug,
                "guideline": guideline,
                "research": research,
                "generated_post": generated,
                "label": entry.label.value,
                "critique": entry.critique,
            }
        )

    dataset_full_name = f"{DATASET_NAME}-{split}"
    client = opik.Opik()
    dataset = client.get_or_create_dataset(
        name=dataset_full_name, description=f"{DATASET_DESCRIPTION} ({split})"
    )
    dataset.clear()
    dataset.insert(items)

    logger.info("Uploaded %d items to Opik dataset '%s'", len(items), dataset_full_name)

    return dataset


def upload_online_dataset_to_opik(split: str) -> opik.Dataset:
    """Upload a dataset split for online evaluation (generate posts on the fly).

    Only includes guideline and research — no pre-generated post.
    The evaluation task will generate the post using the writing workflow.

    Args:
        split: The scope/split to upload.

    Returns:
        The Opik Dataset object.

    Raises:
        ValueError: If no entries are found for the given split.
    """
    entries = load_by_scope(split)
    if not entries:
        msg = f"No entries found for split '{split}'"
        raise ValueError(msg)

    items: list[dict] = []
    for entry in entries:
        guideline = entry.guideline_content(DATASET_DIR)
        research = entry.research_content(DATASET_DIR)

        if not guideline:
            logger.warning("Skipping %s: missing guideline", entry.slug)
            continue

        item: dict = {
            "name": entry.slug,
            "slug": entry.slug,
            "guideline": guideline,
            "research": research,
        }
        if entry.label is not None:
            item["label"] = entry.label.value
        items.append(item)

    dataset_full_name = f"{DATASET_NAME}-online-{split}"
    client = opik.Opik()
    dataset = client.get_or_create_dataset(
        name=dataset_full_name,
        description=f"{DATASET_DESCRIPTION} (online, {split})",
    )
    dataset.clear()
    dataset.insert(items)

    logger.info("Uploaded %d items to Opik dataset '%s'", len(items), dataset_full_name)

    return dataset
