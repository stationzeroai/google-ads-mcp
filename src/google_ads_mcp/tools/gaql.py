"""Google Ads Query Language (GAQL) tools."""

import asyncio
import json
import logging
import re
from typing import Dict, List, Any

from google.ads.googleads.errors import GoogleAdsException


logger = logging.getLogger(__name__)


def detect_and_fix_date_formats(query: str) -> tuple[str, list]:
    """Detect and fix common date format errors in GAQL queries."""
    fixes_applied = []
    fixed_query = query

    # Pattern: segments.date = YESTERDAY|TODAY|LAST_*
    pattern = r'segments\.date\s*=\s*(YESTERDAY|TODAY|LAST_\w+_?\w*)'
    matches = re.findall(pattern, fixed_query, re.IGNORECASE)

    for match in matches:
        old_pattern = f'segments.date = {match}'
        new_pattern = f'segments.date DURING {match}'
        fixed_query = fixed_query.replace(old_pattern, new_pattern)
        fixes_applied.append({
            "type": "auto_fix",
            "message": f"Converted '{old_pattern}' to '{new_pattern}'",
            "reason": "Date equality with keywords requires DURING operator"
        })

    return fixed_query, fixes_applied


def parse_select_fields(query: str) -> dict:
    """Parse GAQL query to extract requested fields.

    Args:
        query: GAQL query string

    Returns:
        dict like: {'campaign': ['id', 'name'], 'metrics': ['clicks', 'impressions']}
    """
    # Extract SELECT clause
    select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
    if not select_match:
        return {}

    # Parse fields like "campaign.id, campaign.name, metrics.clicks"
    select_clause = select_match.group(1)
    fields = [field.strip() for field in select_clause.split(',')]

    # Group by entity (campaign, metrics, segments, etc.)
    entities = {}
    for field in fields:
        if '.' in field:
            parts = field.split('.', 1)  # Split only on first dot
            entity = parts[0]
            attribute = parts[1]
            if entity not in entities:
                entities[entity] = []
            entities[entity].append(attribute)

    return entities


def _convert_protobuf_value(value):
    """Convert protobuf value to a JSON-serializable format."""
    if hasattr(value, '__dict__'):
        # It's a protobuf message, convert to dict
        result = {}
        for field in value.DESCRIPTOR.fields:
            field_name = field.name
            if hasattr(value, field_name):
                field_value = getattr(value, field_name)
                if field_value is not None:
                    if hasattr(field_value, '__iter__') and not isinstance(field_value, (str, bytes)):
                        # It's a repeated field
                        result[field_name] = [_convert_protobuf_value(item) for item in field_value]
                    else:
                        result[field_name] = _convert_protobuf_value(field_value)
        return result
    elif isinstance(value, (int, float, str, bool)):
        return value
    elif hasattr(value, 'name'):
        # It's an enum, return the name
        return value.name
    else:
        # Return string representation as fallback
        return str(value)


