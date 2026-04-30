# Implement the offline evaluation harness with F1 alignment

Status: done
Tags: `evals`, `opik`, `f1`, `alignment`, `harness`
Depends on: #021
Blocks: #023

## Scope

Implement the offline evaluation harness — a function that runs `BinaryLLMJudgeMetric` against the pre-generated posts in a dataset split and computes the F1 score between the judge's predictions and the human expert labels. Wire it through `make eval-dev` and `make eval-test` (the immutable `scripts/run_evaluation.py` is already present in `implement_yourself/scripts/` and only requires the imports to resolve).

This task introduces `writing/evals/evaluation.py`. The metric and dataset layer (#021) are already in place.

### Files to create

- `implement_yourself/src/writing/evals/evaluation.py`

### Public interface

```python
def run_evaluation(
    split: str = "test_evaluator",
    workers: int = 2,
    nb_samples: int | None = None,
) -> float: ...
```

Internally:

1. `dataset = upload_dataset_to_opik(split)` — guarantees the split exists in Opik with the latest content.
2. `metric = BinaryLLMJudgeMetric()`.
3. Define `_offline_task(sample: dict[str, Any]) -> dict[str, Any]`:
   ```python
   return {
     "guideline": sample["guideline"],
     "research":  sample.get("research", ""),
     "output":    sample["generated_post"],
   }
   ```
   Opik's `evaluate(...)` calls this on each dataset item; the returned dict feeds `metric.score(...)`'s named args via Opik's contract.
4. Call `result = evaluation.evaluate(dataset=dataset, task=_offline_task, scoring_metrics=[metric], experiment_config=…, task_threads=workers, nb_samples=nb_samples)` — `experiment_config` carries `mode="offline"`, `split`, `metric=metric.name`, `model=metric._model`.
5. Compute F1 via `_compute_f1(result.test_results)`. Log it. Return it.

### `_compute_f1(test_results: list[TestResult]) -> float`

For each `TestResult`:

- `true_label = tr.test_case.dataset_item_content.get("label")`.
- `pred_score = tr.score_results[0].value` (the only scoring metric; `1.0`/`0.0`).
- If `true_label is None` or `not tr.score_results`, skip.
- Append integers to `true_labels` and `pred_labels` lists (`pass` → 1, anything else → 0).

If no labeled samples were collected, log a warning and return `0.0`.

Otherwise compute:

- `tp = sum(t==1 and p==1 …)`.
- `fp = sum(t==0 and p==1 …)`.
- `fn = sum(t==1 and p==0 …)`.
- `precision = tp / (tp + fp)` (or `0.0` if denominator is zero).
- `recall = tp / (tp + fn)` (or `0.0`).
- `f1 = 2 * precision * recall / (precision + recall)` (or `0.0`).
- Log a one-liner: `F1=0.812 (precision=…, recall=…) over N samples`.

### Notes

- `pass` is the positive class by convention.
- `nb_samples=None` evaluates the whole split; provide an integer to cap.
- `task_threads` is plumbed straight to Opik's evaluator. Default to 2 to match the parent.
- The metric's `score` is synchronous; Opik's `evaluate(...)` calls it in worker threads.

### `scripts/run_evaluation.py` (already present, immutable)

The shipped script:

- Parses `--split {dev_evaluator|test_evaluator}`, `--workers`, `--nb-samples`.
- Calls `setup_logging`, `configure_opik`, then `run_evaluation(...)`.
- Prints `F1 score (judge vs expert labels): {f1:.3f}`.

This task only needs the import path `from writing.evals.evaluation import run_evaluation` to resolve.

## Acceptance Criteria

- [ ] `make eval-dev` runs end-to-end with `OPIK_API_KEY` set; prints `F1 score (judge vs expert labels): 0.xxx` and reports the corresponding Opik experiment URL in logs.
- [ ] `make eval-test` runs against the test split, same shape.
- [ ] If a labeled split has zero usable items, the harness logs a warning and the script exits with `F1=0.000` rather than crashing.
- [ ] The metric's `experiment_config` is passed through to the Opik experiment metadata (visible in the Opik UI).
- [ ] `make format-check && make lint-check` pass.

## User Stories

### Story: Attendee runs alignment on the dev split

1. Attendee runs `make upload-eval-dataset` (from #021), then `make eval-dev`.
2. Logs show evaluation progress per item.
3. Final line: `F1 score (judge vs expert labels): 0.812` (or whatever number).
4. The Opik UI shows the experiment with each item's score, reason, and the dataset content.

### Story: Iterate on the metric

1. Attendee tweaks `JUDGE_PROMPT` or the few-shot section in #021's metric.
2. Reruns `make eval-dev` to compare F1 across runs.
3. Once dev F1 is acceptable, runs `make eval-test` on the held-out split for a final check.

### Story: Quick sanity check

1. Attendee runs `uv run python scripts/run_evaluation.py --split dev_evaluator --nb-samples 3`.
2. The harness evaluates only the first 3 dataset items and prints F1 over those (likely 0.0 or 1.0 with such a tiny set — that's expected; the goal is to verify wiring).

---

Blocked by: #021
