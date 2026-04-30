# Implement online evaluation (generate-then-judge on live traces)

Status: done
Tags: `evals`, `opik`, `online`, `generate-on-the-fly`
Depends on: #022
Blocks: #024

## Scope

Add the **online** evaluation path: generate a post on the fly using the writing workflow, then score it with `BinaryLLMJudgeMetric`. This emulates a production "evaluate the model end-to-end" pipeline. For the dataset's `online_test` split, F1 is intentionally NOT computed (no expert labels available — the goal is to surface samples for human review). For other splits with labels, F1 is computed identically to #022.

Wire it through `make eval-online` (the immutable `scripts/run_online_evaluation.py` is already present).

### Files to modify

- `implement_yourself/src/writing/evals/evaluation.py` — add `run_online_evaluation(...)` alongside `run_evaluation`.

### Public interface

```python
def run_online_evaluation(
    split: str = "online_test",
    workers: int = 1,
    nb_samples: int | None = None,
) -> float | None: ...
```

Internally:

1. `dataset = upload_online_dataset_to_opik(split)` — uses the variant from #021 that uploads guideline + research only.
2. `metric = BinaryLLMJudgeMetric()`.
3. Define `_online_task(sample: dict[str, Any]) -> dict[str, Any]`:
   ```python
   import asyncio
   from writing.app.generate_post import generate_post

   guideline = sample["guideline"]
   research  = sample.get("research", "")
   logger.info(f"Generating post for: {sample.get('slug', 'unknown')}...")
   result = asyncio.run(generate_post(guideline, research))
   logger.info(f"Generated {len(result.post.content)} chars")
   return {
     "guideline": guideline,
     "research":  research,
     "output":    result.post.content,
   }
   ```
4. Call `evaluation.evaluate(dataset, task=_online_task, scoring_metrics=[metric], experiment_config={"mode": "online", "split": split, "metric": metric.name, "model": metric._model}, task_threads=workers, nb_samples=nb_samples)`.
5. If `split == "online_test"`: log "Skipping F1 computation for online_test — no expert labels available." and return `None`.
6. Otherwise compute F1 via `_compute_f1(result.test_results)` and return it.

### Notes

- `workers=1` by default because generation is heavy (each sample runs the full evaluator-optimizer loop). Increasing it linearly raises Gemini API spend.
- `asyncio.run(generate_post(...))` is deliberately wrapped per-task because Opik's evaluator runs `_online_task` in worker threads, each needing its own event loop.
- The function MUST tolerate splits other than `online_test` — for `dev_evaluator` / `test_evaluator` the dataset is reuploaded as `linkedin-posts-online-{split}` so the items lack `generated_post`; the task generates posts on the fly and F1 is then computable.
- Do NOT short-circuit `online_test` before the `evaluate(...)` call — Opik still records the traces and judge scores; the only thing skipped is F1.

### `scripts/run_online_evaluation.py` (immutable)

Parses `--split` (choices: `dev_evaluator | test_evaluator | online_test`), `--workers`, `--nb-samples`. Calls `setup_logging`, `configure_opik`, then `run_online_evaluation(...)`. Prints `F1 score (judge vs expert labels): {f1:.3f}` if F1 returned, else "Online evaluation complete (no F1 — simulating real-world usage)."

## Acceptance Criteria

- [ ] `make eval-online` runs end-to-end. Logs show per-sample generation, then judge scoring. The Opik UI shows an experiment under `linkedin-posts-online-online_test` with one trace per sample and a `binary_llm_judge` score.
- [ ] For `--split online_test`, the function returns `None` and the script prints "Online evaluation complete (no F1 — simulating real-world usage)."
- [ ] For `--split dev_evaluator` (an invocation pattern the parent supports), the function returns a float and the script prints F1.
- [ ] The online evaluation respects `--nb-samples 1` and processes only one item.
- [ ] Cost is measurable but bounded — the implementer can sanity-check by running `--nb-samples 1` first.
- [ ] `make format-check && make lint-check` pass.

## User Stories

### Story: Attendee runs the online judge

1. Attendee runs `make eval-online`. Opik dashboard now has a new experiment under `linkedin-posts-online-online_test`.
2. Each sample's trace shows the generated post + the judge's `pass`/`fail` + the judge's critique.
3. Console prints "Online evaluation complete (no F1 — simulating real-world usage)."

### Story: Attendee runs online evaluation against a labeled split

1. Attendee runs `uv run python scripts/run_online_evaluation.py --split dev_evaluator --workers 1 --nb-samples 5`.
2. Harness generates 5 posts on the fly, judges each, computes F1 vs the dev labels.
3. Console prints `F1 score (judge vs expert labels): 0.667` (example).

### Story: One-sample sanity test

1. Attendee runs `uv run python scripts/run_online_evaluation.py --split online_test --nb-samples 1`.
2. Harness generates one post and judges it; verifies wiring in ~1 minute.

---

Blocked by: #022
