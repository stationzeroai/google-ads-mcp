"""Authentication utilities for Google Ads API."""

from typing import Optional
from google.ads.googleads.client import GoogleAdsClient
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from .config import config


def get_ads_client() -> GoogleAdsClient:
    """Get or create a Google Ads client instance using refresh token authentication.

    Returns:
        GoogleAdsClient: Authenticated Google Ads API client

    Raises:
        ValueError: If required credentials are missing
        RuntimeError: If client creation fails
    """
    try:
        # Validate required credentials
        if not config.GOOGLE_ADS_REFRESH_TOKEN:
            raise ValueError("GOOGLE_ADS_REFRESH_TOKEN is required")
        if not config.GOOGLE_ADS_DEVELOPER_TOKEN:
            raise ValueError("GOOGLE_ADS_DEVELOPER_TOKEN is required")
        if not config.GOOGLE_CLIENT_ID:
            raise ValueError("GOOGLE_CLIENT_ID is required")
        if not config.GOOGLE_CLIENT_SECRET:
            raise ValueError("GOOGLE_CLIENT_SECRET is required")

        # Create OAuth2 credentials with refresh token
        credentials = Credentials(
            token=None,  # Will be refreshed automatically
            refresh_token=config.GOOGLE_ADS_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=config.GOOGLE_CLIENT_ID,
            client_secret=config.GOOGLE_CLIENT_SECRET,
            scopes=[
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/adwords",
            ],
        )

        # Refresh the token to ensure we have a valid access token
        credentials.refresh(Request())

        # Create client with optional MCC support
        client_kwargs = {
            "credentials": credentials,
            "developer_token": config.GOOGLE_ADS_DEVELOPER_TOKEN,
        }

        # Add MCC ID if provided for manager account access
        if config.GOOGLE_ADS_MCC_ID:
            client_kwargs["login_customer_id"] = config.GOOGLE_ADS_MCC_ID

        return GoogleAdsClient(**client_kwargs)

    except Exception as e:
        raise RuntimeError(f"Failed to create Google Ads client: {str(e)}")


def format_customer_id(customer_id: str) -> str:
    """Format customer ID by removing dashes and ensuring 10 digits.

    Args:
        customer_id: Customer ID with or without dashes (e.g., "123-456-7890" or "1234567890")

    Returns:
        str: Formatted customer ID without dashes

    Raises:
        ValueError: If customer ID format is invalid
    """
    if not customer_id:
        raise ValueError("Customer ID cannot be empty")

    # Remove dashes and any whitespace
    clean_id = customer_id.replace("-", "").replace(" ", "")

    # Ensure it's all digits and exactly 10 characters
    if not clean_id.isdigit() or len(clean_id) != 10:
        raise ValueError(f"Customer ID must be exactly 10 digits, got: {customer_id}")

    return clean_id


def validate_gaql_query(query: str) -> bool:
    """Basic validation of GAQL query syntax.

    Args:
        query: GAQL query string

    Returns:
        bool: True if query appears valid, False otherwise
    """
    if not query or not isinstance(query, str):
        return False

    query_upper = query.upper().strip()

    # Must have SELECT and FROM clauses
    if not query_upper.startswith("SELECT"):
        return False

    if "FROM" not in query_upper:
        return False

    return True
