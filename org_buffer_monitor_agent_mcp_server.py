#!/usr/bin/env python3
"""
org_buffer_monitor_agent - Auto-generated Buffer Agent MCP Server
Monitor org-roam buffers for changes
"""

from fastmcp import FastMCP
import redis
import json
import time

mcp = FastMCP("org_buffer_monitor_agent")
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

@mcp.tool()
def monitor_agent_activity() -> str:
    """Monitor this agent's activity in the knowledge graph"""
    
    activity = r.hgetall("agent:org_buffer_monitor_agent:activity")
    if not activity:
        activity = {"status": "active", "last_update": str(time.time())}
        r.hset("agent:org_buffer_monitor_agent:activity", mapping=activity)
    
    return f"""🤖 AGENT STATUS: org_buffer_monitor_agent
Purpose: Monitor org-roam buffers for changes
Status: {activity.get('status', 'unknown')}
Last Update: {activity.get('last_update', 'never')}

✅ Buffer agent monitoring active
"""

@mcp.tool()
def coordinate_with_agents() -> str:
    """Coordinate with other buffer agents"""
    
    # Get all active agents
    active_agents = list(r.smembers("active_agents"))
    
    # Send coordination message
    coord_msg = {
        "from": "org_buffer_monitor_agent",
        "message": "Agent coordination check",
        "timestamp": str(time.time()),
        "active_agents": active_agents
    }
    
    r.xadd("agent:coordination", coord_msg)
    
    return f"""🔗 AGENT COORDINATION:
From: org_buffer_monitor_agent
Active Agents: {len(active_agents)}
Message Sent: Agent coordination check

✅ Coordination message sent to knowledge graph
"""

if __name__ == "__main__":
    mcp.run()
