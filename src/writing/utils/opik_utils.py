"""Opik configuration and tracking utilities."""

import logging
import os
import uuid

from writing.config.settings import get_settings

logger = logging.getLogger(__name__)


class OpikContext:
    """Manages Opik trace thread IDs to group tool calls into a single thread."""

    def __init__(self) -> None:
        self.thread_id = str(uuid.uuid4())

    def initialize_thread_id(self) -> None:
        """Create a new thread_id and register it with Opik.

        Called once at the start of a workflow (e.g., when the MCP prompt is invoked).
        """

        if is_opik_enabled():
            import opik

            self.thread_id = str(uuid.uuid4())
            opik.opik_context.update_current_trace(thread_id=self.thread_id)

    def update_thread_id(self) -> None:
        """Propagate the current thread_id to the active Opik trace.

        Called at the start of each tool to ensure all calls share the same thread.
        """

        if is_opik_enabled():
            import opik

            opik.opik_context.update_current_trace(thread_id=self.thread_id)


opik_context = OpikContext()


def configure_opik() -> bool:
    """Configure Opik monitoring if credentials are available.

    Opik activates when OPIK_API_KEY is set. OPIK_WORKSPACE is optional
    and defaults to the user's default workspace.

    Returns:
        True if Opik was configured, False otherwise.
    """

    settings = get_settings()
    if not is_opik_enabled():
        logger.warning("OPIK_API_KEY is not set. Set it to enable LLMOps with Opik.")
        return False

    os.environ["OPIK_PROJECT_NAME"] = settings.opik_project_name

    try:
        import opik

        opik.configure(
            api_key=settings.opik_api_key.get_secret_value(),
            workspace=settings.opik_workspace,
            use_local=False,
            force=True,
            automatic_approvals=True,
        )

        logger.info("Opik configured successfully!")

        return True
    except Exception:
        logger.warning(
            "Could not configure Opik. Check your OPIK_API_KEY or other OPIK_* "
            "environment variables."
        )
        return False


def track_genai_client(client: object) -> object:
    """Wrap a Gemini client with Opik tracking if configured.

    Args:
        client: The google.genai.Client to track.

    Returns:
        The tracked client if Opik is enabled, otherwise the original client.
    """

    settings = get_settings()
    if is_opik_enabled():
        from opik.integrations.genai import track_genai

        return track_genai(client, project_name=settings.opik_project_name)

    return client


def is_opik_enabled() -> bool:
    """Check if Opik monitoring is enabled."""

    settings = get_settings()

    return settings.opik_api_key is not None
