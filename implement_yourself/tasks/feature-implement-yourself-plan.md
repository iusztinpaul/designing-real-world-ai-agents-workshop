# Feature Plan: Recreate the Workshop Codebase from a Skeleton

## Summary
Reverse-engineer the workshop's hybrid AI system — a Deep Research Agent and a LinkedIn Writing Workflow served as MCP servers — into 24 ordered, independently-shippable tasks. Each task picks up the immutable scaffolding under `implement_yourself/` (Makefile, pyproject, scripts, profiles, server stubs, empty `__init__.py` files) and adds exactly enough code to advance the system one slice at a time. Running task 24 leaves `implement_yourself/` as a 1:1 functional replica of the parent repository.

The plan is designed to be executed with squid's `/day` skill, one task per invocation. Tasks are written in single-task groomed-spec format (Scope / Acceptance Criteria / User Stories) so the SWE agent can implement them without further grooming.

## Active tracker for this plan: `TRACKER_MODE: file`

Tasks live under `implement_yourself/tasks/NNN-slug.groomed.md`. After implementation, rename to `.in-progress.md` and on completion `git mv` to `tasks/done/NNN-slug.md` per squid convention.

## Tasks (in order)

1. **001** — `bootstrap-research-mcp-server` — Wire the Deep Research FastMCP server boot path: settings, constants, server.py, and register the server in `.mcp.json`. No tools yet.
2. **002** — `register-research-tool-shells` — Register the three research MCP tools (`deep_research`, `analyze_youtube_video`, `compile_research`) as empty shells that return placeholder dicts; depends on #001.
3. **003** — `implement-analyze-youtube-video` — Implement Gemini native video understanding via `FileData(file_uri=…)`, save transcripts under `.memory/transcripts/`, return transcript + path; depends on #002.
4. **004** — `implement-deep-research-with-budget` — Implement Gemini grounded search, persistent `research_results.json`, and the 6-call exploration budget shared across `deep_research` + `analyze_youtube_video`; depends on #003.
5. **005** — `implement-compile-research` — Implement markdown aggregation of grounded results + YouTube transcripts into `research.md`, plus `reset_exploration_budget`; depends on #004.
6. **006** — `add-research-workflow-prompt` — Register the `research_workflow` MCP prompt that teaches the harness how to chain the three tools and self-pace within the budget; depends on #005.
7. **007** — `add-research-config-resource` — Register the `resource://config/research` MCP resource that exposes settings (model names, key presence flags) without leaking secrets; depends on #001.
8. **008** — `add-research-skill` — Add the `.claude/skills/research/SKILL.md` skill that drives the deep research workflow from `outputs/{slug}/`; depends on #006.
9. **009** — `add-research-readme` — Author `src/research/README.md` covering prerequisites, install, env vars, Make targets, MCP usage, and skill usage; depends on #008.
10. **010** — `bootstrap-writing-mcp-server` — Wire the LinkedIn Writer FastMCP server boot path: settings, constants, server.py, and register in `.mcp.json`; depends on #001.
11. **011** — `register-writing-tool-shells` — Register `generate_post`, `edit_post`, `generate_image` as empty shells; depends on #010.
12. **012** — `implement-generate-post-no-loop` — Implement initial post generation reading `guideline.md` + `research.md`, profiles loader, dataset few-shot loader, single Gemini call, save `post.md`; depends on #011.
13. **013** — `add-evaluator-optimizer-loop` — Add the review/edit loop: `review_post`, `edit_post`, `GeneratePostResult`, `num_reviews` iterations, intermediate `post_N.md` + `reviews_N.json` artifacts; depends on #012.
14. **014** — `implement-edit-post-tool` — Implement single-pass review+edit driven by human feedback (highest priority), versioned outputs; depends on #013.
15. **015** — `implement-generate-image-tool` — Implement Gemini Flash Image generation with scene-extraction step, branding/character profile anchoring, and reference images from the dataset; depends on #014.
16. **016** — `add-writing-workflow-prompt` — Register the `linkedin_post_workflow` MCP prompt covering all three tools; depends on #015.
17. **017** — `add-writing-resources` — Register `config://settings` and `profiles://all` MCP resources; depends on #010.
18. **018** — `add-write-post-skill` — Add the `.claude/skills/write-post/SKILL.md` skill; depends on #016.
19. **019** — `add-writing-readme` — Author `src/writing/README.md`; depends on #018.
20. **020** — `wire-opik-monitoring` — Hook Opik observability (configure_opik, OpikContext, track_genai_client, @opik.track decorators) into both servers; depends on #009 and #019.
21. **021** — `implement-binary-llm-judge` — Implement `BinaryLLMJudgeMetric` (Pydantic JudgeResult, profile-aware judge prompt, few-shot from `train_evaluator`), Opik dataset uploader, and `make upload-eval-dataset`; depends on #020.
22. **022** — `implement-judge-alignment-f1` — Add the offline evaluation harness: `run_evaluation`, F1 vs human labels, `make eval-dev` / `make eval-test`; depends on #021.
23. **023** — `implement-online-evaluation` — Add the online evaluation harness: generate posts on the fly, judge them, no F1 for `online_test`; depends on #022.
24. **024** — `add-evals-readme` — Author the evals README; depends on #023.

## Out of scope (intentional)

- **Editing the immutable scaffolding** — Makefile, pyproject.toml, `.python-version`, `.env.example` (env vars beyond the two that already exist may be added if a task explicitly calls for it), LICENSE, scripts under `implement_yourself/scripts/`, and shipped profile markdown files are immutable and used as e2e fixtures. Tasks may *read* them but must not *modify* them.
- **CI / pre-commit hooks** — out of scope for the workshop; only `make format-check && make lint-check` are wired through the Makefile.
- **Authentication, rate limiting, retries beyond what `tenacity` provides** — the workshop targets the happy path and does not harden the system for production traffic.
- **Tests beyond the e2e fixtures already in `implement_yourself/scripts/`** — the workshop validates each task by running the relevant `make test-*` or `make eval-*` target.
- **Datasets folder** — copying or curating `datasets/linkedin_paul_iusztin/` into `implement_yourself/` is out of scope. Tasks #021–#024 assume the dataset is reachable at `<repo-root>/datasets/linkedin_paul_iusztin/` (relative to `implement_yourself/`); the user can symlink or copy the dataset before running those tasks.
- **`AGENTS.md` / `CLAUDE.md` updates inside `implement_yourself/`** — already shipped with the project context and do not need changes.

## How `/day` consumes these tickets

Each `NNN-slug.groomed.md` is already groomed — `/day` accepts `.groomed.md` directly without re-grooming. The SWE agent reads the file, implements per its Scope and Acceptance Criteria, and runs the e2e Make target listed under "How to verify" in each task. The Tester then confirms.

Tasks are sized so each can be implemented and verified in a single `/day` session.

## Documentation updates (this grooming round)

- **Glossary:** no `docs/glossary.md` exists for `implement_yourself/`; tickets use the canonical workshop terminology already established in `implement_yourself/CLAUDE.md` (`MCP server`, `tool`, `resource`, `prompt`, `evaluator-optimizer loop`, `working_dir`, `.memory/`, `research.md`, `guideline.md`, `post.md`, `profile`).
- **ADRs:** none required — every architectural choice is already locked in by the immutable scaffolding (Pydantic + FastMCP + Gemini + Opik + Click + uv + Make).

## Open questions

None. All design decisions are inherited from the parent codebase, which the implementer can read for cross-reference if needed.
