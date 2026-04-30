# Wire Opik observability into both MCP servers

Status: done
Tags: `observability`, `opik`, `tracing`, `decorators`, `gemini`
Depends on: #009, #019
Blocks: #021

## Scope

Hook the Opik observability layer into both servers so every Gemini call, every tool invocation, and every prompt fetch is traced when `OPIK_API_KEY` is set — and silently no-ops when it isn't. The whole feature is **optional and additive**: the system continues to work end-to-end with Opik disabled.

This task introduces:

- `utils/opik_utils.py` (one copy in each package — research and writing).
- The `@opik.track(type="...")` decorator on every registered tool and prompt.
- A `track_genai_client(client)` wrapper applied at the `get_client()` cache boundary.
- A `OpikContext` helper that groups a tool sequence into a single Opik thread.
- A `configure_opik()` boot step in each server.

### Files to create

- `implement_yourself/src/research/utils/opik_utils.py`
- `implement_yourself/src/writing/utils/opik_utils.py`

### Files to modify

- `implement_yourself/src/research/utils/llm.py` and `implement_yourself/src/writing/utils/llm.py` — wrap `get_client()` with `track_genai_client(client)` before returning.
- `implement_yourself/src/research/server.py` and `implement_yourself/src/writing/server.py` — call `configure_opik()` at module import time after `setup_logging` and log a confirmation if it returns `True`.
- `implement_yourself/src/research/routers/tools.py` and `implement_yourself/src/writing/routers/tools.py` — decorate each tool with `@opik.track(type="tool")` and call `opik_context.update_thread_id()` at the top of each tool body so the per-tool trace inherits the current thread ID.
- `implement_yourself/src/research/routers/prompts.py` and `implement_yourself/src/writing/routers/prompts.py` — decorate each prompt with `@opik.track(type="general")` and call `opik_context.initialize_thread_id()` at the top of each prompt body so a fresh thread is started.
- `implement_yourself/.env.example` — make sure `OPIK_API_KEY`, `OPIK_WORKSPACE`, and `OPIK_PROJECT_NAME` are documented.

### `opik_utils.py` interface (identical across both packages, except for default project name)

```python
class OpikContext:
    def __init__(self) -> None: ...                # generates a new uuid4 thread_id
    def initialize_thread_id(self) -> None: ...    # new uuid + register with current trace (only if Opik enabled)
    def update_thread_id(self) -> None: ...        # propagate self.thread_id to current trace

opik_context = OpikContext()                       # module-level singleton

def configure_opik() -> bool: ...                  # True iff Opik configured successfully
def track_genai_client(client: object) -> object:  # returns the Opik-wrapped client or the original
def is_opik_enabled() -> bool:                     # settings.opik_api_key is not None
```

Implementation requirements:

- `is_opik_enabled()` checks `get_settings().opik_api_key is not None` (the field is `SecretStr | None`).
- `configure_opik()` early-returns `False` with a `logger.warning("OPIK_API_KEY is not set. Set it to enable LLMOps with Opik.")` when the key is absent.
- When the key is present:
  - Set `os.environ["OPIK_PROJECT_NAME"] = settings.opik_project_name` (so any uncovered Opik calls inherit the right project).
  - Lazily `import opik` inside the function (so `opik` is not a hard import at module-load time when disabled).
  - Call `opik.configure(api_key=..., workspace=settings.opik_workspace, use_local=False, force=True, automatic_approvals=True)`.
  - Wrap any failure in `try/except Exception` and `logger.warning("Could not configure Opik. Check your OPIK_API_KEY...")` and return `False`. The system MUST keep working.
- `track_genai_client(client)`:
  - If `is_opik_enabled()`, lazily `from opik.integrations.genai import track_genai` and `return track_genai(client, project_name=settings.opik_project_name)`.
  - Otherwise return `client` unchanged.
- `OpikContext.initialize_thread_id`:
  - When enabled: `import opik`, `self.thread_id = str(uuid.uuid4())`, `opik.opik_context.update_current_trace(thread_id=self.thread_id)`. When disabled: no-op.
