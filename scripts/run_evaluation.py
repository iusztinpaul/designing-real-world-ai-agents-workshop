"""Run LLM judge evaluation on a dataset split.

Usage:
    uv run python scripts/run_evaluation.py [--split SPLIT] [--workers N]
"""

import logging

import click

from writing.evals.evaluation import run_evaluation
from writing.utils.opik_utils import configure_opik


@click.command()
@click.option(
    "--split",
    default="dev_evaluator",
    type=click.Choice(["dev_evaluator", "test_evaluator"]),
    help="Which split to evaluate (default: dev_evaluator)",
)
@click.option(
    "--workers",
    default=2,
    type=int,
    help="Number of parallel evaluation threads (default: 2)",
)
@click.option(
    "--nb-samples",
    default=None,
    type=int,
    help="Limit number of samples to evaluate (default: all)",
)
def main(split: str, workers: int, nb_samples: int | None) -> None:
    """Run LLM judge evaluation and report results to Opik."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    configure_opik()
    run_evaluation(split=split, workers=workers, nb_samples=nb_samples)


if __name__ == "__main__":
    main()
