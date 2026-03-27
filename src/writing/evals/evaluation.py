"""Evaluation harness for running LLM judge experiments via Opik."""

import logging
from typing import Any

from opik import evaluation

from writing.evals.dataset import upload_dataset_to_opik, upload_online_dataset_to_opik
from writing.evals.metric import BinaryLLMJudgeMetric

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Offline evaluation (pre-generated posts)
# ---------------------------------------------------------------------------


def _offline_task(sample: dict[str, Any]) -> dict[str, Any]:
    """Map a flat Opik dataset item to the metric's expected inputs.

    The metric expects 'guideline', 'research', and 'output' (generated post).
    """

    return {
        "guideline": sample["guideline"],
        "research": sample.get("research", ""),
        "output": sample["generated_post"],
    }


def run_evaluation(
    split: str = "test_evaluator",
    workers: int = 2,
    nb_samples: int | None = None,
) -> None:
    """Run the LLM judge on pre-generated posts from a dataset split.

    Args:
        split: Dataset split to evaluate ('dev_evaluator' or 'test_evaluator').
        workers: Number of parallel evaluation threads.
        nb_samples: Optional limit on number of samples to evaluate.
    """

    logger.info(f"Running offline evaluation on split '{split}'...")

    dataset = upload_dataset_to_opik(split)
    metric = BinaryLLMJudgeMetric()

    evaluation.evaluate(
        dataset=dataset,
        task=_offline_task,
        scoring_metrics=[metric],
        experiment_config={
            "mode": "offline",
            "split": split,
            "metric": metric.name,
            "model": metric._model,
        },
        task_threads=workers,
        nb_samples=nb_samples,
    )

    logger.info("Offline evaluation complete. Check Opik dashboard for results.")


# ---------------------------------------------------------------------------
# Online evaluation (generate posts on the fly, then judge)
# ---------------------------------------------------------------------------


def _online_task(sample: dict[str, Any]) -> dict[str, Any]:
    """Generate a post on the fly using the shared pipeline, then return it for judging."""

    import asyncio

    from writing.app.generate_post import generate_post

    guideline = sample["guideline"]
    research = sample.get("research", "")

    logger.info(f"Generating post for: {sample.get('slug', 'unknown')}...")
    post = asyncio.run(generate_post(guideline, research))
    generated_post = post.content
    logger.info(f"Generated {len(generated_post)} chars")

    return {
        "guideline": guideline,
        "research": research,
        "output": generated_post,
    }


def run_online_evaluation(
    split: str = "test_evaluator",
    workers: int = 1,
    nb_samples: int | None = None,
) -> None:
    """Generate posts on the fly and judge them with the LLM judge.

    This emulates a production evaluation pipeline:
    1. Upload guideline + research to Opik (no pre-generated post)
    2. For each sample, generate a post using the full writing workflow
    3. Judge the generated post with the BinaryLLMJudgeMetric

    Args:
        split: Dataset split to evaluate.
        workers: Number of parallel threads (default 1 — generation is heavy).
        nb_samples: Optional limit on number of samples.
    """

    logger.info(f"Running online evaluation on split '{split}'...")

    dataset = upload_online_dataset_to_opik(split)
    metric = BinaryLLMJudgeMetric()

    evaluation.evaluate(
        dataset=dataset,
        task=_online_task,
        scoring_metrics=[metric],
        experiment_config={
            "mode": "online",
            "split": split,
            "metric": metric.name,
            "model": metric._model,
        },
        task_threads=workers,
        nb_samples=nb_samples,
    )

    logger.info("Online evaluation complete. Check Opik dashboard for results.")
