#!/usr/bin/env python3
"""
REDIS PATTERNS COORDINATOR - Semantic Refactoring Extract
Split from generate_mcp_servers.py based on semantic analysis

🧠 SEMANTIC REFACTORING: Extracted Redis-specific coordination patterns
- Responsible for: Redis connections, data storage, stream coordination
- Bridges: redis_patterns concept (clean separation of concerns)
"""

import redis
import json
import time
from typing import Dict, List, Any

class RedisPatternCoordinator:
    """Handles Redis-specific coordination patterns"""
    
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        print("🔗 REDIS PATTERNS COORDINATOR ACTIVE")
    
    def register_servers_in_network(self, servers: List[Dict]) -> int:
        """Register generated servers in Redis network"""
        count = 0
        for server in servers:
            if server:
                # Register server in network
                self.r.sadd("generated_mcp_servers", server['server_file'])
                
                # Store server metadata
                self.r.hset(f"mcp_server:{server['agent']}", mapping={
                    "server_file": server['server_file'],
                    "agent": server['agent'],
                    "capabilities": json.dumps(server['capabilities']),
                    "generated_at": str(time.time()),
                    "status": "generated"
                })
                
                count += 1
        
        return count
    
    def create_coordination_workflows(self, servers: List[Dict]) -> int:
        """Create Redis-based coordination workflows"""
        workflows = []
        
        # Monitoring workflow
        monitoring_workflow = {
            "name": "buffer_monitoring_workflow",
            "description": "Coordinate buffer monitoring across all agents",
            "servers": [s['agent'] for s in servers if s],
            "frequency": "60s",
            "actions": ["monitor_buffer_state", "analyze_buffer_content"]
        }
        workflows.append(monitoring_workflow)
        
        # Relationship workflow
        relationship_workflow = {
            "name": "relationship_discovery_workflow", 
            "description": "Discover and maintain relationships between agents",
            "servers": [s['agent'] for s in servers if s],
            "frequency": "300s",
            "actions": ["discover_relationships", "coordinate_with_network"]
        }
        workflows.append(relationship_workflow)
        
        # Store workflows in Redis
        for workflow in workflows:
            self.r.hset(f"workflow:{workflow['name']}", mapping={
                "description": workflow['description'],
                "servers": json.dumps(workflow['servers']),
                "frequency": workflow['frequency'],
                "actions": json.dumps(workflow['actions']),
                "created_at": str(time.time())
            })
        
        return len(workflows)
    
    def get_active_buffer_agents(self) -> List[Dict]:
        """Get active buffer agents from Redis"""
        try:
            agent_names = list(self.r.smembers("active_buffer_agents"))
            
            agents = []
            for agent_name in agent_names:
                agent_info = self.r.hgetall(f"buffer_agent:{agent_name}")
                capabilities = self.r.hgetall(f"buffer_agent:{agent_name}:capabilities")
                
                agents.append({
                    "name": agent_name,
                    "info": agent_info,
                    "capabilities": capabilities
                })
            
            return agents
        except:
            return []
    
    def store_generation_result(self, result: Dict) -> None:
        """Store generation results in Redis"""
        # Convert nested dicts to strings for Redis storage
        serializable_result = {}
        for key, value in result.items():
            if isinstance(value, dict):
                serializable_result[key] = json.dumps(value)
            elif isinstance(value, bool):
                serializable_result[key] = str(value)
            else:
                serializable_result[key] = value
        
        self.r.hset("generation:result", mapping=serializable_result)
        
        # Update system status
        self.r.hset("living_knowledge_organism:status", mapping={
            "orchestration": "complete",
            "iteration": "complete", 
            "enhancement": "complete",
            "monitoring": "complete",
            "generation": "complete",
            "next_phase": "coordinate_through_redis",
            "timestamp": str(time.time())
        })