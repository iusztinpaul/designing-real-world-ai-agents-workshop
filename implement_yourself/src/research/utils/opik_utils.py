"""Opik observability utilities for the Deep Research MCP server."""

import logging
import os
import uuid

from research.config.settings import get_settings

logger = logging.getLogger(__name__)


def is_opik_enabled() -> bool:
    """Return True iff OPIK_API_KEY is configured.

    Returns:
        True if the Opik API key is set in settings, False otherwise.
    """
    return get_settings().opik_api_key is not None


def configure_opik() -> bool:
    """Configure Opik observability.

    Early-returns False with a warning when OPIK_API_KEY is not set.
    When the key is present, sets the project name env var, then calls
    opik.configure(). Any failure is caught and logged — the system must
    keep working even if Opik fails to initialise.

    Returns:
        True if Opik was configured successfully, False otherwise.
    """
    settings = get_settings()

    if not is_opik_enabled():
        logger.warning("OPIK_API_KEY is not set. Set it to enable LLMOps with Opik.")
        return False

    try:
        os.environ["OPIK_PROJECT_NAME"] = settings.opik_project_name

        import opik  # noqa: PLC0415

        opik.configure(
            api_key=settings.opik_api_key.get_secret_value(),
            workspace=settings.opik_workspace,
            use_local=False,
            force=True,
            automatic_approvals=True,
        )
        return True
    except Exception as exc:
        logger.warning(
            "Could not configure Opik. Check your OPIK_API_KEY. Error: %s", exc
        )
        return False


def track_genai_client(client: object) -> object:
    """Wrap a Gemini client with Opik tracking if Opik is enabled.

    Args:
        client: A google.genai.Client instance.

    Returns:
        The Opik-wrapped client when enabled, or the original client unchanged.
    """
    if not is_opik_enabled():
        return client

    settings = get_settings()

    from opik.integrations.genai import track_genai  # noqa: PLC0415

    return track_genai(client, project_name=settings.opik_project_name)


class OpikContext:
    """Groups tool calls within a single workflow run under one Opik thread."""

    def __init__(self) -> None:
        self.thread_id: str = str(uuid.uuid4())

    def initialize_thread_id(self) -> None:
        """Generate a new thread ID and register it with the current Opik trace.

        No-op when Opik is disabled.
        """
        if not is_opik_enabled():
            return

        import opik  # noqa: PLC0415

        self.thread_id = str(uuid.uuid4())
        opik.opik_context.update_current_trace(thread_id=self.thread_id)

    def update_thread_id(self) -> None:
        """Propagate the current thread ID to the current Opik trace.

        No-op when Opik is disabled.
        """
        if not is_opik_enabled():
            return

        import opik  # noqa: PLC0415

        opik.opik_context.update_current_trace(thread_id=self.thread_id)


opik_context = OpikContext()
