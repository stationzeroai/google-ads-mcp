from fastmcp import FastMCP
from .tools import *
from .config import *

mcp = FastMCP("Google Ads MCP Server")


def main():
    mcp.run()


if __name__ == "__main__":
    main()
