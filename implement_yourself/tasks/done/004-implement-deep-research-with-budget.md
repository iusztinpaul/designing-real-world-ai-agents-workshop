# Implement the `deep_research` tool with a shared exploration budget

Status: done
Tags: `mcp`, `research`, `gemini`, `grounded-search`, `pydantic`, `budget`
Depends on: #003
Blocks: #005

## Scope

Implement Gemini grounded search end-to-end and add a hard call-budget cap that protects both `deep_research` and `analyze_youtube_video` from runaway agent loops. After this task, the agent can only run a combined **6 exploration calls** before being forced to call `compile_research` (which lands in #005).

This task introduces the **`models/schemas.py`** Pydantic models for grounded research results, the **`app/research_handler.py`** business logic, the **`app/exploration_budget.py`** budget tracker, the **grounded-search variant of the Gemini client**, and the **`PROMPT_RESEARCH`** template.

### Files to create

- `implement_yourself/src/research/app/research_handler.py`
- `implement_yourself/src/research/app/exploration_budget.py`
- `implement_yourself/src/research/models/schemas.py`

### Files to modify

- `implement_yourself/src/research/config/constants.py` — add `EXPLORATION_STATE_FILE = "exploration_state.json"` and `MAX_EXPLORATION_CALLS = 6`. Add a comment explaining why the cap is on **total calls** (not rounds): per-call latency overlaps with the gap between LLM turns, so detecting "rounds" from server-side timing is unreliable; 6 ≈ "3 rounds × 2 queries" — enough breadth without runaway. Wording can paraphrase but must convey the rationale.
- `implement_yourself/src/research/config/prompts.py` — add `PROMPT_RESEARCH` (a `{query}` template that asks for a detailed, well-sourced answer with citations).
- `implement_yourself/src/research/utils/llm.py` — add `call_gemini_search` and `extract_grounding_sources` (see Public interfaces below).
- `implement_yourself/src/research/tools/deep_research_tool.py` — replace the placeholder body with the real flow.
- `implement_yourself/src/research/tools/analyze_youtube_video_tool.py` — **retrofit** budget enforcement. Body now: `validate_directory → ensure_memory_dir → record_exploration_call(...) → … → existing flow`, and append `call`, `max_calls`, `calls_remaining` to the returned dict and the `message` string.

### Public interfaces

`models/schemas.py`:

```python
class ResearchSource(BaseModel):
    url: str
    title: str = ""
    snippet: str = ""

class ResearchResult(BaseModel):
    query: str
    answer: str
    sources: list[ResearchSource] = Field(default_factory=list)
```

`app/research_handler.py`:

```python
async def run_grounded_search(query: str) -> ResearchResult: ...
```

The function formats `PROMPT_RESEARCH.format(query=query)`, calls `call_gemini_search(prompt)`, converts each raw `{url, title}` dict into a `ResearchSource(snippet="")`, and returns `ResearchResult(query, answer_text, sources)`.

`utils/llm.py` additions:

- `async def call_gemini_search(prompt: str, model: str | None = None) -> tuple[str, list[dict[str, str]]]` — sets `config = types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])`. Returns `(response.text or "", extract_grounding_sources(response))`. (Grounding and `response_schema` are mutually exclusive — never use both.)
- `def extract_grounding_sources(response) -> list[dict[str, str]]` — walks `response.candidates[0].grounding_metadata.grounding_chunks[*].web.{uri,title}` defensively (each layer may be `None`); deduplicates by URL; returns `[{"url": ..., "title": ...}, ...]`.

`app/exploration_budget.py`:

```python
class BudgetExceededError(Exception):
    used_calls: int
    max_calls: int
    # __str__: helpful message naming compile_research as the next step

def record_exploration_call(
    memory_path: Path,
    tool: str,
    query: str,
    *,
    max_calls: int = MAX_EXPLORATION_CALLS,
) -> tuple[int, int]:
    """Append an entry to .memory/exploration_state.json; raise BudgetExceededError if the cap is met."""

def reset_exploration_budget(memory_path: Path) -> None:
    """Delete .memory/exploration_state.json (used by compile_research in #005)."""
```

State file shape: `{"calls": [{"tool": str, "query": str, "at": float}, ...]}`. Use `time.time()` for `at`. Re-use `load_json`/`save_json` from `utils/file_utils.py`.

### `deep_research_tool` body

1. `validate_directory(working_dir)`; `memory_path = ensure_memory_dir(working_dir)`.
2. Try `record_exploration_call(memory_path, tool="deep_research", query=query)`. On `BudgetExceededError`, return:
   ```python
   {
     "status": "budget_exceeded",
     "query": query,
     "used_calls": exc.used_calls,
     "max_calls": exc.max_calls,
     "message": str(exc),
   }
   ```
3. `results_path = memory_path / RESEARCH_RESULTS_FILE`.
4. `existing = load_json(results_path, default=[])`.
5. `result = await run_grounded_search(query)`.
6. `existing.append(result.model_dump()); save_json(results_path, existing)`.
7. Return:
   ```python
   {
     "status": "success",
     "query": query,
     "answer": result.answer,
     "sources": [src.model_dump() for src in result.sources],
     "total_sources": len(result.sources),
     "output_path": str(results_path.resolve()),
     "call": call_index,
     "max_calls": MAX_EXPLORATION_CALLS,
     "calls_remaining": calls_remaining,
     "message": f"Researched: '{query}'. Found {len(result.sources)} sources. "
                f"Results saved to {MEMORY_FOLDER}/{RESEARCH_RESULTS_FILE}. "
                f"Call {call_index}/{MAX_EXPLORATION_CALLS} ({calls_remaining} remaining "
                f"before compile_research is required).",
   }
   ```

### Retrofit `analyze_youtube_video_tool`

Insert the same `record_exploration_call(..., tool="analyze_youtube_video", query=youtube_url)` step immediately after `ensure_memory_dir`. On `BudgetExceededError`, return a `status="budget_exceeded"` dict (mirroring `deep_research_tool`). On success, append `call`, `max_calls`, `calls_remaining` to both the returned dict and the `message` string.

### Notes

- The budget is shared. Six calls combined — not six per tool.
- If `deep_research` is invoked seven times in a row, the seventh should not write a 7th entry to the state file; `record_exploration_call` checks `len(calls) >= max_calls` BEFORE appending.
- `BudgetExceededError.__str__` should include the words `compile_research` so the agent knows what to do next.
- The grounded-search response often returns nothing in `candidates[0].grounding_metadata` for trivial queries; `extract_grounding_sources` must return `[]` rather than crash.
- DO NOT touch `compile_research_tool.py` here — that's #005 — but be aware its eventual job is to call `reset_exploration_budget(memory_path)`.

## Acceptance Criteria

- [ ] `Settings` and `constants.py` expose `MAX_EXPLORATION_CALLS = 6`.
- [ ] After 6 successful exploration calls (any combination of `deep_research` / `analyze_youtube_video`), the 7th returns `status="budget_exceeded"` and does NOT increment the state file.
- [ ] `deep_research` writes `.memory/research_results.json` containing a list whose last item has keys `query`, `answer`, `sources`. Sources contain `url` and `title`.
- [ ] `extract_grounding_sources` deduplicates by URL.
- [ ] `make test-research-workflow` succeeds with `--iterations 2`: two `deep_research` calls, both `status="success"`, with `calls_remaining` 4 then 3 in the return payloads.
- [ ] `analyze_youtube_video` still works as in #003 *and* now reports budget metadata in its response.
- [ ] Calling `compile_research` still returns `status="not_implemented"` (it lands in #005).
- [ ] `make format-check && make lint-check` pass.

## User Stories

### Story: Two grounded queries, then a budget guard

1. Attendee runs `make test-research-workflow` (default `--iterations 2`).
2. The script makes two `deep_research` calls. Each returns `status="success"` with non-empty `answer`, ≥1 source, `call`/`max_calls`/`calls_remaining` populated.
3. `test_logic/.memory/research_results.json` now has a JSON array with two objects.
4. The attendee then re-runs the same script four more times in the same `test_logic/` (or once with a higher `--iterations`) and observes the 7th call returning `budget_exceeded`.

### Story: Mixed deep_research + youtube hits the same budget

1. Attendee invokes 5 `deep_research` calls (state file has 5 entries).
2. Attendee then runs `analyze_youtube_video` on a YouTube URL — succeeds, state has 6 entries, `calls_remaining=0`.
3. Attendee tries one more `deep_research` — gets `budget_exceeded` and the message "...Call `compile_research` now to finalize research.md from the results collected so far."

### Story: Validation still kicks in

1. Attendee invokes `deep_research` with `working_dir="/this/path/does/not/exist"`.
2. The tool raises `ValueError` (which FastMCP surfaces to the harness as a tool error).
3. The state file is not created.

---

Blocked by: #003
