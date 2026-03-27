"""Run online LLM judge evaluation — generate posts on the fly and judge them.

This emulates a production evaluation pipeline where posts are generated
by the writing workflow and immediately evaluated by the LLM judge.

Usage:
    uv run python scripts/run_online_evaluation.py [--split SPLIT] [--workers N] [--nb-samples N]
"""

import logging

import click

from writing.evals.evaluation import run_online_evaluation
from writing.utils.opik_utils import configure_opik


@click.command()
@click.option(
    "--split",
    default="test_evaluator",
    type=click.Choice(["dev_evaluator", "test_evaluator"]),
    help="Which split to evaluate (default: test_evaluator)",
)
@click.option(
    "--workers",
    default=1,
    type=int,
    help="Number of parallel threads (default: 1, generation is heavy)",
)
@click.option(
    "--nb-samples",
    default=None,
    type=int,
    help="Limit number of samples (default: all)",
)
def main(split: str, workers: int, nb_samples: int | None) -> None:
    """Run online evaluation: generate posts + judge them."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    configure_opik()
    run_online_evaluation(split=split, workers=workers, nb_samples=nb_samples)


if __name__ == "__main__":
    main()
