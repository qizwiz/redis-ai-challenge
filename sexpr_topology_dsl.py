#!/usr/bin/env python3
"""
S-Expression Network Topology DSL - Revolutionary distributed actor architecture

S-expressions define network topology where each actor is a node and relationships
are expressed as nested structures. This creates self-describing network topologies
that can be introspected, modified, and evolved at runtime.
"""

import redis
import json
import time
from typing import Dict, Any, Optional, Union, Callable
from typing import List as ListType
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


# S-Expression AST for network topology
@dataclass
class SExpr:
    """Base S-expression node"""

    pass


@dataclass
class Symbol(SExpr):
    name: str


@dataclass
class List(SExpr):
    elements: ListType[SExpr]


@dataclass
class Literal(SExpr):
    value: Any


# Network topology primitives
@dataclass
class NetworkNode:
    name: str
    actor_type: str
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: ListType[str] = field(default_factory=list)
    endpoints: ListType[str] = field(default_factory=list)


@dataclass
class NetworkTopology:
    nodes: Dict[str, NetworkNode] = field(default_factory=dict)
    connections: ListType[tuple] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SExprParser:
    """Parse S-expressions into network topologies"""

    def __init__(self):
        self.pos = 0
        self.text = ""

    def parse(self, text: str) -> SExpr:
        """Parse S-expression text"""
        self.text = text.strip()
        self.pos = 0
        return self._parse_expr()


