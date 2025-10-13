# Google Ads MCP Server

MCP (Model Context Protocol) server for Google Ads API integration, enabling AI assistants to interact with Google Ads accounts.

## Features

- **Authentication**: OAuth2 refresh token-based authentication with automatic token renewal
- **MCC Support**: Connect to Manager (MCC) accounts to access multiple client accounts
- **Health Check**: Built-in connection validation tool

## Prerequisites

1. **Google Ads Developer Token**: Required for all API access
   - Apply at: https://ads.google.com/aw/apicenter
   - Must have at least Basic access level

2. **Google Cloud Project**: OAuth2 credentials
   - Create project at: https://console.cloud.google.com
   - Enable Google Ads API
   - Create OAuth 2.0 credentials (Desktop app type)

3. **OAuth2 Refresh Token**: Generated via OAuth flow
   - Use Google's [generate-refresh-token tool](https://github.com/googleads/google-ads-python/blob/main/examples/authentication/generate_user_credentials.py)
   - Or implement your own OAuth flow

## Installation

```bash
# Install dependencies
uv sync

# Or with pip
pip install -e .
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Fill in your credentials in `.env`:
```env
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token

# Optional: For MCC (Manager) accounts
GOOGLE_ADS_MCC_ID=1234567890
```

## Usage

### Standalone Mode

```bash
# Run the MCP server directly
uv run google-ads-mcp

# Or with environment variables
GOOGLE_ADS_DEVELOPER_TOKEN=xxx GOOGLE_CLIENT_ID=xxx ... uv run google-ads-mcp
```

### Integration with MCPClientBuilder

Add to your MCP client configuration:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

servers = {
    "google-ads-mcp": {
        "transport": "stdio",
        "command": "uv",
        "args": ["run", "google-ads-mcp"],
        "env": {
            "GOOGLE_ADS_DEVELOPER_TOKEN": context.google_ads_developer_token,
            "GOOGLE_ADS_REFRESH_TOKEN": context.google_ads_refresh_token,
            "GOOGLE_CLIENT_ID": context.google_client_id,
            "GOOGLE_CLIENT_SECRET": context.google_client_secret,
            "GOOGLE_ADS_MCC_ID": context.google_ads_mcc_id or "",
        }
    }
}

client = MultiServerMCPClient(servers)
```

## Available Tools

### check_connection

Test Google Ads API authentication and return connection status.

**Returns**: JSON with connection status and list of accessible customer accounts

**Example response**:
```json
{
  "status": "connected",
  "authentication_method": "refresh_token",
  "mcc_account": "1234567890",
  "total_accessible_customers": 5,
  "accessible_customers": [
    {
      "customer_id": "9876543210",
      "resource_name": "customers/9876543210"
    }
  ],
  "message": "Successfully authenticated with Google Ads API"
}
```

## Authentication Details

The server uses OAuth2 refresh token authentication with automatic token renewal:

1. **Refresh Token**: Long-lived token that doesn't expire
2. **Access Token**: Automatically generated and refreshed when needed
3. **MCC Support**: Optional manager account ID for accessing linked accounts

### Required Scopes

- `https://www.googleapis.com/auth/adwords`
- `https://www.googleapis.com/auth/userinfo.email`
- `https://www.googleapis.com/auth/userinfo.profile`

## Troubleshooting

### "Developer token is invalid"
- Verify your developer token at https://ads.google.com/aw/apicenter
- Ensure token has at least Basic access level

### "OAuth2 credentials are invalid"
- Regenerate your refresh token using the OAuth flow
- Verify client_id and client_secret are correct

### "Customer ID format is invalid"
- Customer IDs must be exactly 10 digits
- Remove dashes if present (e.g., use `1234567890` not `123-456-7890`)

### "Cannot access customer account"
- Verify account is linked to your MCC (if using MCC)
- Check account permissions in Google Ads interface

## Development

```bash
# Install development dependencies
uv sync

# Run tests (when available)
pytest

# Format code
black src/

# Type checking
mypy src/
```

## License

MIT

## Related Resources

- [Google Ads API Documentation](https://developers.google.com/google-ads/api/docs)
- [Google Ads Python Client](https://github.com/googleads/google-ads-python)
- [MCP Protocol](https://modelcontextprotocol.io)
