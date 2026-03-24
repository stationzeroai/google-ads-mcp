"""Google Ads campaign management tools."""

import asyncio
import json
import logging
import re

from google.ads.googleads.errors import GoogleAdsException

from .gaql import parse_select_fields, _convert_protobuf_value


logger = logging.getLogger(__name__)

_BUDGET_RESOURCE_RE = re.compile(r'^customers/\d+/campaignBudgets/\d+$')
_CAMPAIGN_RESOURCE_RE = re.compile(r'^customers/\d+/campaigns/\d+$')
_CAMPAIGN_ID_RE = re.compile(r'^\d+$')


async def _update_campaign_budget_async(
    customer_id: str,
    budget_resource_name: str,
    amount_micros: int,
) -> str:
    """Update the daily budget amount for a campaign budget asynchronously."""
    from ..__main__ import get_client
    from ..auth import format_customer_id

    try:
        if not customer_id:
            return json.dumps({
                "error": "customer_id is required"
            }, indent=2)

        formatted_customer_id = format_customer_id(customer_id)

        if not _BUDGET_RESOURCE_RE.match(budget_resource_name):
            return json.dumps({
                "error": "Invalid budget_resource_name format. Expected: customers/{id}/campaignBudgets/{id}",
                "received": budget_resource_name
            }, indent=2)

        if not isinstance(amount_micros, int) or amount_micros <= 0:
            return json.dumps({
                "error": "amount_micros must be a positive integer",
                "received": amount_micros
            }, indent=2)

        logger.info(
            "Updating campaign budget: customer_id=%s, resource_name=%s, new_amount_micros=%d",
            formatted_customer_id,
            budget_resource_name,
            amount_micros,
        )

        client = get_client()
        service = client.get_service("CampaignBudgetService")
        operation = client.get_type("CampaignBudgetOperation")

        budget = operation.update
        budget.resource_name = budget_resource_name
        budget.amount_micros = amount_micros

        operation.update_mask.paths.append("amount_micros")

        response = await asyncio.to_thread(
            service.mutate_campaign_budgets,
            customer_id=formatted_customer_id,
            operations=[operation],
        )

        result = response.results[0]
        return json.dumps({
            "status": "success",
            "operation": "update_campaign_budget",
            "customer_id": formatted_customer_id,
            "resource_name": result.resource_name,
            "updated_fields": {
                "amount_micros": amount_micros
            }
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
            "details": error_details,
            "customer_id": customer_id
        }, indent=2)

    except Exception as e:
        logger.error("Error updating campaign budget: %s", e)
        return json.dumps({
            "error": f"Failed to update campaign budget: {str(e)}"
        }, indent=2)


async def _update_campaign_status_async(
    customer_id: str,
    campaign_resource_name: str,
    status: str,
) -> str:
    """Update the status of a campaign (enable or pause) asynchronously."""
    from ..__main__ import get_client
    from ..auth import format_customer_id

    try:
        if not customer_id:
            return json.dumps({
                "error": "customer_id is required"
            }, indent=2)

        formatted_customer_id = format_customer_id(customer_id)

        if not _CAMPAIGN_RESOURCE_RE.match(campaign_resource_name):
            return json.dumps({
                "error": "Invalid campaign_resource_name format. Expected: customers/{id}/campaigns/{id}",
                "received": campaign_resource_name
            }, indent=2)

        normalized_status = status.upper()
        if normalized_status not in {"ENABLED", "PAUSED"}:
            return json.dumps({
                "error": "status must be ENABLED or PAUSED",
                "received": status
            }, indent=2)

        logger.info(
            "Updating campaign status: customer_id=%s, resource_name=%s, new_status=%s",
            formatted_customer_id,
            campaign_resource_name,
            normalized_status,
        )

        client = get_client()
        service = client.get_service("CampaignService")
        operation = client.get_type("CampaignOperation")

        campaign = operation.update
        campaign.resource_name = campaign_resource_name

        status_enum = client.enums.CampaignStatusEnum.CampaignStatus
        campaign.status = getattr(status_enum, normalized_status)

        operation.update_mask.paths.append("status")

        response = await asyncio.to_thread(
            service.mutate_campaigns,
            customer_id=formatted_customer_id,
            operations=[operation],
        )

        result = response.results[0]
        return json.dumps({
            "status": "success",
            "operation": "update_campaign_status",
            "customer_id": formatted_customer_id,
            "resource_name": result.resource_name,
            "updated_fields": {
                "status": normalized_status
            }
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
            "details": error_details,
            "customer_id": customer_id
        }, indent=2)

    except Exception as e:
        logger.error("Error updating campaign status: %s", e)
        return json.dumps({
            "error": f"Failed to update campaign status: {str(e)}"
        }, indent=2)


async def _get_campaign_budgets_async(
    customer_id: str,
    campaign_ids: list[str] | None = None,
) -> str:
    """Get budget information for enabled campaigns asynchronously."""
    from ..__main__ import get_client
    from ..auth import format_customer_id

    try:
        if not customer_id:
            return json.dumps({
                "error": "customer_id is required"
            }, indent=2)

        formatted_customer_id = format_customer_id(customer_id)

        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign_budget.resource_name,
                campaign_budget.amount_micros
            FROM campaign
            WHERE campaign.status = 'ENABLED'
        """

        if campaign_ids:
            for cid in campaign_ids:
                if not _CAMPAIGN_ID_RE.match(cid):
                    return json.dumps({
                        "error": f"Invalid campaign_id: must be digits only",
                        "received": cid
                    }, indent=2)
            ids_str = ", ".join(f"'{cid}'" for cid in campaign_ids)
            query += f" AND campaign.id IN ({ids_str})"

        client = get_client()
        google_ads_service = client.get_service("GoogleAdsService")

        search_request = client.get_type("SearchGoogleAdsRequest")
        search_request.customer_id = formatted_customer_id
        search_request.query = query

        response = await asyncio.to_thread(google_ads_service.search, request=search_request)

        requested_entities = parse_select_fields(query)
        results = []

        for row in response:
            result_dict = {}

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

        return json.dumps({
            "query": query.strip(),
            "customer_id": formatted_customer_id,
            "total_results": len(results),
            "results": results
        }, indent=2, default=str)

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
            "customer_id": customer_id
        }, indent=2)

    except Exception as e:
        logger.error("Error getting campaign budgets: %s", e)
        return json.dumps({
            "error": f"Failed to get campaign budgets: {str(e)}"
        }, indent=2)