- `OpikContext.update_thread_id`:
  - When enabled: `import opik`, `opik.opik_context.update_current_trace(thread_id=self.thread_id)`. When disabled: no-op.

### Tool / prompt decoration pattern

`routers/tools.py` example for one tool:

```python
import opik
from research.utils.opik_utils import opik_context

@mcp.tool()
@opik.track(type="tool")
async def deep_research(working_dir: str, query: str) -> dict[str, Any]:
    """..."""
    opik_context.update_thread_id()
    return await deep_research_tool(working_dir, query)
```

`routers/prompts.py` example:

```python
import opik
from research.utils.opik_utils import opik_context

@mcp.prompt()
@opik.track(type="general")
async def research_workflow() -> str:
    """..."""
    opik_context.initialize_thread_id()
    return WORKFLOW_INSTRUCTIONS
```

Decorator order matters: `@mcp.tool()` / `@mcp.prompt()` is the outermost wrapper; `@opik.track(...)` lives between the MCP decorator and the function body.

### Server boot integration

After `setup_logging`, call `configure_opik()`. If it returns `True`, log `Opik monitoring enabled for project: {get_settings().opik_project_name}`. Mirror this in both servers.

### Notes

- DO NOT import `opik` at module top-level inside `opik_utils.py` — keep it lazy. `import opik` inside `configure_opik` and `track_genai_client` and the `OpikContext` methods.
- `@opik.track` itself is a top-level import, but `opik` is already a hard dep in `pyproject.toml`. The lazy imports above are about specific submodules.
- The two `opik_utils.py` copies are intentionally per-package — each reads its own `Settings`. Do not consolidate.
- The `configure_opik()` boot step runs before `mcp = create_mcp_server()` so trace decorators see the configured client.

## Acceptance Criteria

- [ ] With `OPIK_API_KEY` unset, `make test-research-workflow` and `make test-writing-workflow` both succeed end-to-end. Logs show "OPIK_API_KEY is not set..." once per server boot. No Opik traces exist.
- [ ] With `OPIK_API_KEY` set:
  - Logs show "Opik monitoring enabled for project: research-agent" / "...writing-workflow" on boot.
  - After running the test workflows, the Opik dashboard shows traces under those projects.
  - All tool calls within a single workflow run share a `thread_id` (so they group as one conversation).
  - Each Gemini call's input/output is captured.
- [ ] The two `opik_utils.py` files exist and are functionally identical (modulo `import` paths).
- [ ] Tool and prompt decorators use `@opik.track(type="tool")` and `@opik.track(type="general")` respectively.
- [ ] No `import opik` is required at module-load time inside `opik_utils.py` for the disabled path; the system imports cleanly even if the `opik` package is uninstalled (verify by `uv pip uninstall opik` and re-running with the key unset). *(If the implementer prefers to keep `import opik` at the top — matching the parent's style — note that `pyproject.toml` already requires `opik` so it will always be installed; the lazy-import requirement is mainly to keep boot fast and to make the disabled path obvious.)*
- [ ] `make format-check && make lint-check` pass.

## User Stories

### Story: Operator with Opik account

1. Operator pastes a real `OPIK_API_KEY` into `.env`.
2. Reruns `make test-research-workflow`. Logs show "Opik monitoring enabled for project: research-agent".
3. Opens the Opik dashboard; sees a trace tree per tool call, with the same `thread_id` across all calls in the run.
4. Drills into a `deep_research` trace; sees the full Gemini prompt + response.

### Story: Operator without Opik

1. `OPIK_API_KEY` left blank.
2. Both test workflows still pass.
3. Logs show one warning per server boot; no errors, no missing-import crashes.

### Story: Per-workflow thread grouping

1. Operator triggers `/research` then `/write-post` in the same Claude Code session (and same working directory).
2. The research run has its own `thread_id` (initialized by `research_workflow` prompt fetch).
3. The writing run has its own `thread_id` (initialized by `linkedin_post_workflow` prompt fetch).
4. Tools within each run inherit the right thread.

---

Blocked by: #009 and #019 (both servers must be feature-complete before adding observability)
