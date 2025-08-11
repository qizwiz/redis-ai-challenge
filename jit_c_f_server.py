#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("jit-c-f")


@mcp.tool()
def c_f(arg0: str) -> str:
    """JIT-created server for c_f operation"""
    return f"Executed c_f with args: {locals()}"


if __name__ == "__main__":
    mcp.run()
