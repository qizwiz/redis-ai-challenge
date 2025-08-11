#!/usr/bin/env python3
"""
Dynamic MCP Server Registration without Claude Code restart
"""

import json
import os

def register_mcp_server(name, command, args=None, env=None, description=None):
    """Register MCP server dynamically by updating Claude's config"""
    
    config_path = os.path.expanduser("~/.claude/.mcp.json")
    
    # Read existing config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Add new server
    config["mcpServers"][name] = {
        "type": "stdio",
        "command": command,
        "args": args or [],
        "env": env or {},
        "description": description or f"Dynamically registered {name}"
    }
    
    # Write back
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Registered MCP server: {name}")
    return True

def trigger_mcp_refresh():
    """Attempt to trigger Claude Code MCP refresh"""
    # This is the research question - can we signal Claude Code to reload?
    os.system("killall -USR1 claude 2>/dev/null")  # Signal reload
    print("🔄 Triggered MCP refresh signal")

if __name__ == "__main__":
    # Test registration
    register_mcp_server(
        "real-time-state",
        "python3",
        ["real_time_state_bridge.py"],
        description="Real-time Emacs state synchronization"
    )
    trigger_mcp_refresh()