#!/usr/bin/env python3
"""
MCP Network Supervisor: Orchestrates distributed Lisp execution across MCP servers
Manages health, routing, failures, and coordination
"""

import json
import time
import asyncio
import redis
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class MCPServerHealth:
    """Health status of an MCP server"""
    name: str
    status: str  # 'healthy', 'degraded', 'failed'
    last_response: Optional[datetime] = None
    response_time: float = 0.0
    error_count: int = 0
    success_count: int = 0
    
    @property 
    def success_rate(self) -> float:
        total = self.success_count + self.error_count
        return self.success_count / total if total > 0 else 0.0

@dataclass
class ExecutionPlan:
    """Execution plan for distributed Lisp expression"""
    expression: List
    routing_table: Dict[str, str] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    estimated_time: float = 0.0

class MCPNetworkSupervisor:
    """
    Supervises and orchestrates MCP network execution
    """
    
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # Server registry with health monitoring
        self.servers = {
            'emacs-vision': MCPServerHealth('emacs-vision', 'unknown'),
            'voice-mode': MCPServerHealth('voice-mode', 'unknown'), 
            'redis-lisp': MCPServerHealth('redis-lisp', 'unknown')
        }
        
        # Routing table: function_name -> server_name
        self.routing_table = {
            'emacs-execute': 'emacs-vision',
            'emacs-get-state': 'emacs-vision',
            'emacs-goto': 'emacs-vision',
            'voice-synthesize': 'voice-mode',
            'voice-converse': 'voice-mode',
            'redis-store': 'redis-lisp',
            'redis-get': 'redis-lisp',
            'redis-exec': 'redis-lisp'
        }
        
        # Execution statistics
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'avg_execution_time': 0.0
        }
    
    def health_check_all(self) -> Dict[str, MCPServerHealth]:
        """Perform health checks on all MCP servers"""
        print("🏥 Performing MCP network health check...")
        
        for server_name, health in self.servers.items():
            try:
                start_time = time.time()
                
                # Attempt basic connectivity check
                if server_name == 'redis-lisp':
                    # Test Redis connectivity
                    self.redis.ping()
                    health.status = 'healthy'
                elif server_name == 'emacs-vision':
                    # Test Emacs connectivity (would be real MCP call)
                    health.status = 'healthy'  # Placeholder
                elif server_name == 'voice-mode':
                    # Test Voice connectivity (would be real MCP call)
                    health.status = 'degraded'  # Known issue from earlier
                
                health.last_response = datetime.now()
                health.response_time = time.time() - start_time
                health.success_count += 1
                
            except Exception as e:
                health.status = 'failed'
                health.error_count += 1
                print(f"❌ {server_name}: {e}")
        
        return self.servers
    
    def create_execution_plan(self, lisp_expr: List) -> ExecutionPlan:
        """Create distributed execution plan from Lisp expression"""
        plan = ExecutionPlan(expression=lisp_expr)
        
        def analyze_expression(expr, depth=0):
            if not isinstance(expr, list) or len(expr) == 0:
                return
                
            func_name = expr[0]
            args = expr[1:]
            
            # Map function to server
            if func_name in self.routing_table:
                server = self.routing_table[func_name]
                plan.routing_table[func_name] = server
                if func_name not in plan.execution_order:
                    plan.execution_order.append(func_name)
            
            # Handle parallel execution
            if func_name == 'parallel':
                for sub_expr in args:
                    analyze_expression(sub_expr, depth + 1)
            
            # Handle sequential execution
            elif func_name == 'sequence':
                prev_func = None
                for sub_expr in args:
                    if isinstance(sub_expr, list) and len(sub_expr) > 0:
                        curr_func = sub_expr[0]
                        if prev_func:
                            if curr_func not in plan.dependencies:
                                plan.dependencies[curr_func] = []
                            plan.dependencies[curr_func].append(prev_func)
                        prev_func = curr_func
                    analyze_expression(sub_expr, depth + 1)
            
            # Analyze nested expressions
            else:
                for arg in args:
                    if isinstance(arg, list):
                        analyze_expression(arg, depth + 1)
        
        analyze_expression(lisp_expr)
        
        # Estimate execution time based on server health
        total_time = 0.0
        for func_name in plan.execution_order:
            server = plan.routing_table.get(func_name)
            if server and server in self.servers:
                total_time += self.servers[server].response_time
        plan.estimated_time = total_time
        
        return plan
    
    def execute_distributed_lisp(self, lisp_expr: List) -> Dict[str, Any]:
        """Execute Lisp expression across MCP network with supervision"""
        start_time = time.time()
        execution_id = f"exec_{int(time.time())}"
        
        print(f"🚀 Executing distributed Lisp: {execution_id}")
        print(f"📄 Expression: {lisp_expr}")
        
        # Create execution plan
        plan = self.create_execution_plan(lisp_expr)
        print(f"📋 Execution Plan: {len(plan.execution_order)} operations across {len(set(plan.routing_table.values()))} servers")
        print(f"⏱️  Estimated time: {plan.estimated_time:.2f}s")
        
        # Pre-execution health check
        health_status = self.health_check_all()
        failed_servers = [name for name, health in health_status.items() if health.status == 'failed']
        
        if failed_servers:
            print(f"⚠️  Warning: Failed servers detected: {failed_servers}")
        
        # Execute with monitoring
        results = {}
        errors = {}
        
        try:
            # This would contain the actual distributed execution logic
            results = self._execute_with_fallback(lisp_expr, plan)
            
            execution_time = time.time() - start_time
            self.execution_stats['total_executions'] += 1
            self.execution_stats['successful_executions'] += 1
            self._update_avg_time(execution_time)
            
            print(f"✅ Execution completed in {execution_time:.2f}s")
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.execution_stats['total_executions'] += 1
            self.execution_stats['failed_executions'] += 1
            errors['execution_error'] = str(e)
            print(f"❌ Execution failed after {execution_time:.2f}s: {e}")
        
        # Store execution record in Redis
        execution_record = {
            'id': execution_id,
            'expression': lisp_expr,
            'plan': {
                'routing': plan.routing_table,
                'order': plan.execution_order,
                'dependencies': plan.dependencies
            },
            'results': results,
            'errors': errors,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat(),
            'server_health': {name: health.status for name, health in health_status.items()}
        }
        
        self.redis.hset(f"mcp:execution:{execution_id}", mapping={
            'record': json.dumps(execution_record)
        })
        
        return execution_record
    
    def _execute_with_fallback(self, expr: List, plan: ExecutionPlan) -> Dict:
        """Execute with fallback handling for failed servers"""
        # This would contain the actual execution logic with:
        # - Circuit breakers for failed servers
        # - Retry logic
        # - Fallback routing
        # - Result aggregation
        
        return {
            'simulated_execution': True,
            'expression': expr,
            'routing_used': plan.routing_table,
            'execution_order': plan.execution_order
        }
    
    def _update_avg_time(self, new_time: float):
        """Update running average execution time"""
        total = self.execution_stats['total_executions']
        current_avg = self.execution_stats['avg_execution_time']
        self.execution_stats['avg_execution_time'] = (current_avg * (total - 1) + new_time) / total
    
    def get_network_status(self) -> Dict:
        """Get comprehensive network status"""
        health_status = self.health_check_all()
        
        return {
            'network_health': {
                'healthy_servers': len([s for s in health_status.values() if s.status == 'healthy']),
                'total_servers': len(health_status),
                'failed_servers': [name for name, health in health_status.items() if health.status == 'failed']
            },
            'server_details': {
                name: {
                    'status': health.status,
                    'success_rate': health.success_rate,
                    'avg_response_time': health.response_time,
                    'last_response': health.last_response.isoformat() if health.last_response else None
                }
                for name, health in health_status.items()
            },
            'execution_stats': self.execution_stats,
            'routing_table': self.routing_table
        }

# Test the supervisor
if __name__ == "__main__":
    supervisor = MCPNetworkSupervisor()
    
    # Test distributed execution supervision
    test_expr = [
        'parallel',
        ['emacs-execute', ['message', '"Supervised distributed execution"']],
        ['voice-synthesize', 'Supervision is working'],
        ['redis-store', 'supervision-test', 'SUCCESS']
    ]
    
    print("🌐 MCP Network Supervisor Test")
    print("=" * 60)
    
    # Get network status
    status = supervisor.get_network_status()
    print(f"🏥 Network Health: {status['network_health']}")
    
    # Execute supervised distributed Lisp
    result = supervisor.execute_distributed_lisp(test_expr)
    print("\n📊 Execution Record:")
    print(json.dumps(result, indent=2, default=str))