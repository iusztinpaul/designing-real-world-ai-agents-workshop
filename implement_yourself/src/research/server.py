"""Main MCP server implementation for the Deep Research Agent."""

import logging

from fastmcp import FastMCP

from research.config.settings import get_settings
from research.routers.prompts import register_mcp_prompts
from research.routers.resources import register_mcp_resources
from research.routers.tools import register_mcp_tools
from research.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def create_mcp_server() -> FastMCP:
    """Construct and return the FastMCP server instance.

    Tools, resources, and prompts will be registered here once the
    corresponding router modules are implemented.

    Returns:
        A configured FastMCP server with name and version from settings.
    """
    settings = get_settings()
    mcp = FastMCP(name=settings.server_name, version=settings.version)

    register_mcp_tools(mcp)
    register_mcp_prompts(mcp)
    register_mcp_resources(mcp)

    return mcp


setup_logging(level=get_settings().log_level)

logger.info(
    "%s v%s starting up",
    get_settings().server_name,
    get_settings().version,
)

mcp = create_mcp_server()

if __name__ == "__main__":
    mcp.run()
