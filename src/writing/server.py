"""Main MCP server implementation for the LinkedIn Writer."""

import logging

from fastmcp import FastMCP

from writing.config.settings import get_settings
from writing.routers.prompts import register_mcp_prompts
from writing.routers.resources import register_mcp_resources
from writing.routers.tools import register_mcp_tools
from writing.utils.logging import setup_logging
from writing.utils.opik_utils import configure_opik

logger = logging.getLogger(__name__)


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
setup_logging(level=get_settings().log_level)

# Configure Opik if available
if configure_opik():
    logger.info(
        f"Opik monitoring enabled for project: {get_settings().opik_project_name}"
    )

# Create the server instance (used by `fastmcp run`)
mcp = create_mcp_server()

if __name__ == "__main__":
    mcp.run()
