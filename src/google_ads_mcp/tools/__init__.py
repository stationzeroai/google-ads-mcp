"""Google Ads MCP tools."""

from ..server import mcp
from .health import check_google_ads_connection
from .gaql import preprocess_gaql_query


# Register health check tool
@mcp.tool()
async def check_connection() -> str:
    """Test Google Ads API authentication and return connection status.

    Returns:
        str: JSON string with connection status and accessible customer information
    """
    return await check_google_ads_connection()


# Register GAQL query tools
@mcp.tool()
async def execute_gaql(query: str, customer_id: str) -> str:
    """Execute a Google Ads Query Language (GAQL) query.

    Args:
        query: GAQL query string to execute
        customer_id: Google Ads customer ID (10 digits, with or without dashes)

    Returns:
        str: JSON string containing query results

    Example:
        SELECT campaign.name, metrics.clicks FROM campaign WHERE segments.date DURING LAST_7_DAYS
    """
    from .gaql import _execute_gaql_async
    return await _execute_gaql_async(query, customer_id)


@mcp.tool()
async def preprocess_gaql(query: str) -> str:
    """Validate and optimize a GAQL query for better performance.

    Args:
        query: GAQL query string to preprocess

    Returns:
        str: JSON string with validation results and optimization suggestions
    """
    return preprocess_gaql_query(query)


# Register customer account tools
@mcp.tool()
async def list_customers() -> str:
    """List all accessible Google Ads customer accounts.

    Returns:
        str: JSON string with list of accessible customer accounts and their IDs
    """
    from .customers import _list_accessible_customers_async
    return await _list_accessible_customers_async()


@mcp.tool()
async def get_customer_details(customer_id: str) -> str:
    """Get detailed information about a Google Ads customer account.

    Args:
        customer_id: Google Ads customer ID (10 digits, with or without dashes)

    Returns:
        str: JSON string with customer account details (name, currency, timezone, etc.)
    """
    from .customers import _get_customer_info_async
    return await _get_customer_info_async(customer_id)
