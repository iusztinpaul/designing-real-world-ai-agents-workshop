# Author the Evals README

Status: pending
Tags: `docs`, `readme`, `evals`, `opik`
Depends on: #023
Blocks: —

## Scope

Author a self-contained README for the evals subsystem. Same constraints as the prior READMEs: prerequisites, install, env vars, run instructions via Make + scripts. **No** marketing or workshop framing.

### File to create

- `implement_yourself/src/writing/evals/README.md`

### Required sections (in order)

1. **`# LinkedIn Writer — Evaluation Harness`** + 1-paragraph summary: what the harness does (uploads dataset splits to Opik, runs `BinaryLLMJudgeMetric`, computes F1 vs human labels for offline splits, generates posts on the fly for online splits).
2. **`## Prerequisites`** — Python ≥ 3.12, `uv`, GNU Make, `OPIK_API_KEY` (mandatory for evals — unlike the rest of the system, where Opik is optional), Google AI Studio API key, the `datasets/linkedin_paul_iusztin/` directory accessible from `implement_yourself/`. Mention: if running `implement_yourself/` standalone, symlink the dataset (`ln -s ../datasets ./datasets` from inside `implement_yourself/`).
3. **`## Installation`** — `uv sync`.
4. **`## Configuration`** —
   - `OPIK_API_KEY` (required for evals).
   - `OPIK_WORKSPACE` (optional).
   - `OPIK_PROJECT_NAME` (optional, defaults to `writing-workflow`; the metric reuses the same project so traces colocate with normal generation traces).
   - `GOOGLE_API_KEY` (required — judge calls Gemini).
5. **`## Concepts`** — short paragraphs:
   - **Dataset splits.** `train_evaluator` (few-shot examples for the judge), `dev_evaluator` (alignment dev set), `test_evaluator` (held-out test set), `online_test` (no labels — emulates production). The split values come from each entry's `scope:` field in `datasets/linkedin_paul_iusztin/index.yaml`.
   - **Offline evaluation.** Reads pre-generated posts from the dataset; the judge scores each; the harness computes F1 against human labels. Used to align the judge.
   - **Online evaluation.** Generates posts on the fly via the writing workflow, then judges them. Emulates production. F1 is computed only when the split has labels (i.e. NOT `online_test`).
   - **F1 alignment.** "F1 between the LLM judge and the human labels" — measures judge agreement. We optimize the judge prompt + few-shot examples until dev F1 plateaus, then validate on the test split.
6. **`## Architecture`** — directory tree of `src/writing/evals/`: `dataset.py`, `metric.py`, `evaluation.py`, `__init__.py`, plus this README.
7. **`## Running the harness`** — Make targets:
   - `make upload-eval-dataset` — pushes all three splits to Opik (`dev_evaluator`, `test_evaluator`, `online_test`).
   - `make eval-dev` — offline F1 on the dev split.
   - `make eval-test` — offline F1 on the test split.
   - `make eval-online` — online evaluation (generate + judge); prints `Online evaluation complete (no F1 — simulating real-world usage).` for `online_test`.
   - Direct script invocations with `--split`, `--workers`, `--nb-samples` for finer control (link to each script).
8. **`## Authoring labeled samples`** — describe how to add an entry to `datasets/linkedin_paul_iusztin/index.yaml` with `label: pass|fail` and a short `critique`. Mention that entries with both `label` and `critique` flow into `train_evaluator` few-shot examples and into the offline test sets.
9. **`## Cost considerations`** — brief: each sample runs at most one judge call for offline; one full writing workflow + one judge call for online. Suggest using `--nb-samples` while iterating to keep cost bounded.
10. **`## Troubleshooting`** — short bullets:
    - "F1=0.000 over 0 samples" → no labeled items match the split filter; check `scope` values.
    - "`upload_dataset_to_opik` raises `ValueError: No entries found for split '…'`" → wrong split name or missing dataset.
    - Online runs are slow → reduce `--nb-samples` or accept that generation is heavy.

### Notes

- DO NOT include marketing or workshop framing.
- Cross-link the writing README (`../README.md`) and the research README (`../../research/README.md`).

## Acceptance Criteria

- [ ] `src/writing/evals/README.md` exists with all 10 sections (or equivalent).
- [ ] Markdown renders cleanly. Cross-links resolve.
- [ ] Every Make target related to evals is listed and explained.
- [ ] Every env var the evals subsystem reads is documented.
- [ ] No marketing language.
- [ ] `make format-check && make lint-check` pass.

## User Stories

### Story: Engineer onboards onto the evals system

1. Engineer reads `src/writing/evals/README.md`.
2. Sets `OPIK_API_KEY` per Configuration.
3. Runs `make upload-eval-dataset`, then `make eval-dev`, then `make eval-test`, then `make eval-online`.
4. The README's troubleshooting bullets resolve any first-run issues.

### Story: Engineer adds a new labeled sample

1. Reads "Authoring labeled samples".
2. Adds an entry to `index.yaml` with `label: fail`, `critique: ...`, and the right `scope`.
3. Reuploads, reruns `make eval-dev`, observes the new sample influences F1.

---

Blocked by: #023
