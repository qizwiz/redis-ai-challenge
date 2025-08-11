#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("jit-tutorial-parser")


@mcp.tool()
def tutorial_parser(arg0: str, arg1: str) -> str:
    """JIT-created server for tutorial-parser operation"""
    return f"Executed tutorial-parser with args: {locals()}"


if __name__ == "__main__":
    mcp.run()
