# Implement the BinaryLLMJudgeMetric and Opik dataset upload

Status: pending
Tags: `evals`, `opik`, `llm-judge`, `pydantic`, `dataset`
Depends on: #020
Blocks: #022

## Scope

Implement the LLM-judge half of the evals system: a `BinaryLLMJudgeMetric` that scores a generated post pass/fail against the writing profiles, with few-shot examples drawn from the dataset's `train_evaluator` split. Wire an Opik dataset uploader that pushes both pre-generated (offline) and guideline-only (online) splits to Opik for evaluation.

This task introduces the `writing/evals/` package (currently only `__init__.py` exists in the skeleton) — specifically `dataset.py` and `metric.py`. The harness (`evaluation.py` + scripts) lands in #022.

### Files to create

- `implement_yourself/src/writing/evals/dataset.py`
- `implement_yourself/src/writing/evals/metric.py`

### Files to modify

- `implement_yourself/src/writing/app/dataset_loader.py` — add `load_labeled_samples(label_filter: Label | None = None) -> list[LabeledSample]` and define the `LabeledSample(BaseModel)` model: `slug, ground_truth, generated, label: Label, critique: str`. (The other classes already exist from #012.)
- `implement_yourself/scripts/upload_eval_dataset.py` is **immutable**; this task wires the implementation that the script imports — `upload_dataset_to_opik` and `upload_online_dataset_to_opik` from `writing.evals.dataset`.

### Public interfaces

`writing/evals/dataset.py`:

```python
DATASET_NAME = "linkedin-posts"
DATASET_DESCRIPTION = "LinkedIn posts dataset for LLM judge evaluation"

def upload_dataset_to_opik(split: str) -> opik.Dataset: ...
def upload_online_dataset_to_opik(split: str) -> opik.Dataset: ...
```

`upload_dataset_to_opik`:

1. `entries = load_by_scope(split)`. If empty, raise `ValueError(f"No entries found for split '{split}'")`.
2. For each entry with both `label` and `critique` set, build an item:
   ```python
   {
     "name": entry.slug,
     "slug": entry.slug,
     "guideline": entry.guideline_content(DATASET_DIR),
     "research":  entry.research_content(DATASET_DIR),
     "generated_post": entry.generated_content(DATASET_DIR),
     "label":     entry.label.value,
     "critique":  entry.critique,
   }
   ```
   Skip entries where `generated_post` is empty (with a warning log).
3. Compute `dataset_full_name = f"{DATASET_NAME}-{split}"` (e.g. `linkedin-posts-dev_evaluator`).
4. `client = opik.Opik(); dataset = client.get_or_create_dataset(name=dataset_full_name, description=...)`.
5. `dataset.clear(); dataset.insert(items); return dataset`.

`upload_online_dataset_to_opik`:

- Same shape, but items only carry `name, slug, guideline, research` (and `label` if present). Dataset name suffix is `-online-{split}`.

`writing/evals/metric.py`:

```python
class JudgeResult(BaseModel):
    label: str             # "pass" or "fail"
    critique: str          # 1–3 sentences

class _FewShotExample(BaseModel):
    guideline: str
    generated_post: str
    label: str
    critique: str

class BinaryLLMJudgeMetric(base_metric.BaseMetric):
    def __init__(self, name: str = "binary_llm_judge", model: str | None = None) -> None: ...
    def _build_prompt(self, guideline: str, research: str, generated_post: str) -> str: ...
    def score(self, guideline, research, output, **ignored_kwargs) -> score_result.ScoreResult: ...
    async def ascore(self, guideline, research, output, **ignored_kwargs) -> score_result.ScoreResult: ...
```

Constructor must:

1. Call `super().__init__(name=name)`.
2. `settings = get_settings()`. Set `self._model = model or settings.reviewer_model`.
3. Instantiate a fresh `genai.Client(api_key=settings.google_api_key.get_secret_value())` (the metric does NOT need Opik tracking on this client — Opik captures evaluation traces separately).
4. Load profiles (`load_profiles()`) — store `structure`, `terminology`, `character` content strings.
5. Load few-shot examples from `train_evaluator`:
   - `train_entries = load_by_scope("train_evaluator")`.
   - For each with both `label` and `critique`, build a `_FewShotExample` from `guideline_content(DATASET_DIR)` and `generated_content(DATASET_DIR)` (skip if either is empty).
6. `self._few_shot_section = _build_few_shot_section(few_shot_examples)`.

`_build_few_shot_section`:

- If empty list, return `""`.
- Otherwise, build a heading "**FEW-SHOT EXAMPLES — follow the same labeling logic:**" followed by per-example XML blocks `<example_{i}> <guideline>...</guideline> <generated_post>...</generated_post> <expected_output>label: ... critique: ...</expected_output> </example_{i}>`.

`_build_prompt` formats `JUDGE_PROMPT` with placeholders:

- `{structure_profile}`, `{terminology_profile}`, `{character_profile}` — from the loaded profiles.
- `{few_shot_section}` — from `_build_few_shot_section`.
- `{guideline}`, `{research}` (default `"<none>"` if empty), `{generated_post}`.

`score()` (synchronous):

- Build prompt.
- Call `self._client.models.generate_content(model=self._model, contents=prompt, config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=JudgeResult))`.
- `result = JudgeResult.model_validate_json(response.text)`.
- Return `score_result.ScoreResult(name=self.name, value=1.0 if result.label == Label.PASS else 0.0, reason=f"[{result.label}] {result.critique}")`.

`ascore()` is the awaited variant using `self._client.aio.models.generate_content`.

### `JUDGE_PROMPT` content checklist

Wording does not need to be byte-identical to the parent's prompt. It must:

1. State the judge has **no ground truth** — must judge against guideline + profiles only.
2. Inject the three profiles in `<structure_profile>`, `<terminology_profile>`, `<character_profile>` blocks.
3. State **labeling guidelines**: leave room for creativity; flag `fail` only for major violations (banned AI slop / banned marketing terms; off-topic; structural violations like markdown headers, hashtags, way too long; corporate-salesy tone; wrong POV; passive throughout). Otherwise `pass`.
4. Insert `{few_shot_section}` after the labeling guidelines.
5. Provide the actual case under "**NOW EVALUATE THIS:**" with `<guideline>`, `<research_context>`, `<generated_post>` blocks.
6. Demand output of a JSON object: `label` (`"pass"`/`"fail"`) and `critique` (1–3 sentences). The Pydantic schema enforces this at the API level.

### Notes

- The metric MUST work even if `train_evaluator` produces zero few-shot examples (then `_few_shot_section` is `""`).
- The dataset uploader requires the dataset's `index.yaml` to be present. If your `implement_yourself/` directory does not include `datasets/`, symlink or copy the parent's: `cd implement_yourself && ln -s ../datasets ./datasets`. Document this in the user stories.
- `dataset.clear()` is intentional: every upload replaces the previous content for that split. Implementers should NOT skip it — partial state across runs is harder to debug than a clean reset.

## Acceptance Criteria

- [ ] `make upload-eval-dataset` succeeds with `OPIK_API_KEY` set. The Opik UI shows three datasets: `linkedin-posts-dev_evaluator`, `linkedin-posts-test_evaluator`, `linkedin-posts-online-online_test`.
- [ ] Each item in the offline datasets has the keys `name, slug, guideline, research, generated_post, label, critique`.
- [ ] The online dataset items only carry `name, slug, guideline, research` (and optionally `label`).
- [ ] `BinaryLLMJudgeMetric().score(guideline=..., research=..., output=...)` returns a `ScoreResult` with `value in {0.0, 1.0}` and a non-empty `reason` like `"[pass] critique here..."`.
- [ ] When `train_evaluator` has ≥ 1 labeled entry, the prompt includes a `<example_1>` block.
- [ ] When `train_evaluator` has 0 labeled entries, `_few_shot_section` is `""` and the prompt still validates.
- [ ] `make format-check && make lint-check` pass.

## User Stories

### Story: Attendee uploads the eval datasets

1. Attendee adds `OPIK_API_KEY` to `.env` (and confirms `OPIK_WORKSPACE` / `OPIK_PROJECT_NAME` if needed). Symlinks `datasets/` if running standalone.
2. Runs `make upload-eval-dataset`.
3. Logs report each split's row count. Opik UI now lists three datasets under the configured workspace.

### Story: Judge produces structured output

1. Attendee constructs the metric (`metric = BinaryLLMJudgeMetric()`).
2. Calls `metric.score(guideline="…", research="", output="<a known-bad post full of em-dashes and 'leverage'>")`.
3. Returns `value=0.0`, `reason` cites banned terminology violations.
4. Calls again with a clean post → returns `value=1.0`.

### Story: Few-shot examples shape labels

1. Attendee adds a `train_evaluator` entry with `label: fail` for a post that's borderline.
2. Reconstructs the metric — the new few-shot example shows up in `_few_shot_section`.
3. Subsequent scoring is more aligned with the labeled example's reasoning.

---

Blocked by: #020
