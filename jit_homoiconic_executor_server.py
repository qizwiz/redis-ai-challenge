#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("jit-homoiconic-executor")


@mcp.tool()
def homoiconic_executor(arg0: lisp_expr, arg1: context) -> str:
    """Execute homoiconic Lisp expressions"""
    return f"Executed homoiconic_executor with args: {locals()}"


if __name__ == "__main__":
    mcp.run()
