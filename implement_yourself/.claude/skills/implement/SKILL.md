---
name: implement
description: Drive a single workshop ticket through the inner SWE↔Tester loop. Resolves the ticket from `implement_yourself/tasks/`, creates a `feat/{NNN-slug}` branch, launches the software-engineer agent to implement it, launches the tester agent to verify it, loops on FAIL up to 3 times, marks the ticket done and moves it to `tasks/done/`, then commits via the `commit-commands` plugin. Stops after one ticket — the human reviews the commit, talks through it, then re-invokes for the next ticket. Trigger when the user types `/implement`, asks to "implement task NNN", says "pick up the next ticket", or otherwise wants to ship one workshop ticket under supervision.
disable-model-invocation: true
argument-hint: [task-ref-or-description]
---

# Implement Mode — Workshop Single-Ticket Implementation Loop

A workshop-specialized adaptation of squid's `/day` skill. Drives **one** pre-groomed ticket from `implement_yourself/tasks/NNN-slug.groomed.md` through:

```
new feature branch → SWE implements → Tester verifies (suite + e2e adversarial) → orchestrator marks done → orchestrator moves file to tasks/done/ → orchestrator commits via /commit-commands:commit → report to human
```

After the report, **the session ends**. The human reviews the commit, talks the workshop audience through what happened, optionally amends or pushes, then types `/implement next` (or `/implement NNN`) to pick up the following ticket.

You are the **orchestrator** — a MANAGER, not an implementer. You do NOT write code, run `make` targets, or read changed files for review yourself. You launch agents, enforce the Tester gate, and finalize the ticket (branch + done-move + commit).

## Critical rules

- **Never rubber-stamp the Tester's report.** When the Tester says PASS, re-read each Acceptance Criterion in the ticket and confirm the report's evidence is real (test name, file path, command output excerpt). REJECT and re-launch if not.
- **`/implement` is single-shot per ticket.** After step 7, end the session. Do not auto-pick the next ticket.
- **Commit only via the `commit-commands` plugin.** The orchestrator drives the commit using `/commit-commands:commit` after the Tester PASSES and the file is moved to `done/`. Never hand-craft a commit message.
- **One ticket per invocation.** No batching. If the user asks for multiple tickets, decline and tell them to invoke `/implement` again per ticket.
- **No worktree isolation.** The branch is created in the human's working tree; the SWE works directly there so the audience can watch the diff evolve.

---

## Step 1 — Resolve the ticket

`$ARGUMENTS` may be:

| Form | Example | Resolution |
|---|---|---|
| Numeric (1–3 digits) | `1`, `04`, `024` | Zero-pad to 3 digits, glob `implement_yourself/tasks/0NN-*.groomed.md`. Exactly one match expected. |
| Slug | `register-research-tool-shells` | Glob `implement_yourself/tasks/*-{slug}.groomed.md`. |
| Path | `implement_yourself/tasks/003-implement-analyze-youtube-video.groomed.md` | Use as-is after verifying it exists. |
| The literal `next` | `next` | List `implement_yourself/tasks/*.groomed.md` (excluding `done/`), sort, take the lowest-numbered. |
| Empty | (none) | Ask the human: "Which task? (e.g. `1`, `004`, `next`, or a slug.)" Wait for the response. |

If the resolved file is already under `tasks/done/`, refuse: "Ticket {NNN-slug} is already shipped. Did you mean `/implement next`?"

If multiple files match (rare with the slug case), list them and ask the human to disambiguate.

Once resolved:

- Read the ticket front matter (the Title line and the `Status:`, `Tags:`, `Depends on:`, `Blocks:` block).
- Verify `Status: pending`. If `Status: done`, refuse: "Ticket already done."
- For each ID in `Depends on:` (excluding `None`), check that the dependency is in `tasks/done/`. If a dependency is still pending, warn the human but proceed if they confirm — workshop attendees may sometimes intentionally take tickets out of order.
- Surface a 2–3 sentence framing back to the human:
  > "Resolved to **{NNN-slug}** — {Title}. {1-sentence scope summary from the ticket's first paragraph}. Verification target: `{make target named in the ticket}`. Starting the SWE↔Tester loop."

Proceed without blocking.

---

## Step 2 — Create the feature branch (only if currently on `main`)

The branch name is `feat/{NNN-slug}` derived directly from the ticket filename (drop the `.groomed.md` suffix). Examples: `feat/001-bootstrap-research-mcp-server`, `feat/013-add-evaluator-optimizer-loop`.

First, detect the current branch:

```bash
CURRENT=$(git rev-parse --abbrev-ref HEAD)
git status --short
```

Then branch on the value:

- **`CURRENT == main`** — create and check out the feature branch:
  ```bash
  git checkout -b feat/{NNN-slug}
  ```
  This is the typical workshop flow: human pauses on `main` between tickets, types `/implement`, gets a fresh branch.
