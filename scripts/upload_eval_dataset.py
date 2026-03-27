"""Upload evaluation dataset splits to Opik.

Usage:
    uv run python scripts/upload_eval_dataset.py [--split SPLIT]
"""

import logging

import click

from writing.evals.dataset import upload_dataset_to_opik
from writing.utils.opik_utils import configure_opik


@click.command()
@click.option(
    "--split",
    default="all",
    type=click.Choice(["dev_evaluator", "test_evaluator", "all"]),
    help="Which split to upload (default: all)",
)
def main(split: str) -> None:
    """Upload evaluation dataset to Opik."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    configure_opik()

    splits = ["dev_evaluator", "test_evaluator"] if split == "all" else [split]

    for s in splits:
        dataset = upload_dataset_to_opik(s)
        print(f"Uploaded: {dataset.name} ({len(dataset.get_items())} items)")


if __name__ == "__main__":
    main()
