"""Evaluation harness for running LLM judge experiments via Opik."""

import logging
from typing import Any

from opik import evaluation

from writing.evals.dataset import upload_dataset_to_opik
from writing.evals.metric import BinaryLLMJudgeMetric

logger = logging.getLogger(__name__)


def _evaluation_task(sample: dict[str, Any]) -> dict[str, Any]:
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
    """Run the LLM judge evaluation on a dataset split.

    1. Uploads the dataset split to Opik (flat format)
    2. Creates the BinaryLLMJudgeMetric (profiles loaded from files,
       few-shot examples from train_evaluator)
    3. Runs opik.evaluation.evaluate() to produce an experiment

    Args:
        split: Dataset split to evaluate ('dev_evaluator' or 'test_evaluator').
        workers: Number of parallel evaluation threads.
        nb_samples: Optional limit on number of samples to evaluate.
    """

    logger.info(f"Running evaluation on split '{split}'...")

    dataset = upload_dataset_to_opik(split)

    metric = BinaryLLMJudgeMetric()

    experiment_config = {
        "split": split,
        "metric": metric.name,
        "model": metric._model,
    }

    evaluation.evaluate(
        dataset=dataset,
        task=_evaluation_task,
        scoring_metrics=[metric],
        experiment_config=experiment_config,
        task_threads=workers,
        nb_samples=nb_samples,
    )

    logger.info("Evaluation complete. Check Opik dashboard for results.")
