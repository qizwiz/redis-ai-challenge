#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("jit-result-formatter")


@mcp.tool()
def result_formatter(arg0: str, arg1: str) -> str:
    """JIT-created server for result-formatter operation"""
    return f"Executed result-formatter with args: {locals()}"


if __name__ == "__main__":
    mcp.run()
