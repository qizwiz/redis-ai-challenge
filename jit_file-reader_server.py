#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("jit-file-reader")


@mcp.tool()
def file_reader(arg0: str) -> str:
    """JIT-created server for file-reader operation"""
    return f"Executed file-reader with args: {locals()}"


if __name__ == "__main__":
    mcp.run()
