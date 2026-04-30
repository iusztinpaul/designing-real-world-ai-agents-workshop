"""Offline evaluation harness for LinkedIn post judge alignment."""

import logging
from typing import Any

from opik import evaluation

from writing.evals.dataset import upload_dataset_to_opik
from writing.evals.metric import BinaryLLMJudgeMetric

logger = logging.getLogger(__name__)


def run_evaluation(
    split: str = "test_evaluator",
    workers: int = 2,
    nb_samples: int | None = None,
) -> float:
    """Run the offline LLM judge evaluation and compute the F1 score.

    Uploads the dataset split to Opik (idempotent get_or_create), runs
    BinaryLLMJudgeMetric against every pre-generated post, and computes
    the F1 score between the judge's predictions and the expert labels.

    Args:
        split: Dataset split to evaluate (e.g. 'dev_evaluator', 'test_evaluator').
        workers: Number of parallel evaluation threads.
        nb_samples: Max number of samples to evaluate. None means all.

    Returns:
        The F1 score (float in [0.0, 1.0]).
    """
    # 1. Upload split (idempotent get_or_create) — get fresh dataset content.
    dataset = upload_dataset_to_opik(split)

    # 2. Construct judge metric.
    metric = BinaryLLMJudgeMetric()

    # 3. Define offline task that maps dataset item → metric named args.
    def _offline_task(sample: dict[str, Any]) -> dict[str, Any]:
        return {
            "guideline": sample["guideline"],
            "research": sample.get("research", ""),
            "output": sample["generated_post"],
        }

    # 4. Build experiment_config, run evaluation.
    experiment_config = {
        "mode": "offline",
        "split": split,
        "metric": metric.name,
        "model": metric._model,
    }

    result = evaluation.evaluate(
        dataset=dataset,
        task=_offline_task,
        scoring_metrics=[metric],
        experiment_config=experiment_config,
        task_threads=workers,
        nb_samples=nb_samples,
    )

    # 5. Log the experiment URL if available.
    if result.experiment_url:
        logger.info("Opik experiment URL: %s", result.experiment_url)

    # 6. Compute and log F1.
    f1 = _compute_f1(result.test_results)
    return f1


def _compute_f1(test_results: list) -> float:
    """Compute F1 score between judge predictions and expert labels.

    Uses 'pass' as the positive class. Skips test results with no score
    or no label in the dataset item content.

    Args:
        test_results: List of TestResult objects from Opik evaluation.

    Returns:
        F1 score (float in [0.0, 1.0]).
    """
    true_labels: list[int] = []
    pred_labels: list[int] = []

    for tr in test_results:
        if not tr.score_results:
            continue
        true_label = tr.test_case.dataset_item_content.get("label")
        if true_label is None:
            continue
        pred_score = tr.score_results[0].value
        true_labels.append(1 if true_label == "pass" else 0)
        pred_labels.append(1 if pred_score == 1.0 else 0)

    if not true_labels:
        logger.warning(
            "No labeled samples found in test results — cannot compute F1. "
            "Make sure the dataset split contains items with 'label' fields."
        )
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

    n = len(true_labels)
    logger.info(
        "F1=%.3f (precision=%.3f, recall=%.3f) over %d samples",
        f1,
        precision,
        recall,
        n,
    )

    return f1