async def _execute_gaql_async(query: str, customer_id: str) -> str:
    """Execute a GAQL query asynchronously."""
    from ..__main__ import get_client
    from ..auth import format_customer_id, validate_gaql_query

    try:
        # Validate inputs
        if not validate_gaql_query(query):
            return json.dumps({
                "error": "Invalid GAQL query format",
                "query": query
            }, indent=2)

        # Auto-fix common date format errors
        fixed_query, fixes = detect_and_fix_date_formats(query)
        query = fixed_query

        if not customer_id:
            return json.dumps({
                "error": "customer_id is required"
            }, indent=2)

        # Format customer ID
        formatted_customer_id = format_customer_id(customer_id)

        # Get authenticated client
        client = get_client()
        google_ads_service = client.get_service("GoogleAdsService")

        # Execute the query
        search_request = client.get_type("SearchGoogleAdsRequest")
        search_request.customer_id = formatted_customer_id
        search_request.query = query

        results = []
        response = await asyncio.to_thread(google_ads_service.search, request=search_request)

        # Parse the query to get only requested fields
        requested_entities = parse_select_fields(query)

        for row in response:
            result_dict = {}

            # Only extract the specifically requested fields
            for entity_name, field_names in requested_entities.items():
                if hasattr(row, entity_name):
                    entity = getattr(row, entity_name)
                    entity_dict = {}
                    for field_name in field_names:
                        if hasattr(entity, field_name):
                            value = getattr(entity, field_name)
                            entity_dict[field_name] = _convert_protobuf_value(value)
                        else:
                            entity_dict[field_name] = None
                    result_dict[entity_name] = entity_dict

            results.append(result_dict)

        response_data = {
            "query": query,
            "customer_id": formatted_customer_id,
            "total_results": len(results),
            "results": results
        }

        # Add fixes info if any were applied
        if fixes:
            response_data["auto_fixes_applied"] = fixes

        return json.dumps(response_data, indent=2, default=str)

    except GoogleAdsException as ex:
        error_details = []
        for error in ex.failure.errors:
            error_details.append({
                "error_code": str(error.error_code),
                "message": error.message,
                "location": error.location.field_path_elements if error.location else None
            })

        return json.dumps({
            "error": "Google Ads API error",
            "details": error_details,
            "query": query
        }, indent=2)

    except Exception as e:
        logger.error(f"Error executing GAQL query: {e}")
        return json.dumps({
            "error": f"Failed to execute GAQL query: {str(e)}",
            "query": query
        }, indent=2)


def execute_gaql_query(query: str, customer_id: str) -> str:
    """Execute a Google Ads Query Language (GAQL) query.

    Args:
        query: GAQL query string to execute
        customer_id: Google Ads customer ID (10 digits, with or without dashes)

    Returns:
        JSON string containing query results

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
    return asyncio.run(_execute_gaql_async(query, customer_id))


def preprocess_gaql_query(query: str) -> str:
    """Preprocess and optimize a GAQL query for better performance.

    Args:
        query: GAQL query string to preprocess

    Returns:
        JSON string containing the optimized query and suggestions
    """
    from ..auth import validate_gaql_query

    try:
        if not validate_gaql_query(query):
            return json.dumps({
                "error": "Invalid GAQL query format",
                "original_query": query
            }, indent=2)

        suggestions = []
        optimized_query = query.strip()

        # Check for missing LIMIT clause
        if "LIMIT" not in optimized_query.upper():
            suggestions.append({
                "type": "performance",
                "message": "Consider adding a LIMIT clause to prevent large result sets",
                "suggestion": "Add 'LIMIT 1000' to your query"
            })

        # Check for date range filtering
        if "segments.date" in optimized_query.lower() and "DURING" not in optimized_query.upper():
            suggestions.append({
                "type": "performance",
                "message": "When using segments.date, consider adding a date range filter",
                "suggestion": "Add 'WHERE segments.date DURING LAST_30_DAYS' to your query"
            })

        # Check for expensive metrics without filtering
        expensive_metrics = ["metrics.impressions", "metrics.clicks", "metrics.cost_micros"]
        has_expensive_metrics = any(metric in optimized_query.lower() for metric in expensive_metrics)
        has_where_clause = "WHERE" in optimized_query.upper()

        if has_expensive_metrics and not has_where_clause:
            suggestions.append({
                "type": "performance",
                "message": "Performance metrics should be filtered to improve query speed",
                "suggestion": "Add WHERE conditions to filter your data"
            })

        return json.dumps({
            "original_query": query,
            "optimized_query": optimized_query,
            "is_valid": True,
            "suggestions": suggestions,
            "suggestion_count": len(suggestions)
        }, indent=2)

    except Exception as e:
        logger.error(f"Error preprocessing GAQL query: {e}")
        return json.dumps({
            "error": f"Failed to preprocess GAQL query: {str(e)}",
            "original_query": query
        }, indent=2)
