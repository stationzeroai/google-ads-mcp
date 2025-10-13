from fastmcp import FastMCP
from .tools import *
from .config import config
from .auth import get_ads_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Google Ads MCP Server")

# Initialize Google Ads client on startup
_ads_client = None


def get_client():
    """Get or create the Google Ads client instance."""
    global _ads_client
    if _ads_client is None:
        try:
            logger.info("Initializing Google Ads client...")
            _ads_client = get_ads_client()
            logger.info("Google Ads client initialized successfully")
            if config.GOOGLE_ADS_MCC_ID:
                logger.info(f"Using MCC account: {config.GOOGLE_ADS_MCC_ID}")
        except Exception as e:
            logger.error(f"Failed to initialize Google Ads client: {e}")
            raise
    return _ads_client


def main():
    try:
        # Validate authentication on startup
        get_client()
        logger.info("Starting Google Ads MCP Server...")
        mcp.run()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()
