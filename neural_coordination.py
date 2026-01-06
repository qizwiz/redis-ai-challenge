#!/usr/bin/env python3
"""
NEURAL COORDINATION - Fast Agent Coordination Using FANN
Sub-100ms coordination decisions through ephemeral neural networks
Built on proven FANN algorithms with modern Python integration
"""

import time
import numpy as np
import json
import redis
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Use pyfann if available, fallback to numpy simulation
try:
    import pyfann
    FANN_AVAILABLE = True
except ImportError:
    FANN_AVAILABLE = False
    print("⚠️  FANN not available - using numpy simulation")

class CoordinationNetworkType(Enum):
    SIMPLE_ALLOCATION = "simple_allocation"
    PRIORITY_ROUTING = "priority_routing" 
    LOAD_BALANCING = "load_balancing"
    FAULT_RECOVERY = "fault_recovery"

@dataclass
class Agent:
    id: str
    capabilities: List[str]
    current_load: float
    availability: bool
    performance_history: List[float]

@dataclass
class CoordinationTask:
    task_id: str
    requirements: List[str]
    priority: float
    estimated_effort: float
    deadline: Optional[float] = None

class FANNCoordinator:
    """Fast neural network coordination for agent swarms"""
    
    def __init__(self, redis_client):
        self.r = redis_client
        self.coordination_networks = {}
        self.performance_cache = {}
        
        print("🧠 FANN COORDINATOR INITIALIZED")
        print(f"   FANN Available: {'✅' if FANN_AVAILABLE else '❌ (using numpy simulation)'}")
    
    def create_coordination_network(self, network_type: CoordinationNetworkType, 
                                   input_size: int, output_size: int) -> str:
        """Create ephemeral neural network for specific coordination task"""
        
        network_id = f"{network_type.value}_{int(time.time() * 1000)}"
        
        # Calculate hidden layer size
        hidden_size = max(4, min(input_size + output_size, 16))
        
        if FANN_AVAILABLE:
            # Create FANN network
            ann = pyfann.libfann.neural_net()
            
            # Simple 3-layer network optimized for speed
            ann.create_standard_array([input_size, hidden_size, output_size])
            
            # Fast training parameters
            ann.set_activation_function_hidden(pyfann.SIGMOID_SYMMETRIC)
            ann.set_activation_function_output(pyfann.SIGMOID_SYMMETRIC)
            ann.set_training_algorithm(pyfann.TRAIN_QUICKPROP)
            
            self.coordination_networks[network_id] = {
                'network': ann,
                'type': network_type,
                'created_at': time.time(),
                'input_size': input_size,
                'output_size': output_size,
                'uses': 0
            }
        else:
            # Numpy simulation of neural network
            self.coordination_networks[network_id] = {
                'network': self._create_numpy_network(input_size, hidden_size, output_size),
                'type': network_type,
                'created_at': time.time(),
                'input_size': input_size,
                'output_size': output_size,
                'uses': 0
            }
        
        print(f"🚀 Created coordination network: {network_id}")
        return network_id
    
    def _create_numpy_network(self, input_size: int, hidden_size: int, output_size: int):
        """Create numpy-based neural network simulation"""
        return {
            'w1': np.random.randn(input_size, hidden_size) * 0.5,
            'b1': np.zeros(hidden_size),
            'w2': np.random.randn(hidden_size, output_size) * 0.5,
            'b2': np.zeros(output_size)
        }
    
    def _numpy_forward(self, network, inputs):
        """Forward pass through numpy network"""
        x = np.array(inputs)
        
        # Hidden layer
        z1 = np.dot(x, network['w1']) + network['b1']
        a1 = np.tanh(z1)  # Activation function
        
        # Output layer
        z2 = np.dot(a1, network['w2']) + network['b2']
        a2 = np.tanh(z2)  # Output activation
        
        return a2
    
    def coordinate_agents_fast(self, task: CoordinationTask, 
                              agents: List[Agent]) -> Dict[str, Any]:
        """Sub-100ms agent coordination using neural networks"""
        
        start_time = time.time()
        
        # Step 1: Determine optimal network type for task
        network_type = self._select_network_type(task, agents)
        
        # Step 2: Create or reuse coordination network
        input_size = len(agents) + 4  # agents + task features
        output_size = len(agents)     # assignment scores per agent
        
        network_id = self.create_coordination_network(network_type, input_size, output_size)
        
        # Step 3: Prepare inputs for neural network
        network_inputs = self._prepare_coordination_inputs(task, agents)
        
        # Step 4: Fast neural coordination decision
        coordination_scores = self._run_coordination_network(network_id, network_inputs)
        
        # Step 5: Generate optimal assignment
        assignment = self._generate_assignment(agents, coordination_scores, task)
        
        # Step 6: Cleanup ephemeral network (if single-use)
        if self.coordination_networks[network_id]['uses'] > 10:
            self._destroy_network(network_id)
        
        coordination_time = (time.time() - start_time) * 1000  # milliseconds
        
        result = {
            'assignment': assignment,
            'coordination_time_ms': coordination_time,
            'network_type': network_type.value,
            'network_id': network_id,
            'confidence': self._calculate_confidence(coordination_scores),
            'task_id': task.task_id
        }
        
        print(f"⚡ FAST COORDINATION: {coordination_time:.1f}ms")
        print(f"   Network: {network_type.value}")
        print(f"   Assignment: {len(assignment)} agents")
        
        return result
    
    def _select_network_type(self, task: CoordinationTask, 
                           agents: List[Agent]) -> CoordinationNetworkType:
        """Select optimal network architecture for coordination task"""
        
        # Simple heuristics for network type selection
        if task.priority > 0.8:
            return CoordinationNetworkType.PRIORITY_ROUTING
        elif len(agents) > 10:
            return CoordinationNetworkType.LOAD_BALANCING
        elif any(not agent.availability for agent in agents):
            return CoordinationNetworkType.FAULT_RECOVERY
        else:
            return CoordinationNetworkType.SIMPLE_ALLOCATION
    
    def _prepare_coordination_inputs(self, task: CoordinationTask, 
                                   agents: List[Agent]) -> List[float]:
        """Convert task and agent data to neural network inputs"""
        
        inputs = []
        
        # Task features (normalized)
        inputs.extend([
            task.priority,                              # Already [0,1]
            min(1.0, task.estimated_effort / 10.0),   # Normalize effort to [0,1]
            min(1.0, len(task.requirements) / 10.0),  # Normalize requirement count
            1.0 if task.deadline else 0.0             # Already [0,1]
        ])
        
        # Agent features (normalized)
        for agent in agents:
            agent_score = (
                len(agent.capabilities) / 10.0 +           # capability breadth
                (1.0 - agent.current_load) +               # availability
                (1.0 if agent.availability else 0.0) +     # online status
                np.mean(agent.performance_history[-5:])    # recent performance
            ) / 4.0
            
            inputs.append(min(1.0, max(0.0, agent_score)))  # Normalize to [0,1]
        
        return inputs
    
    def _run_coordination_network(self, network_id: str, inputs: List[float]) -> List[float]:
        """Execute neural network for coordination decision"""
        
        network_data = self.coordination_networks[network_id]
        network_data['uses'] += 1
        
        if FANN_AVAILABLE:
            # Run FANN network
            outputs = network_data['network'].run(inputs)
        else:
            # Run numpy simulation
            outputs = self._numpy_forward(network_data['network'], inputs)
            outputs = outputs.tolist()
        
        return outputs
    
    def _generate_assignment(self, agents: List[Agent], scores: List[float], 
                           task: CoordinationTask) -> Dict[str, Dict[str, Any]]:
        """Generate agent assignments from neural network scores"""
        
        assignment = {}
        
        # Sort agents by coordination score
        agent_scores = list(zip(agents, scores))
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Assign based on task requirements and scores
        assigned_agents = 0
        max_agents = min(len(task.requirements), len(agents))
        
        for agent, score in agent_scores[:max_agents]:
            if agent.availability and agent.current_load < 0.8:
                assignment[agent.id] = {
                    'score': float(score),
                    'role': task.requirements[assigned_agents] if assigned_agents < len(task.requirements) else 'support',
                    'estimated_effort': task.estimated_effort / max_agents,
                    'priority': task.priority
                }
                assigned_agents += 1
        
        return assignment
    
    def _calculate_confidence(self, scores: List[float]) -> float:
        """Calculate confidence in coordination decision"""
        
        if not scores:
            return 0.0
        
        # High confidence when scores are clearly differentiated
        score_variance = np.var(scores)
        max_score = max(scores)
        
        confidence = min(1.0, score_variance * 2 + max_score * 0.5)
        return confidence
    
    def _destroy_network(self, network_id: str):
        """Destroy ephemeral coordination network"""
        
        if network_id in self.coordination_networks:
            network_data = self.coordination_networks[network_id]
            
            # Store performance metrics before destruction
            self._record_network_performance(network_id, network_data)
            
            del self.coordination_networks[network_id]
            print(f"🗑️  Destroyed ephemeral network: {network_id}")
    
    def _record_network_performance(self, network_id: str, network_data: Dict[str, Any]):
        """Record network performance for learning"""
        
        performance_data = {
            'network_type': network_data['type'].value,
            'lifetime_seconds': time.time() - network_data['created_at'],
            'total_uses': network_data['uses'],
            'avg_uses_per_second': network_data['uses'] / max(1, time.time() - network_data['created_at'])
        }
        
        # Store in Redis for analysis
        self.r.hset(f"neural_coord:performance:{network_id}", mapping=performance_data)
    
    def get_coordination_stats(self) -> Dict[str, Any]:
        """Get neural coordination performance statistics"""
        
        active_networks = len(self.coordination_networks)
        total_uses = sum(net['uses'] for net in self.coordination_networks.values())
        
        network_types = {}
        for net in self.coordination_networks.values():
            net_type = net['type'].value
            network_types[net_type] = network_types.get(net_type, 0) + 1
        
        return {
            'active_networks': active_networks,
            'total_coordination_calls': total_uses,
            'network_types': network_types,
            'fann_available': FANN_AVAILABLE
        }

