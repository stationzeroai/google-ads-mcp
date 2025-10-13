"""Google Ads MCP tools."""

from ..__main__ import mcp
from .health import check_google_ads_connection


# Register health check tool
@mcp.tool()
def check_connection() -> str:
    """Test Google Ads API authentication and return connection status.

    Returns:
        str: JSON string with connection status and accessible customer information
    """
    return check_google_ads_connection()
