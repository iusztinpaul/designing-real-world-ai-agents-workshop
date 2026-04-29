# Implement the `analyze_youtube_video` tool

Status: done
Tags: `mcp`, `research`, `gemini`, `youtube`, `video-understanding`
Depends on: #002
Blocks: #004, #005

## Scope

Replace the `analyze_youtube_video_tool` shell with a real implementation that hands a public YouTube URL to Gemini via `google.genai.types.FileData(file_uri=url)` and saves the resulting timestamped transcript markdown under `<working_dir>/.memory/transcripts/<video_id>.md`.

This task introduces the **app/ business-logic layer** and the **utils/llm + utils/file_utils** support modules — both will be reused by `deep_research` and `compile_research` in later tasks. Implementer should design these modules to be shared, even though only one tool consumes them in this task.

### Files to create

- `implement_yourself/src/research/app/youtube_handler.py`
- `implement_yourself/src/research/utils/llm.py`
- `implement_yourself/src/research/utils/file_utils.py`

### Files to modify

- `implement_yourself/src/research/config/prompts.py` — add `PROMPT_YOUTUBE_TRANSCRIPTION`.
- `implement_yourself/src/research/tools/analyze_youtube_video_tool.py` — replace the placeholder body with the real flow described below.

### Public interfaces

`utils/llm.py`:

