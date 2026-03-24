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


# Register campaign management tools
@mcp.tool()
async def update_campaign_budget(
    customer_id: str,
    budget_resource_name: str,
    amount_micros: int,
) -> str:
    """Update the daily budget amount for a Google Ads campaign budget.

    Args:
        customer_id: Google Ads customer ID (10 digits, with or without dashes)
        budget_resource_name: Full resource name of the budget (format: customers/{id}/campaignBudgets/{id}).
            Use get_campaign_budgets to find this value.
        amount_micros: New daily budget in micros (1 currency unit = 1,000,000 micros, e.g. 50000000 = R$50/day)

    Returns:
        str: JSON with the resource_name of the updated budget
    """
    from .campaigns import _update_campaign_budget_async
    return await _update_campaign_budget_async(customer_id, budget_resource_name, amount_micros)


@mcp.tool()
async def update_campaign_status(
    customer_id: str,
    campaign_resource_name: str,
    status: str,
) -> str:
    """Update the status of a Google Ads campaign (enable or pause).

    Args:
        customer_id: Google Ads customer ID (10 digits, with or without dashes)
        campaign_resource_name: Full resource name of the campaign (format: customers/{id}/campaigns/{id})
        status: New campaign status — must be ENABLED or PAUSED

    Returns:
        str: JSON with the resource_name of the updated campaign
    """
    from .campaigns import _update_campaign_status_async
    return await _update_campaign_status_async(customer_id, campaign_resource_name, status)


@mcp.tool()
async def get_campaign_budgets(
    customer_id: str,
    campaign_ids: list[str] | None = None,
) -> str:
    """Get budget information for enabled Google Ads campaigns.

    Args:
        customer_id: Google Ads customer ID (10 digits, with or without dashes)
        campaign_ids: Optional list of campaign IDs to filter by. If not provided, returns budgets for all enabled campaigns.

    Returns:
        str: JSON with campaign budget details (campaign id, name, budget resource_name, amount_micros)
    """
    from .campaigns import _get_campaign_budgets_async
    return await _get_campaign_budgets_async(customer_id, campaign_ids)