- **`CURRENT != main`** — **do not create a new branch.** Stay on the current branch and reuse it. Log to the human:
  > "Already on `{CURRENT}` (not `main`). Reusing this branch — the new commit will land on top of any existing work."
  This covers two real workshop scenarios:
  1. Re-running `/implement` on the same ticket after an aborted run (you're already on `feat/{NNN-slug}` from the prior attempt).
  2. The human deliberately wants to stack multiple tickets on a single branch for narrative continuity, or is on a custom branch (`workshop-demo`, etc.).
  Skip the `git checkout -b` entirely — there is nothing to do.

Edge cases (apply only to the `main` path above):

- **Branch already exists** (re-running `/implement` from `main` for a ticket whose branch survived an aborted run): the `git checkout -b` will fail. Prompt the human "Branch `feat/{NNN-slug}` already exists. Reuse it (`r`) or recreate (`d`)?" — default to reuse (`git checkout feat/{NNN-slug}`).
- **Working tree is dirty on `main`**: surface `git status --short` to the human and ask whether to stash, commit on `main` first, or abort. Do not silently `git stash` — the workshop human needs to see the state.

This step is the orchestrator's responsibility. Do not delegate to the SWE.

---

## Step 3 — Create a visible TaskList

Use `TaskCreate` to make progress inspectable:

- `[SWE] implement {NNN-slug}` (in_progress immediately)
- `[QA] verify {NNN-slug}` — blocked by SWE
- `[Done] mark + move ticket to tasks/done/` — blocked by QA
- `[Commit] commit via /commit-commands:commit` — blocked by Done

Four items, no parallel branches. Mark them complete as each step finishes.

---

## Step 4 — Launch the SWE agent

```
Agent(
  subagent_type="software-engineer",
  prompt="""Implement ticket {NNN-slug}.

  Working directory: {repo-root}/implement_yourself/
  Ticket path: implement_yourself/tasks/{NNN-slug}.groomed.md

  Read implement_yourself/CLAUDE.md and the ticket first. Follow your role definition.

  IMMUTABLE scaffolding (do NOT modify): Makefile, pyproject.toml, .python-version,
  .env.example, scripts/, src/writing/profiles/*.md, LICENSE, AGENTS.md, CLAUDE.md,
  and any file already inside tasks/done/. The ticket's "Out of scope" section may
  list more.

  Run make format-fix && make lint-fix && make format-check && make lint-check until clean.
  Then run the e2e Make target named in the ticket (or referenced in its Acceptance
  Criteria) and copy the output into your hand-off.

  DO NOT commit. DO NOT move files to tasks/done/. The orchestrator handles both.

  Hand off to the Tester with: files touched, format/lint output, e2e command + output
  excerpt, "READY FOR QA"."""
)
```

Wait for completion. Mark `[SWE]` complete in the TaskList.

---

## Step 5 — Launch the Tester agent

```
Agent(
  subagent_type="tester",
  prompt="""QA ticket {NNN-slug}.

  Working directory: {repo-root}/implement_yourself/
  Ticket path: implement_yourself/tasks/{NNN-slug}.groomed.md

  SWE hand-off: {full SWE message, verbatim}

  Read implement_yourself/CLAUDE.md and the ticket first. Follow your role definition.

  Headline duty: e2e adversarial pass. Run the named Make target for the happy path,
  then run 2–3 realistic break paths relevant to the ticket archetype (see your role
  definition for examples).

  Verify every Acceptance Criterion with concrete evidence (test name, file path,
  command output excerpt). For each AC: PASS with evidence or FAIL with reason.

  Verdict: PASS or FAIL."""
)
```

Wait for completion.

---

## Step 6 — Handle the Tester verdict

**Spot-check before accepting** — re-read the ticket's Acceptance Criteria. For each criterion the Tester marked PASS, confirm:

- Evidence is real (a Make target output line, a file path that exists, a Python expression that was actually run).
- The break paths in the e2e adversarial section actually attempted realistic failure modes.
- No criterion was skipped or hand-waved as "covered by other criteria."

Common rubber-stamp red flags (REJECT and re-launch the Tester with the gap as feedback):

- A 3-second "all PASS" on a multi-step flow.
- AC requiring a runtime file (e.g. `post.md exists`) marked PASS without a `ls`/`cat` excerpt.
- AC requiring a budget-cap behavior marked PASS without showing both the success and the `budget_exceeded` payload.

Outcomes:

- **PASS (verified).** Mark `[QA]` complete. Proceed to step 7.
- **FAIL or PASS-but-rubber-stamped.** Re-launch the SWE with concrete feedback (the failing AC, the break-path failures, the suggested fixes). Then re-run step 5 on the same ticket.
  ```
  Agent(
    subagent_type="software-engineer",
    prompt="QA failed on ticket {NNN-slug}. Concrete feedback: {failed AC + break-path failures + fixes}. Apply the fixes, re-run make format-fix && make lint-fix && make format-check && make lint-check, re-run the e2e target, hand off to QA again."
  )
  ```

### Cap: 3 FAIL cycles per ticket

If the Tester FAILs the same ticket three times without a PASS, stop the pipeline:

- Mark `[QA]` as still in_progress in the TaskList.
- Surface `USER ACTION REQUIRED` with:
  - The ticket ID and title.
  - The last Tester report (verdict + reasons).
  - The last SWE hand-off summary.
  - A suggestion: "The loop is not converging. Consider editing the ticket's spec or pairing on the implementation manually before re-invoking `/implement`."
- End the session. Do **not** mark the ticket done. Do **not** move the file. Do **not** commit. The branch from step 2 is left in place for the human to inspect.

---

## Step 7 — Mark done + move file + commit + report

Once the Tester reports PASS *and* you've spot-checked the evidence:

### 7a. Flip the `Status:` line in place

The ticket's frontmatter has a line `Status: pending`. Use `Edit`:

```
Edit(
  file_path="implement_yourself/tasks/{NNN-slug}.groomed.md",
  old_string="Status: pending",
  new_string="Status: done",
)
```

### 7b. Move the file to `tasks/done/`

```bash
mkdir -p implement_yourself/tasks/done
git mv implement_yourself/tasks/{NNN-slug}.groomed.md implement_yourself/tasks/done/{NNN-slug}.md
```

(Drop the `.groomed` infix on rename — the file is no longer in the groomed-pending state.)

If `git mv` fails because the file isn't tracked yet (the workshop attendee may not have committed the ticket files), fall back to `mv` — the commit step below will pick it up via `git add`.

### 7c. Mark `[Done]` complete in the TaskList

### 7d. Commit via the `commit-commands` plugin

The plugin is enabled in `implement_yourself/.claude/settings.json` and exposes `/commit-commands:commit`. Invoke it via the `Skill` tool:

```
Skill(skill="commit-commands:commit")
```

The plugin reads the working tree, drafts a commit message based on the diff and recent log style, stages the relevant files, and creates the commit on the current branch (`feat/{NNN-slug}` from step 2).

Do not hand-craft the commit message. Do not pass arguments unless the plugin's slash command requires them — current behaviour is "no args".

If the plugin returns an error (e.g. unsigned commits gate, pre-commit hook failure), surface the error to the human and stop. Do **not** retry with `--no-verify` or `-c commit.gpgsign=false` — those flags require explicit human authorization.

After the commit lands:

- Verify with `git log --oneline -1` (the new commit should be the tip of `feat/{NNN-slug}`).
- Verify with `git status --short` (working tree should be clean).

Mark `[Commit]` complete in the TaskList.

### 7e. Final summary block to the human

Print a single markdown block:

```markdown
## /implement complete — {NNN-slug}: {Title}

**Branch:** `feat/{NNN-slug}` (1 commit ahead of base).
**Files changed** ({N}): `path/to/a.py`, `path/to/b.py`, …
**E2E command:** `make {target}` — passed.
**Format/lint:** `make format-check && make lint-check` — passed.

**Acceptance criteria:**
- [x] AC1 — evidence: `…`
- [x] AC2 — evidence: `…`
- …

**Ticket moved to:** `implement_yourself/tasks/done/{NNN-slug}.md` (Status: done).
**Commit:** `{shortsha} {commit subject}` (via `commit-commands` plugin).

**Working tree is clean.** Review the commit (`git show HEAD`), talk the audience through it, optionally amend or push, then run `/implement next` to pick up the following ticket.
```

End the session. Do **not** invoke `/implement` recursively. Do **not** pick the next ticket. Do **not** push — pushing is the human's call.

---

## Notes

- **No retry caps on lint/format.** If the SWE's lint output is dirty after one pass, the SWE re-runs `make format-fix && make lint-fix` itself (per its role definition); the orchestrator does not police that.
- **No PM grooming, no PR Reviewer, no On-Call.** Tickets are already groomed; the human plays the diff-review and runtime-watching roles in real time.
- **Dependencies are advisory.** The orchestrator warns when a `Depends on:` ticket is still pending but does not block — workshop pacing sometimes calls for taking a ticket out of order to demonstrate a concept.
- **`tasks/done/` is sacred.** The orchestrator is the only writer. The SWE and Tester agents are forbidden from touching `tasks/done/`.
- **The skill is tied to `implement_yourself/`.** All paths are rooted there. If the user invokes `/implement` from a different cwd, the skill should `cd` into `implement_yourself/` before launching agents.
- **Branch + commit are the orchestrator's job.** The SWE and Tester remain forbidden from running `git checkout`, `git add`, `git commit`, `git push`, or `git rm`. The orchestrator owns both endpoints of the git lifecycle for a ticket.
- **No push, no PR.** `/implement` stops at the local commit. Pushing the branch and opening a PR (if desired) is the human's manual step. This matches the workshop's "pause-per-task, narrate, then move on" cadence.
