#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("jit-data-merger")


@mcp.tool()
def data_merger(arg0: str, arg1: str) -> str:
    """JIT-created server for data-merger operation"""
    return f"Executed data-merger with args: {locals()}"


if __name__ == "__main__":
    mcp.run()