class CoordinationDemo:
    """Demonstrate neural coordination capabilities"""
    
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.coordinator = FANNCoordinator(self.r)
        
        print("🎯 NEURAL COORDINATION DEMO INITIALIZED")
    
    def create_demo_agents(self) -> List[Agent]:
        """Create demo agents with varying capabilities"""
        
        agents = [
            Agent("agent_1", ["coding", "testing"], 0.3, True, [0.9, 0.8, 0.9]),
            Agent("agent_2", ["analysis", "documentation"], 0.1, True, [0.7, 0.8, 0.9]),
            Agent("agent_3", ["deployment", "monitoring"], 0.6, True, [0.8, 0.7, 0.8]),
            Agent("agent_4", ["security", "review"], 0.2, False, [0.9, 0.9, 0.8]),
            Agent("agent_5", ["optimization", "testing"], 0.8, True, [0.6, 0.7, 0.8])
        ]
        
        return agents
    
    def create_demo_task(self) -> CoordinationTask:
        """Create demo coordination task"""
        
        return CoordinationTask(
            task_id="demo_task_001",
            requirements=["coding", "testing", "review"],
            priority=0.7,
            estimated_effort=8.0,
            deadline=time.time() + 3600  # 1 hour
        )
    
    def run_coordination_demo(self):
        """Run complete neural coordination demonstration"""
        
        print("\n🚀 RUNNING NEURAL COORDINATION DEMO")
        print("=" * 50)
        
        # Create demo scenario
        agents = self.create_demo_agents()
        task = self.create_demo_task()
        
        print(f"📋 Task: {task.task_id}")
        print(f"   Requirements: {task.requirements}")
        print(f"   Priority: {task.priority}")
        print(f"   Available agents: {len(agents)}")
        
        # Run neural coordination
        start_time = time.time()
        result = self.coordinator.coordinate_agents_fast(task, agents)
        total_time = (time.time() - start_time) * 1000
        
        # Display results
        print(f"\n✅ COORDINATION COMPLETE")
        print(f"   Total time: {total_time:.1f}ms")
        print(f"   Neural time: {result['coordination_time_ms']:.1f}ms")
        print(f"   Network type: {result['network_type']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        
        print(f"\n📊 AGENT ASSIGNMENTS:")
        for agent_id, assignment in result['assignment'].items():
            print(f"   {agent_id}: {assignment['role']} (score: {assignment['score']:.3f})")
        
        # Show coordination stats
        stats = self.coordinator.get_coordination_stats()
        print(f"\n📈 COORDINATION STATS:")
        print(f"   Active networks: {stats['active_networks']}")
        print(f"   Total uses: {stats['total_coordination_calls']}")
        print(f"   FANN available: {stats['fann_available']}")
        
        return result

if __name__ == "__main__":
    demo = CoordinationDemo()
    demo.run_coordination_demo()