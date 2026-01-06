#!/usr/bin/env python3
"""
session_context_agent - Auto-generated Buffer Agent MCP Server
Maintain session context across interactions
"""

from fastmcp import FastMCP
import redis
import json
import time

mcp = FastMCP("session_context_agent")
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

@mcp.tool()
def monitor_agent_activity() -> str:
    """Monitor this agent's activity in the knowledge graph"""
    
    activity = r.hgetall("agent:session_context_agent:activity")
    if not activity:
        activity = {"status": "active", "last_update": str(time.time())}
        r.hset("agent:session_context_agent:activity", mapping=activity)
    
    return f"""🤖 AGENT STATUS: session_context_agent
Purpose: Maintain session context across interactions
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
        "from": "session_context_agent",
        "message": "Agent coordination check",
        "timestamp": str(time.time()),
        "active_agents": active_agents
    }
    
    r.xadd("agent:coordination", coord_msg)
    
    return f"""🔗 AGENT COORDINATION:
From: session_context_agent
Active Agents: {len(active_agents)}
Message Sent: Agent coordination check

✅ Coordination message sent to knowledge graph
"""

if __name__ == "__main__":
    mcp.run()
