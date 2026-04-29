# Register the `resource://config/research` MCP resource

Status: done
Tags: `mcp`, `research`, `resources`, `routers`, `config`
Depends on: #001
Blocks: #009

## Scope

Add the MCP-resource registration layer to the Deep Research server. Expose the running configuration so a harness or human can introspect which Gemini models are wired in and whether external integrations are enabled — without ever leaking secret values.

### Files to create

- `implement_yourself/src/research/routers/resources.py`

### Files to modify

- `implement_yourself/src/research/server.py` — wire `register_mcp_resources(mcp)` into `create_mcp_server()`.

### Public interface

```python
def register_mcp_resources(mcp: FastMCP) -> None:
    @mcp.resource("resource://config/research")
    async def get_research_config() -> dict[str, Any]:
        """Get the current research agent configuration."""
        settings = get_settings()
        return {
            "server_name": settings.server_name,
            "version": settings.version,
            "gemini_model": settings.gemini_model,
            "youtube_transcription_model": settings.youtube_transcription_model,
            "has_google_api_key": settings.google_api_key is not None,
            "has_opik_api_key": settings.opik_api_key is not None,
            "opik_workspace": settings.opik_workspace,
            "opik_project_name": settings.opik_project_name,
        }
```

### Notes

- **Never expose `SecretStr` values.** Only return a boolean (`has_*_api_key`) for keys, and the plain workspace/project-name strings for the non-secret Opik fields.
- The resource URI must be exactly `resource://config/research` — the README and any future tutorial reference this URI.
- The resource is read-only by definition; no side effects.

## Acceptance Criteria

- [ ] `mcp.list_resources()` includes `resource://config/research`.
- [ ] Reading the resource returns a dict with the exact keys above and no `*api_key*` field that contains a real key value.
- [ ] `gemini_model` and `youtube_transcription_model` reflect the values configured in `Settings`.
- [ ] If `OPIK_API_KEY` is unset, `has_opik_api_key` is `False`. If it is set (any non-empty string), the field is `True`.
- [ ] `make format-check && make lint-check` pass.

## User Stories

### Story: Operator inspects the running config

1. Operator boots the server with `make run-research-server`.
2. From an MCP client (FastMCP inspector, Claude Code resource picker), they read `resource://config/research`.
3. The response shows `server_name`, `version`, both model names, and three booleans/strings about Opik.
4. None of the API keys are visible.

### Story: Harness gates a feature on Opik availability

1. A harness reads the resource and sees `has_opik_api_key: false`.
2. The harness skips opening an Opik dashboard link in its UI.

---

Blocked by: #001
