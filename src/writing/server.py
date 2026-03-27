"""Main MCP server implementation for the LinkedIn Writer."""

import logging

from fastmcp import FastMCP

from writing.config.settings import get_settings
from writing.routers.prompts import register_mcp_prompts
from writing.routers.resources import register_mcp_resources
from writing.routers.tools import register_mcp_tools

logger = logging.getLogger(__name__)


def configure_opik() -> bool:
    """Configure Opik monitoring if credentials are available.

    Returns:
        True if Opik was configured, False otherwise.
    """

    settings = get_settings()
    if settings.opik_api_key is None or settings.opik_workspace is None:
        return False

    try:
        import opik

        opik.configure(
            api_key=settings.opik_api_key.get_secret_value(),
            workspace=settings.opik_workspace,
            use_local=False,
            force=True,
        )

        return True
    except Exception:
        logger.warning(
            "Could not configure Opik. Check your OPIK_* environment variables."
        )
        return False


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server instance.

    Returns:
        FastMCP: Configured MCP server instance.
    """

    settings = get_settings()

    mcp = FastMCP(
        name=settings.server_name,
        version=settings.version,
    )

    register_mcp_tools(mcp)
    register_mcp_resources(mcp)
    register_mcp_prompts(mcp)

    return mcp


# Configure logging
logging.basicConfig(
    level=get_settings().log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Configure Opik if available
if configure_opik():
    logger.info(
        f"Opik monitoring enabled for project: {get_settings().opik_project_name}"
    )

# Create the server instance (used by `fastmcp run`)
mcp = create_mcp_server()

if __name__ == "__main__":
    mcp.run()
