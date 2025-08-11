#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("jit-database-query")


@mcp.tool()
def database_query(arg0: str, arg1: str) -> str:
    """JIT-created server for database-query operation"""
    return f"Executed database-query with args: {locals()}"


if __name__ == "__main__":
    mcp.run()
