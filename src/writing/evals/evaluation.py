"""Evaluation harness for running LLM judge experiments via Opik."""

import logging
from typing import Any

from opik import evaluation
from opik.evaluation.test_result import TestResult

from writing.evals.dataset import upload_dataset_to_opik, upload_online_dataset_to_opik
from writing.evals.metric import BinaryLLMJudgeMetric

logger = logging.getLogger(__name__)


def _compute_f1(test_results: list[TestResult]) -> float:
    """Compute F1 score between LLM judge predictions and true dataset labels.

    Measures agreement between the LLM judge and expert human annotations.
    "pass" is treated as the positive class.
    """

    true_labels: list[int] = []
    pred_labels: list[int] = []
    for tr in test_results:
        true_label = tr.test_case.dataset_item_content.get("label")
        if true_label is None or not tr.score_results:
            continue
        true_labels.append(1 if true_label == "pass" else 0)
        pred_labels.append(int(tr.score_results[0].value))

    if not true_labels:
        logger.warning("No samples with true labels found — cannot compute F1.")
        return 0.0

    tp = sum(t == 1 and p == 1 for t, p in zip(true_labels, pred_labels))
    fp = sum(t == 0 and p == 1 for t, p in zip(true_labels, pred_labels))
    fn = sum(t == 1 and p == 0 for t, p in zip(true_labels, pred_labels))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    logger.info(
        f"F1={f1:.3f} (precision={precision:.3f}, recall={recall:.3f}) "
        f"over {len(true_labels)} samples"
    )

    return f1


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
) -> float:
    """Run the LLM judge on pre-generated posts from a dataset split.

    Args:
        split: Dataset split to evaluate ('dev_evaluator' or 'test_evaluator').
        workers: Number of parallel evaluation threads.
        nb_samples: Optional limit on number of samples to evaluate.

    Returns:
        F1 score measuring agreement between judge predictions and true labels.
    """

    logger.info(f"Running offline evaluation on split '{split}'...")

    dataset = upload_dataset_to_opik(split)
    metric = BinaryLLMJudgeMetric()

    result = evaluation.evaluate(
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

    f1 = _compute_f1(result.test_results)
    logger.info("Offline evaluation complete. Check Opik dashboard for results.")

    return f1


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
    result = asyncio.run(generate_post(guideline, research))
    generated_post = result.post.content
    logger.info(f"Generated {len(generated_post)} chars")

    return {
        "guideline": guideline,
        "research": research,
        "output": generated_post,
    }


def run_online_evaluation(
    split: str = "online_test",
    workers: int = 1,
    nb_samples: int | None = None,
) -> float | None:
    """Generate posts on the fly and judge them with the LLM judge.

    This emulates a production evaluation pipeline:
    1. Upload guideline + research to Opik (no pre-generated post)
    2. For each sample, generate a post using the full writing workflow
    3. Judge the generated post with the BinaryLLMJudgeMetric

    For the 'online_test' split, F1 is not computed because this simulates
    real-world usage where expert labels are not available.

    Args:
        split: Dataset split to evaluate.
        workers: Number of parallel threads (default 1 — generation is heavy).
        nb_samples: Optional limit on number of samples.

    Returns:
        F1 score if true labels are available, None for online_test.
    """

    logger.info(f"Running online evaluation on split '{split}'...")

    dataset = upload_online_dataset_to_opik(split)
    metric = BinaryLLMJudgeMetric()

    result = evaluation.evaluate(
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

    f1: float | None = None
    if split != "online_test":
        f1 = _compute_f1(result.test_results)
    else:
        logger.info(
            "Skipping F1 computation for online_test — no expert labels available."
        )

    logger.info("Online evaluation complete. Check Opik dashboard for results.")

    return f1
