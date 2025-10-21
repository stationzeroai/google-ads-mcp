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
        str: JSON string containing query results with total_results count and results array

    Date Filtering Examples:
        CORRECT:
            "WHERE segments.date DURING YESTERDAY"  # Use DURING with date keywords
            "WHERE segments.date DURING LAST_7_DAYS"
            "WHERE segments.date = '2025-09-24'"  # Use YYYY-MM-DD for specific dates

        INCORRECT (will be auto-fixed):
            "WHERE segments.date = YESTERDAY"  # Will convert to DURING YESTERDAY
            "WHERE segments.date = TODAY"  # Will convert to DURING TODAY

    Common Date Keywords (use with DURING):
        - YESTERDAY, TODAY
        - LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS
        - LAST_MONTH, THIS_MONTH
        - LAST_WEEK_MON_SUN, THIS_WEEK_MON_TODAY

    Example Query:
        SELECT
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros
        FROM campaign
        WHERE segments.date DURING YESTERDAY
            AND campaign.status = 'ENABLED'
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
