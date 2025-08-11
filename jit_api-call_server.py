#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("jit-api-call")


@mcp.tool()
def api_call(arg0: str, arg1: str) -> str:
    """JIT-created server for api-call operation"""
    return f"Executed api-call with args: {locals()}"


if __name__ == "__main__":
    mcp.run()
