#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("jit-split-window")


@mcp.tool()
def split_window(arg0: str) -> str:
    """JIT-created server for split-window operation"""
    return f"Executed split-window with args: {locals()}"


if __name__ == "__main__":
    mcp.run()
