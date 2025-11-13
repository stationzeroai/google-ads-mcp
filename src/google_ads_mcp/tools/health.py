"""Health check and authentication validation tools."""

import asyncio
import json
from google.ads.googleads.errors import GoogleAdsException


async def check_google_ads_connection() -> str:
    """Test Google Ads API authentication and return connection status.

    This tool validates that the Google Ads client is properly authenticated
    and can communicate with the Google Ads API.

    Returns:
        str: JSON string containing connection status and customer count
    """
    from ..__main__ import get_client
    from ..config import config

    try:
        client = get_client()

        # Test the connection by listing accessible customers
        customer_service = client.get_service("CustomerService")
        accessible_customers = await asyncio.to_thread(
            customer_service.list_accessible_customers
        )

        total_customers = len(accessible_customers.resource_names)

        return json.dumps(
            {
                "status": "connected",
                "authentication_method": "refresh_token",
                "mcc_account": config.GOOGLE_ADS_MCC_ID or "N/A",
                "total_accessible_customers": total_customers,
                "message": "Successfully authenticated with Google Ads API",
            },
            indent=2,
        )

    except GoogleAdsException as ex:
        error_details = []
        for error in ex.failure.errors:
            error_details.append(
                {"error_code": str(error.error_code), "message": error.message}
            )

        return json.dumps(
            {
                "status": "error",
                "error_type": "GoogleAdsException",
                "details": error_details,
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps(
            {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e),
            },
            indent=2,
        )
