"""FastMCP server instance.

This module holds the MCP server instance to avoid circular imports between
__main__.py and tools modules.
"""

from fastmcp import FastMCP

mcp = FastMCP("Google Ads MCP Server")
