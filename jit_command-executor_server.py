#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("jit-command-executor")


@mcp.tool()
def command_executor(arg0: str, arg1: str) -> str:
    """JIT-created server for command-executor operation"""
    return f"Executed command-executor with args: {locals()}"


if __name__ == "__main__":
    mcp.run()
