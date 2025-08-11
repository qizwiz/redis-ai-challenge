#!/usr/bin/env python3
"""
Custom MCP Server for ContextManagerAgent.
A simple JSON-RPC server that wraps ContextManagerAgent tools.
"""

import sys
import json
import traceback # For detailed error logging
import os # For os.path.dirname
import inspect # For introspection

# Import the ContextManagerAgent and its dependencies
# Assuming context_manager_agent.py is in the same directory
try:
    from context_manager_agent import (
        ContextManagerAgent, ContextAnalyzer,
        add_context, get_relevant_context, get_session_summary,
        search_context_by_tag, cleanup_old_context, get_context_stats
    )
except ImportError:
    # Fallback for when run from a different directory
    sys.path.append(os.path.dirname(__file__))
    from context_manager_agent import (
        ContextManagerAgent, ContextAnalyzer,
        add_context, get_relevant_context, get_session_summary,
        search_context_by_tag, cleanup_old_context, get_context_stats
    )

# Initialize the agent (still needed for ContextManagerAgent instance)
agent = ContextManagerAgent()

def send_response(id, result=None, error=None):
    """Sends a JSON-RPC response."""
    response = {"jsonrpc": "2.0", "id": id}
    if result is not None:
        response["result"] = result
    if error is not None:
        response["error"] = error
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()

def send_error(id, code, message, data=None):
    """Sends a JSON-RPC error response."""
    error_obj = {"code": code, "message": message}
    if data is not None:
        error_obj["data"] = data
    send_response(id, error=error_obj)

def dispatch_tool_call(method_name, params):
    """Dispatches the tool call to the ContextManagerAgent."""
    # All our tools now expect a single args_json string
    args_json = params.get("arguments")

    # Map method names to agent methods (now directly to the imported functions)
    tool_map = {
        "add_context": add_context,
        "get_relevant_context": get_relevant_context,
        "get_session_summary": get_session_summary,
        "search_context_by_tag": search_context_by_tag,
        "cleanup_old_context": cleanup_old_context,
        "get_context_stats": get_context_stats,
    }

    if method_name not in tool_map:
        raise ValueError(f"Unknown tool: {method_name}")

    # Call the tool function with the args_json string
    return tool_map[method_name].fn(args_json)

def main():
    sys.stderr.write("--- Custom Context MCP Server Starting ---
")
    sys.stderr.flush()

    for line in sys.stdin:
        try:
            request = json.loads(line)
            id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            if method == "initialize":
                # Respond to initialize
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True},
                        # Add other capabilities as needed
                    },
                    "serverInfo": {"name": "custom-context-mcp", "version": "1.0.0"},
                }
                send_response(id, result=result)
            elif method == "notifications/initialized":
                # Notification, no response expected
                pass
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments") # This will be the args_json string

                try:
                    tool_result = dispatch_tool_call(tool_name, {"arguments": tool_args})
                    # Wrap the result in the expected FastMCP format
                    wrapped_result = {"content": [{"type": "text", "text": tool_result}]}
                    send_response(id, result=wrapped_result)
                except Exception as e:
                    sys.stderr.write(f"Error dispatching tool {tool_name}: {e}\n")
                    traceback.print_exc(file=sys.stderr)
                    send_error(id, -32000, "Tool execution failed", str(e))
            elif method == "tools/list":
                # Implement tools/list response
                # This would require building the schema dynamically or hardcoding
                # For now, just return a simplified list
                tools_list = [
                    {"name": "add_context", "description": "Add new context (args_json)"},
                    {"name": "get_relevant_context", "description": "Get relevant context (args_json)"},
                    {"name": "get_session_summary", "description": "Get session summary (args_json)"},
                    {"name": "search_context_by_tag", "description": "Search by tag (args_json)"},
                    {"name": "cleanup_old_context", "description": "Cleanup old context (args_json)"},
                    {"name": "get_context_stats", "description": "Get context stats (args_json)"},
                ]
                send_response(id, result={"tools": tools_list})
            else:
                send_error(id, -32601, f"Method not found: {method}")

        except json.JSONDecodeError:
            send_error(None, -32700, "Parse error")
        except Exception as e:
            sys.stderr.write(f"Unhandled server error: {e}\n")
            traceback.print_exc(file=sys.stderr)
            send_error(None, -32000, "Server error", str(e))

if __name__ == "__main__":
    main()
