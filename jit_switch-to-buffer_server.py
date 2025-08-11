#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("jit-switch-to-buffer")


@mcp.tool()
def switch_to_buffer(arg0: str) -> str:
    """JIT-created server for switch-to-buffer operation"""
    return f"Executed switch-to-buffer with args: {locals()}"


if __name__ == "__main__":
    mcp.run()
