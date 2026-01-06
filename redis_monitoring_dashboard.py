#!/usr/bin/env python3
"""
REDIS MONITORING DASHBOARD - Created by AI Dev Team
Real-time monitoring of our semantic intelligence systems
"""

import redis
import time
import json

class RedisMonitoringDashboard:
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    def show_live_stats(self):
        """Show live Redis stats for our semantic systems"""
        print("📊 SEMANTIC INTELLIGENCE LIVE STATS")
        print("=" * 40)
        
        # Get semantic execution counts
        semantic_executions = self.r.xlen("semantic:validation") or 0
        lisp_executions = self.r.xlen("lisp:real_executions") or 0
        user_problems = self.r.xlen("real_user_problems") or 0
        
        print(f"Semantic Validations: {semantic_executions}")
        print(f"Lisp Executions: {lisp_executions}")  
        print(f"User Problems Solved: {user_problems}")
        
        # Show active MCP servers
        generated_servers = self.r.smembers("generated_mcp_servers")
        print(f"Active MCP Servers: {len(generated_servers)}")
        
        # Show recent activity
        recent = self.r.xrevrange("semantic:scaling_proven", count=1)
        if recent:
            print(f"Latest Activity: {recent[0][1]}")
        
        return {
            "semantic_executions": semantic_executions,
            "lisp_executions": lisp_executions,
            "user_problems": user_problems,
            "mcp_servers": len(generated_servers)
        }

if __name__ == "__main__":
    dashboard = RedisMonitoringDashboard()
    dashboard.show_live_stats()
