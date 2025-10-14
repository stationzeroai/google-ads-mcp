"""Google Ads customer account management tools."""

import asyncio
import json
import logging

from google.ads.googleads.errors import GoogleAdsException

from .gaql import parse_select_fields, _convert_protobuf_value


logger = logging.getLogger(__name__)


async def _list_accessible_customers_async() -> str:
    """List all accessible Google Ads customer accounts asynchronously."""
    from ..__main__ import get_client

    try:
        # Get authenticated client
        client = get_client()
        customer_service = client.get_service("CustomerService")

        # List accessible customers
        accessible_customers = await asyncio.to_thread(customer_service.list_accessible_customers)

        customers = []
        for customer_resource_name in accessible_customers.resource_names:
            # Extract customer ID from resource name
            customer_id = customer_resource_name.split("/")[-1]

            # Just include basic information from the resource name
            customers.append({
                "customer_id": customer_id,
                "resource_name": customer_resource_name,
                "status": "accessible"
            })

        return json.dumps({
            "total_customers": len(customers),
            "customers": customers
        }, indent=2, default=str)

    except GoogleAdsException as ex:
        error_details = []
        for error in ex.failure.errors:
            error_details.append({
                "error_code": str(error.error_code),
                "message": error.message
            })

        return json.dumps({
            "error": "Google Ads API error",
            "details": error_details
        }, indent=2)

    except Exception as e:
        logger.error(f"Error listing accessible customers: {e}")
        return json.dumps({
            "error": f"Failed to list accessible customers: {str(e)}"
        }, indent=2)




async def _get_customer_info_async(customer_id: str) -> str:
    """Get detailed information about the customer account asynchronously."""
    from ..__main__ import get_client
    from ..auth import format_customer_id

    try:
        if not customer_id:
            return json.dumps({
                "error": "customer_id is required"
            }, indent=2)

        # Format customer ID
        formatted_customer_id = format_customer_id(customer_id)

        # Build GAQL query for customer information
        query = """
            SELECT
                customer.id,
                customer.descriptive_name,
                customer.currency_code,
                customer.time_zone,
                customer.tracking_url_template,
                customer.auto_tagging_enabled,
                customer.has_partners_badge,
                customer.manager,
                customer.test_account,
                customer.resource_name
            FROM customer
            LIMIT 1
        """

        # Get authenticated client and execute the query
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

        # Parse the result and extract customer info
        if results and len(results) > 0:
            customer_data = results[0].get("customer", {})

            return json.dumps({
                "customer_id": formatted_customer_id,
                "name": customer_data.get("descriptive_name", ""),
                "currency_code": customer_data.get("currency_code", ""),
                "time_zone": customer_data.get("time_zone", ""),
                "resource_name": customer_data.get("resource_name", ""),
                "auto_tagging_enabled": customer_data.get("auto_tagging_enabled", False),
                "has_partners_badge": customer_data.get("has_partners_badge", False),
                "is_manager": customer_data.get("manager", False),
                "is_test_account": customer_data.get("test_account", False),
                "tracking_url_template": customer_data.get("tracking_url_template", "")
            }, indent=2)
        else:
            return json.dumps({
                "error": f"No customer information found for ID: {formatted_customer_id}"
            }, indent=2)

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
            "details": error_details
        }, indent=2)

    except Exception as e:
        logger.error(f"Error getting customer info: {e}")
        return json.dumps({
            "error": f"Failed to get customer info: {str(e)}"
        }, indent=2)