- `@lru_cache` `def get_client() -> google.genai.Client` — instantiates `genai.Client(api_key=settings.google_api_key.get_secret_value())`. **Do not** wrap with Opik yet (task #020).
- `async def call_gemini(prompt: str, model: str | None = None, response_schema: type[BaseModel] | None = None, system_instruction: str | None = None) -> str` — minimal async wrapper around `client.aio.models.generate_content`; honors structured-output by setting `response_mime_type="application/json"` + `response_schema=` when `response_schema` is provided. Returns `response.text`. (For this task you only call it from `youtube_handler` without `response_schema`, but the full signature is intentional so #004 doesn't touch this file again.)

`utils/file_utils.py`:

- `def ensure_memory_dir(working_dir: str) -> Path` — `Path(working_dir) / MEMORY_FOLDER`, `mkdir(parents=True, exist_ok=True)`, returns the path.
- `def validate_directory(working_dir: str) -> Path` — verifies the path exists and is a directory; raises `ValueError` with a helpful message otherwise.
- `def read_file(path: Path) -> str` — returns text or `""` if missing; logs on `IOError`.
- `def write_file(path: Path, content: str) -> None` — creates parent dirs.
- `def load_json(path: Path, default: Any = None) -> Any` — returns parsed JSON or `default` (default itself defaulting to `{}`).
- `def save_json(path: Path, data: Any) -> None` — pretty-prints with `indent=2` and `default=str`.

`app/youtube_handler.py`:

- `async def analyze_youtube_video(url: str, output_path: Path, timestamp: int = 30) -> str` — formats `PROMPT_YOUTUBE_TRANSCRIPTION` with `timestamp`, builds a `types.Content` with two parts (`Part(file_data=FileData(file_uri=url))` then `Part(text=prompt)`), calls `client.aio.models.generate_content(model=settings.youtube_transcription_model, contents=…)`, persists `response.text` to `output_path`. Returns the transcript string. If `response.text` is empty/None, write an error message into `output_path` and return that string. Wrap the call with `time.monotonic()` to log elapsed time.
- `def get_video_id(url: str) -> str | None` — handles `youtube.com/watch?v=…` (use `urllib.parse.parse_qs`) and `youtu.be/…` short URLs. Returns `None` if neither matches.

### Tool flow (`tools/analyze_youtube_video_tool.py`)

1. `validate_directory(working_dir)` — raise on bad input.
2. `memory_path = ensure_memory_dir(working_dir)`.
3. Create the `transcripts/` subfolder: `dest_folder = memory_path / TRANSCRIPTS_FOLDER; dest_folder.mkdir(parents=True, exist_ok=True)`.
4. `video_id = get_video_id(youtube_url)`. If `None`, fall back to a sanitized URL (strip `https://`, replace `/` with `_`) and `logger.warning` about it.
5. `output_path = dest_folder / f"{video_id}.md"`.
6. `transcript = await analyze_youtube_video(url=youtube_url, output_path=output_path)`.
7. Return:
   ```python
   {
     "status": "success",
     "youtube_url": youtube_url,
     "video_id": video_id,
     "transcript": transcript,
     "output_path": str(output_path.resolve()),
     "message": f"Analyzed video: {youtube_url}. "
                f"Transcript saved to {MEMORY_FOLDER}/{TRANSCRIPTS_FOLDER}/{video_id}.md.",
   }
   ```

### `PROMPT_YOUTUBE_TRANSCRIPTION` (template body)

A `{timestamp}` placeholder is substituted in `youtube_handler.analyze_youtube_video`. The prompt instructs Gemini to:

1. Transcribe verbatim.
2. Insert `[MM:SS]` markers every `{timestamp}` seconds.
3. Add brief parenthetical visual descriptions where relevant.
4. Identify multiple speakers as `Speaker 1`, `Speaker 2`, …
5. End each major section with a one-sentence italic summary.
6. Output Markdown.

Implement this by mirroring the parent's `src/research/config/prompts.py:PROMPT_YOUTUBE_TRANSCRIPTION`. Wording does not need to be byte-identical — semantic equivalence is sufficient — but the `{timestamp}` placeholder is mandatory.

### Notes

- `get_client()` reads `settings.google_api_key.get_secret_value()` — `Settings` from #001 already has this field as `SecretStr`.
- Use `asyncio` correctly — the tool wrapper is async, so `await analyze_youtube_video(...)`.
- DO NOT enforce the exploration budget in this task — that lands with `deep_research` in #004 and is retrofitted to this tool there.
- DO NOT track Opik — that's #020.

## Acceptance Criteria

- [ ] `analyze_youtube_video_tool` returns a dict with `status="success"`, a non-empty `transcript`, and an `output_path` pointing to a real file.
- [ ] After invocation, `<working_dir>/.memory/transcripts/<video_id>.md` exists and contains the transcript text.
- [ ] `get_video_id` returns the right ID for both `https://www.youtube.com/watch?v=dQw4w9WgXcQ` and `https://youtu.be/dQw4w9WgXcQ`, and `None` for `https://example.com/`.
- [ ] `validate_directory("/path/that/does/not/exist")` raises `ValueError`.
- [ ] `make test-research-workflow` followed by passing the `--youtube-url` flag manually (e.g. `uv run python scripts/test_research_workflow.py --working-dir test_logic --iterations 1 --youtube-url https://www.youtube.com/watch?v=mYSRn6PC1mc`) produces a transcript in `test_logic/.memory/transcripts/mYSRn6PC1mc.md`. (The default `make` invocation skips the URL — that path remains valid here too.)
- [ ] `deep_research` and `compile_research` still return `not_implemented` (they will be implemented in #004/#005 — do not regress them).
- [ ] `make format-check && make lint-check` pass.

## User Stories

### Story: Attendee transcribes a YouTube talk

1. The attendee runs `mkdir -p test_logic`.
2. They invoke the test script with a public YouTube URL: `uv run python scripts/test_research_workflow.py --working-dir test_logic --iterations 0 --youtube-url https://www.youtube.com/watch?v=mYSRn6PC1mc`.
3. The script connects via stdio, lists 3 tools, calls `analyze_youtube_video`, then `compile_research` (still a shell).
4. The console shows `Status: success`, the transcript path, and the size in bytes.
5. Opening `test_logic/.memory/transcripts/mYSRn6PC1mc.md` reveals a Markdown transcript with `[00:00]`-style timestamps and italicized section summaries.

### Story: Attendee passes a malformed URL

1. The attendee passes `--youtube-url https://example.com/foo`.
2. The tool logs `WARNING - … - Could not extract video ID from URL: https://example.com/foo` and writes the transcript to a sanitized filename (e.g. `example.com_foo.md`).
3. The tool still returns `status="success"` (Gemini may still produce a transcript, or the fallback "Could not generate transcript" message — either is valid).

### Story: Attendee inspects the working directory

1. After running the tool, `ls test_logic/.memory/transcripts/` shows one or more `<video_id>.md` files.
2. `ls test_logic/.memory/` does **not** yet show `research_results.json` (that's #004) or `exploration_state.json` (also #004).

---

Blocked by: #002
