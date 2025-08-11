#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("jit-api-call")


@mcp.tool()
def api_call(arg0: str, arg1: str) -> str:
    """Make API calls"""
    return f"Executed api_call with args: {locals()}"


if __name__ == "__main__":
    mcp.run()