class TopologyBuilder:
    """Build network topology from S-expressions"""

    def __init__(self):
        self.topology = NetworkTopology()

    def build_from_sexpr(self, sexpr: SExpr) -> NetworkTopology:
        """Build topology from S-expression"""
        if isinstance(sexpr, List):
            return self._build_from_list(sexpr)
        else:
            raise ValueError("Topology must be a list expression")

    def _build_from_list(self, expr: "List") -> NetworkTopology:
        """Build from list expression"""
        if not expr.elements:
            return self.topology

        # First element should be topology command
        if not isinstance(expr.elements[0], Symbol):
            raise ValueError("First element must be a command symbol")

        command = expr.elements[0].name

        if command == "topology":
            return self._build_topology(expr.elements[1:])
        elif command == "cluster":
            return self._build_cluster(expr.elements[1:])
        elif command == "pipeline":
            return self._build_pipeline(expr.elements[1:])
        elif command in ["emergent-emacs-brain", "evolved-emacs-brain"]:
            # Handle emergent system topologies as generic topologies
            return self._build_topology(expr.elements[1:])
        else:
            raise ValueError(f"Unknown topology command: {command}")

    def _define_node(self, elements: ListType[SExpr]):
        """Define a network node"""
        if len(elements) < 2:
            return

        name = elements[0].name if isinstance(elements[0], Symbol) else str(elements[0])
        actor_type = (
            elements[1].name if isinstance(elements[1], Symbol) else str(elements[1])
        )

        config = {}
        dependencies = []

        # Process additional parameters
        i = 2
        while i < len(elements):
            if isinstance(elements[i], Symbol):
                if elements[i].name == ":config" and i + 1 < len(elements):
                    config = self._extract_config(elements[i + 1])
                    i += 2
                elif elements[i].name == ":depends" and i + 1 < len(elements):
                    dependencies = self._extract_dependencies(elements[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                i += 1

        self.topology.nodes[name] = NetworkNode(
            name=name, actor_type=actor_type, config=config, dependencies=dependencies
        )


class NetworkTopologyDSL:
    """Beautiful DSL for S-expression network topologies"""

    def __init__(self, redis_host="localhost", redis_port=6379):
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )
        self.parser = SExprParser()
        self.builder = TopologyBuilder()

    def parse_topology(self, sexpr_text: str) -> NetworkTopology:
        """Parse S-expression topology"""
        sexpr = self.parser.parse(sexpr_text)
        return self.builder.build_from_sexpr(sexpr)

    def deploy_topology(self, topology: NetworkTopology, namespace: str = "default"):
        """Deploy topology to Redis"""
        topology_data = {
            "nodes": {
                name: {
                    "name": node.name,
                    "actor_type": node.actor_type,
                    "config": node.config,
                    "dependencies": node.dependencies,
                    "endpoints": node.endpoints,
                }
                for name, node in topology.nodes.items()
            },
            "connections": topology.connections,
            "metadata": topology.metadata,
            "deployed_at": time.time(),
        }

        self.redis.set(f"topology:{namespace}", json.dumps(topology_data))

        # Deploy individual nodes
        for name, node in topology.nodes.items():
            node_key = f"actor:{namespace}:{name}:topology"
            self.redis.set(
                node_key,
                json.dumps(
                    {
                        "name": node.name,
                        "actor_type": node.actor_type,
                        "config": node.config,
                        "dependencies": node.dependencies,
                        "endpoints": node.endpoints,
                    }
                ),
            )

        return namespace

    def introspect_topology(
        self, namespace: str = "default"
    ) -> Optional[NetworkTopology]:
        """Introspect deployed topology"""
        topology_data = self.redis.get(f"topology:{namespace}")
        if not topology_data:
            return None

        data = json.loads(topology_data)
        topology = NetworkTopology()

        # Reconstruct nodes
        for name, node_data in data["nodes"].items():
            topology.nodes[name] = NetworkNode(
                name=node_data["name"],
                actor_type=node_data["actor_type"],
                config=node_data["config"],
                dependencies=node_data["dependencies"],
                endpoints=node_data["endpoints"],
            )

        topology.connections = data["connections"]
        topology.metadata = data["metadata"]

        return topology

    def evolve_topology(self, namespace: str, evolution_sexpr: str):
        """Evolve existing topology with S-expression"""
        current_topology = self.introspect_topology(namespace)
        if not current_topology:
            raise ValueError(f"No topology found for namespace: {namespace}")

        # Parse evolution expression
        evolution = self.parse_topology(evolution_sexpr)

        # Merge topologies
        current_topology.nodes.update(evolution.nodes)
        current_topology.connections.extend(evolution.connections)
        current_topology.metadata.update(evolution.metadata)

        # Redeploy
        return self.deploy_topology(current_topology, namespace)

    def visualize_topology(self, topology: NetworkTopology) -> str:
        """Generate ASCII visualization of topology"""
        lines = ["🕸️  NETWORK TOPOLOGY", "=" * 30, ""]

        # Show nodes
        lines.append("NODES:")
        for name, node in topology.nodes.items():
            deps = (
                f" (depends: {', '.join(node.dependencies)})"
                if node.dependencies
                else ""
            )
            lines.append(f"  📦 {name}: {node.actor_type}{deps}")
            if node.config:
                lines.append(f"     Config: {node.config}")

        lines.append("")

        # Show connections
        lines.append("CONNECTIONS:")
        for from_node, to_node in topology.connections:
            lines.append(f"  {from_node} → {to_node}")

        lines.append("")

        # Show supervision
        if "supervision" in topology.metadata:
            lines.append("SUPERVISION:")
            for supervisor, supervised in topology.metadata["supervision"].items():
                lines.append(f"  👑 {supervisor} supervises: {', '.join(supervised)}")

        return "\n".join(lines)


# Example beautiful topology definitions
EXAMPLE_TOPOLOGIES = {
    "simple_cluster": """
    (cluster message-processor facade-monitor state-tracker)
    """,
    "pipeline": """
    (pipeline input-validator message-processor output-formatter result-sender)
    """,
    "fault_tolerant_system": """
    (topology
      (node supervisor supervisor-actor :config (strategy one-for-all max-restarts 5))
      (node message-hub message-processor :depends (supervisor) 
            :config (buffer-size 1000 batch-size 10))
      (node facade-sync facade-monitor :depends (message-hub)
            :config (poll-interval 1.0 redis-key "emacs:live_facade"))
      (node state-machine state-tracker :depends (facade-sync)
            :config (persistence true checkpoint-interval 30))
      
      (connect supervisor message-hub)
      (connect message-hub facade-sync)
      (connect facade-sync state-machine)
      (connect state-machine message-hub)
      
      (supervise supervisor message-hub facade-sync state-machine))
    """,
    "distributed_brain": """
    (topology
      (node cortex coordinator-actor :config (decision-algorithm consensus))
      (node memory-left memory-actor :depends (cortex) :config (type semantic))
      (node memory-right memory-actor :depends (cortex) :config (type episodic))
      (node sensory visual-processor :config (input-stream emacs:change_events))
      (node motor action-executor :config (output-stream emacs:commands))
      
      (connect sensory cortex)
      (connect cortex memory-left)
      (connect cortex memory-right)
      (connect memory-left cortex)
      (connect memory-right cortex)
      (connect cortex motor)
      
      (supervise cortex memory-left memory-right sensory motor))
    """,
}


def demo_sexpr_topology():
    """Demo the S-expression topology DSL"""
    print("🕸️  S-Expression Network Topology DSL Demo")
    print("=" * 50)

    dsl = NetworkTopologyDSL()

    for name, sexpr_text in EXAMPLE_TOPOLOGIES.items():
        print(f"\n🔧 Building topology: {name}")
        print(f"S-Expression: {sexpr_text.strip()}")

        try:
            topology = dsl.parse_topology(sexpr_text)
            print(f"✅ Parsed successfully:")
            print(dsl.visualize_topology(topology))

            # Deploy to Redis
            namespace = f"demo-{name}"
            dsl.deploy_topology(topology, namespace)
            print(f"🚀 Deployed to Redis namespace: {namespace}")

        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n✅ S-Expression topology DSL demo complete")


if __name__ == "__main__":
    demo_sexpr_topology()
