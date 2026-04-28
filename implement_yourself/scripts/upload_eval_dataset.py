"""Upload evaluation dataset splits to Opik.

Usage:
    uv run python scripts/upload_eval_dataset.py [--split SPLIT]
"""

import click

from writing.evals.dataset import upload_dataset_to_opik, upload_online_dataset_to_opik
from writing.utils.logging import setup_logging
from writing.utils.opik_utils import configure_opik

OFFLINE_SPLITS = ["dev_evaluator", "test_evaluator"]
ONLINE_SPLITS = ["online_test"]
ALL_SPLITS = OFFLINE_SPLITS + ONLINE_SPLITS


@click.command()
@click.option(
    "--split",
    default="all",
    type=click.Choice(ALL_SPLITS + ["all"]),
    help="Which split to upload (default: all)",
)
def main(split: str) -> None:
    """Upload evaluation dataset to Opik."""

    setup_logging()

    configure_opik()

    splits = ALL_SPLITS if split == "all" else [split]

    for s in splits:
        if s in ONLINE_SPLITS:
            dataset = upload_online_dataset_to_opik(s)
        else:
            dataset = upload_dataset_to_opik(s)
        print(f"Uploaded: {dataset.name} ({len(dataset.get_items())} items)")


if __name__ == "__main__":
    main()
