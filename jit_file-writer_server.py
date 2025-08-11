#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("jit-file-writer")


@mcp.tool()
def file_writer(arg0: str) -> str:
    """JIT-created server for file-writer operation"""
    return f"Executed file-writer with args: {locals()}"


if __name__ == "__main__":
    mcp.run()
