#!/usr/bin/env python3
"""
Tools for introspecting FastMCP FunctionTool objects.
"""

import sys
import json
import inspect
import os
import traceback

def print_log(prefix, text):
    """Prints a log message to stderr, pretty-printing JSON if possible."""
    try:
        parsed = json.loads(text)
        pretty_text = json.dumps(parsed, indent=2)
        log_message = f"{prefix}\n{pretty_text}\n"
    except json.JSONDecodeError:
        log_message = f"{prefix} {text.strip()}\n"
    
    sys.stderr.write(log_message)
    sys.stderr.flush()

def introspect_function_tool(func_tool_obj, name="FunctionTool"):
    """
    Prints detailed introspection information about a FastMCP FunctionTool object.
    """
    sys.stderr.write(f"--- Introspecting {name} ({type(func_tool_obj)}) ---\n")
    sys.stderr.write(f"Type: {type(func_tool_obj)}\n")
    sys.stderr.write(f"Callable: {callable(func_tool_obj)}\n")
    sys.stderr.write(f"Has __wrapped__: {hasattr(func_tool_obj, '__wrapped__')}\n")
    if hasattr(func_tool_obj, '__wrapped__'):
        sys.stderr.write(f"__wrapped__ type: {type(func_tool_obj.__wrapped__)}\n")
        sys.stderr.write(f"__wrapped__ callable: {callable(func_tool_obj.__wrapped__)}\n")
        try:
            sys.stderr.write(f"__wrapped__ signature: {inspect.signature(func_tool_obj.__wrapped__)}\n")
        except ValueError:
            sys.stderr.write(f"__wrapped__ signature: Not available\n")
    
    # Specific FastMCP attributes
    sys.stderr.write(f"Has .fn: {hasattr(func_tool_obj, 'fn')}\n")
    if hasattr(func_tool_obj, 'fn'):
        sys.stderr.write(f".fn type: {type(func_tool_obj.fn)}\n")
        sys.stderr.write(f".fn callable: {callable(func_tool_obj.fn)}\n")
        try:
            sys.stderr.write(f".fn signature: {inspect.signature(func_tool_obj.fn)}\n")
        except ValueError:
            sys.stderr.write(f".fn signature: Not available\n")

    sys.stderr.write(f"Dir: {dir(func_tool_obj)}\n")
    sys.stderr.write(f"--- End Introspection ---\n")

if __name__ == "__main__":
    # This part allows running the introspection tool directly
    # For example: python mcp_introspection_tools.py add_context
    if len(sys.argv) < 2:
        print("Usage: python mcp_introspection_tools.py <tool_name>", file=sys.stderr)
        sys.exit(1)

    tool_name_to_introspect = sys.argv[1]

    # Dynamically import the context_manager_agent to get the FunctionTool object
    try:
        # Add parent directory to path if not already there
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
        from emacs_persistent_vision_mcp import (
            get_emacs_state,
            execute_elisp,
            switch_buffer,
            create_buffer_with_content,
            split_window,
            goto_line,
            insert_text,
            get_vision_history,
            emacs_health_check
        )
        
        tool_map = {
            "get_emacs_state": get_emacs_state,
            "execute_elisp": execute_elisp,
            "switch_buffer": switch_buffer,
            "create_buffer_with_content": create_buffer_with_content,
            "split_window": split_window,
            "goto_line": goto_line,
            "insert_text": insert_text,
            "get_vision_history": get_vision_history,
            "emacs_health_check": emacs_health_check
        }

        if tool_name_to_introspect in tool_map:
            introspect_function_tool(tool_map[tool_name_to_introspect], tool_name_to_introspect)
        else:
            print(f"Tool '{tool_name_to_introspect}' not found in context_manager_agent.py", file=sys.stderr)

    except ImportError as e:
        print(f"Error importing context_manager_agent: {e}. Make sure it's in the same directory or Python path.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred during introspection: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
