#!/usr/bin/env python3
import json
import sys
from typing import Dict, Any

def handle_mcp_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Generated MCP server that responds to conversation context"""
    if request.get("method") == "tools/list":
        return {
            "result": {
                "tools": [
                    {
                        "name": "conversation_echo",
                        "description": "Echo conversation context"
                    }
                ]
            }
        }
    return {"error": {"code": -1, "message": "Unknown method"}}

if __name__ == "__main__":
    request = json.load(sys.stdin)
    response = handle_mcp_request(request)
    print(json.dumps(response))