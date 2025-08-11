#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("jit-ml-inference")


@mcp.tool()
def ml_inference(arg0: str, arg1: str) -> str:
    """JIT-created server for ml-inference operation"""
    return f"Executed ml-inference with args: {locals()}"


if __name__ == "__main__":
    mcp.run()
