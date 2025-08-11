#!/usr/bin/env python3
"""
Evolution Engine - Live topology evolution based on learned patterns

This system continuously evolves the network topology based on real patterns
discovered from development workflows, creating a truly adaptive AI system.
"""

import redis
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import threading

from learning_engine import LearningEngine, Pattern
from sexpr_topology_dsl import NetworkTopologyDSL, NetworkTopology, NetworkNode
from facade_visibility_analyzer import FacadeAnalyzer


@dataclass
class EvolutionTrigger:
    """A trigger for topology evolution"""

    trigger_id: str
    trigger_type: str
    description: str
    conditions: Dict[str, Any]
    topology_changes: List[str]  # S-expression modifications
    confidence: float
    created_at: float


@dataclass
class TopologyMutation:
    """A mutation to apply to topology"""

    mutation_id: str
    mutation_type: str  # add_node, remove_node, modify_connection, etc.
    target: str  # what to mutate
    parameters: Dict[str, Any]
    rationale: str  # why this mutation
    confidence: float


class PatternEvolutionMapper:
    """Maps learned patterns to topology evolutions"""

    def __init__(self):
        self.evolution_rules = {
            "sequence": self._sequence_to_evolution,
            "coding_habit": self._coding_habit_to_evolution,
            "navigation_pattern": self._navigation_to_evolution,
            "workflow_pattern": self._workflow_to_evolution,
            "productivity_pattern": self._productivity_to_evolution,
        }

    def pattern_to_evolution(self, pattern: Pattern) -> List[TopologyMutation]:
        """Convert learned pattern to topology evolution"""
        if pattern.pattern_type in self.evolution_rules:
            return self.evolution_rules[pattern.pattern_type](pattern)
        return []

    def _sequence_to_evolution(self, pattern: Pattern) -> List[TopologyMutation]:
        """Convert sequence pattern to topology mutations"""
        mutations = []

        sequence = pattern.conditions.get("sequence", [])
        if len(sequence) >= 3 and pattern.confidence > 0.7:
            # High-confidence sequences get dedicated processing nodes
            sequence_name = "_".join(sequence[:3])

            mutations.append(
                TopologyMutation(
                    mutation_id=f"seq_processor_{sequence_name}",
                    mutation_type="add_node",
                    target="sequence_processors",
                    parameters={
                        "name": f"sequence-processor-{sequence_name}",
                        "actor_type": "sequence-processor",
                        "config": {
                            "sequence": sequence,
                            "confidence": pattern.confidence,
                            "optimization_target": "prediction_accuracy",
                        },
                        "dependencies": ["cortex"],
                    },
                    rationale=f"User frequently does: {' → '.join(sequence)}. Dedicated processor will predict and optimize this workflow.",
                    confidence=pattern.confidence,
                )
            )

        return mutations

    def _coding_habit_to_evolution(self, pattern: Pattern) -> List[TopologyMutation]:
        """Convert coding habit to topology mutations"""
        mutations = []

        buffer_type = pattern.conditions.get("buffer_type")
        command_sequence = pattern.conditions.get("command_sequence", [])

        if buffer_type and pattern.confidence > 0.6:
            # Create language-specific optimization node
            mutations.append(
                TopologyMutation(
                    mutation_id=f"lang_optimizer_{buffer_type}",
                    mutation_type="add_node",
                    target="language_optimizers",
                    parameters={
                        "name": f"{buffer_type}-optimizer",
                        "actor_type": "language-optimizer",
                        "config": {
                            "language": buffer_type,
                            "command_patterns": command_sequence,
                            "confidence": pattern.confidence,
                            "optimization_type": "coding_assistance",
                        },
                        "dependencies": ["cortex", "sensory"],
                    },
                    rationale=f"User has strong {buffer_type} coding patterns. Dedicated optimizer will provide better language-specific assistance.",
                    confidence=pattern.confidence,
                )
            )

        return mutations

    def _navigation_to_evolution(self, pattern: Pattern) -> List[TopologyMutation]:
        """Convert navigation pattern to topology mutations"""
        mutations = []

        from_buffer = pattern.conditions.get("from_buffer")
        to_buffer = pattern.conditions.get("to_buffer")

        if from_buffer and to_buffer and pattern.confidence > 0.8:
            # High-confidence navigation gets direct connection
            mutations.append(
                TopologyMutation(
                    mutation_id=f"nav_shortcut_{from_buffer}_{to_buffer}",
                    mutation_type="add_connection",
                    target="navigation_shortcuts",
                    parameters={
                        "from": f"buffer-{from_buffer}",
                        "to": f"buffer-{to_buffer}",
                        "connection_type": "navigation_shortcut",
                        "confidence": pattern.confidence,
                        "frequency": pattern.frequency,
                    },
                    rationale=f"User frequently navigates {from_buffer} → {to_buffer}. Direct connection will reduce latency.",
                    confidence=pattern.confidence,
                )
            )

        return mutations

    def _workflow_to_evolution(self, pattern: Pattern) -> List[TopologyMutation]:
        """Convert workflow pattern to topology mutations"""
        mutations = []

        session_type = pattern.conditions.get("session_type")
        phases = pattern.conditions.get("phases", [])

        if session_type and len(phases) >= 2 and pattern.confidence > 0.7:
            # Create workflow coordinator for this session type
            mutations.append(
                TopologyMutation(
                    mutation_id=f"workflow_coordinator_{session_type}",
                    mutation_type="add_node",
                    target="workflow_coordinators",
                    parameters={
                        "name": f"{session_type}-workflow-coordinator",
                        "actor_type": "workflow-coordinator",
                        "config": {
                            "session_type": session_type,
                            "phases": phases,
                            "estimated_duration": pattern.predictions.get(
                                "estimated_duration", 3600
                            ),
                            "optimization_target": "workflow_efficiency",
                        },
                        "dependencies": ["meta-cortex"],
                    },
                    rationale=f"User has consistent {session_type} workflow: {' → '.join(phases)}. Coordinator will optimize phase transitions.",
                    confidence=pattern.confidence,
                )
            )

        return mutations

    def _productivity_to_evolution(self, pattern: Pattern) -> List[TopologyMutation]:
        """Convert productivity pattern to topology mutations"""
        mutations = []

        productivity_level = pattern.conditions.get("productivity_level")
        expected_apm = pattern.predictions.get("expected_actions_per_minute", 0)

        if productivity_level == "high" and expected_apm > 4:
            # High productivity users get performance optimization
            mutations.append(
                TopologyMutation(
                    mutation_id="performance_optimizer_high_productivity",
                    mutation_type="modify_node",
                    target="cortex",
                    parameters={
                        "config_updates": {
                            "performance_mode": "high_throughput",
                            "batch_size": min(int(expected_apm * 2), 20),
                            "response_timeout": 500,  # Faster responses
                            "predictive_caching": True,
                        }
                    },
                    rationale=f"User shows high productivity ({expected_apm:.1f} actions/min). Optimizing for fast response times.",
                    confidence=pattern.confidence,
                )
            )

        elif productivity_level == "low" and expected_apm < 1:
            # Low productivity users get assistance optimization
            mutations.append(
                TopologyMutation(
                    mutation_id="assistance_optimizer_low_productivity",
                    mutation_type="modify_node",
                    target="cortex",
                    parameters={
                        "config_updates": {
                            "assistance_mode": "proactive",
                            "suggestion_threshold": 0.3,  # Lower threshold for suggestions
                            "context_window": 30,  # Longer context
                            "learning_rate": 1.2,  # Learn faster from limited data
                        }
                    },
                    rationale=f"User shows lower activity ({expected_apm:.1f} actions/min). Optimizing for proactive assistance.",
                    confidence=pattern.confidence,
                )
            )

        return mutations


class TopologyEvolver:
    """Evolves topology based on mutations"""

    def __init__(self, topology_dsl: NetworkTopologyDSL):
        self.topology_dsl = topology_dsl
        self.evolution_history = []
        self.active_mutations = {}

    def apply_mutations(
        self, mutations: List[TopologyMutation], namespace: str = "emergent-system"
    ) -> Optional[NetworkTopology]:
        """Apply mutations to create evolved topology"""

        # Get current topology
        current_topology = self.topology_dsl.introspect_topology(namespace)
        if not current_topology:
            print(f"❌ No topology found for namespace: {namespace}")
            return None

        # Apply mutations
        evolved_topology = self._clone_topology(current_topology)

        for mutation in mutations:
            try:
                self._apply_single_mutation(evolved_topology, mutation)
                self.active_mutations[mutation.mutation_id] = mutation
                print(f"✅ Applied: {mutation.rationale}")

            except Exception as e:
                print(f"❌ Failed to apply mutation {mutation.mutation_id}: {e}")

        return evolved_topology

    def generate_evolved_sexpr(self, topology: NetworkTopology) -> str:
        """Generate S-expression for evolved topology"""
        lines = ["(evolved-emacs-brain"]

        # Add nodes
        for name, node in topology.nodes.items():
            config_str = " ".join(f"{k} {v}" for k, v in node.config.items())
            deps_str = (
                f" :depends ({' '.join(node.dependencies)})"
                if node.dependencies
                else ""
            )
            config_part = f" :config ({config_str})" if config_str else ""

            lines.append(f"  (node {name} {node.actor_type}{deps_str}{config_part})")

        # Add connections
        for from_node, to_node in topology.connections:
            lines.append(f"  (connect {from_node} {to_node})")

        # Add supervision
        if "supervision" in topology.metadata:
            for supervisor, supervised in topology.metadata["supervision"].items():
                lines.append(f'  (supervise {supervisor} {" ".join(supervised)})')

        lines.append(")")

        return "\n".join(lines)


class EvolutionEngine:
    """Main evolution engine that coordinates learning and topology evolution"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

        # Components
        self.learning_engine = LearningEngine(redis_client)
        self.facade_analyzer = FacadeAnalyzer()
        self.topology_dsl = NetworkTopologyDSL()
        self.pattern_mapper = PatternEvolutionMapper()
        self.topology_evolver = TopologyEvolver(self.topology_dsl)

        # Evolution state
        self.evolution_history = []
        self.evolution_triggers = {}
        self.running = False

        # Evolution parameters
        self.min_pattern_confidence = 0.6
        self.evolution_interval = 60  # Evolve every 60 seconds
        self.max_mutations_per_cycle = 5

    def start_evolution_loop(self):
        """Start the continuous evolution loop"""
        print("🧬 Starting evolution loop...")

        self.running = True
        evolution_thread = threading.Thread(target=self._evolution_loop, daemon=True)
        evolution_thread.start()

        print("✅ Evolution loop started")

    def _execute_evolution_cycle(self):
        """Execute one evolution cycle"""
        print("🧬 Executing evolution cycle...")

        # 1. Get current facade state
        facade_state = self.facade_analyzer.get_live_facade()
        if not facade_state:
            print("⚠️ No facade state - skipping evolution")
            return

        # 2. Process observations for learning
        new_patterns = self.learning_engine.process_facade_observation(
            {
                "timestamp": facade_state.timestamp,
                "current_buffer": facade_state.current_buffer,
                "cursor_position": facade_state.cursor_position,
                "cursor_line": facade_state.cursor_line,
                "cursor_column": facade_state.cursor_column,
                "major_mode": facade_state.major_mode,
                "minor_modes": facade_state.minor_modes,
                "window_count": facade_state.window_count,
                "last_command": facade_state.last_command,
            }
        )

        if new_patterns:
            print(f"📚 Learned {len(new_patterns)} new patterns")

        # 3. Get high-confidence patterns
        all_patterns = self.learning_engine.get_discovered_patterns()
        evolution_worthy_patterns = [
            p for p in all_patterns if p.confidence >= self.min_pattern_confidence
        ]

        if not evolution_worthy_patterns:
            print("⚠️ No high-confidence patterns - no evolution needed")
            return

        print(f"🎯 Found {len(evolution_worthy_patterns)} evolution-worthy patterns")

        # 4. Generate mutations
        all_mutations = []
        for pattern in evolution_worthy_patterns:
            mutations = self.pattern_mapper.pattern_to_evolution(pattern)
            all_mutations.extend(mutations)

        if not all_mutations:
            print("⚠️ No mutations generated from patterns")
            return

        # Limit mutations per cycle
        selected_mutations = all_mutations[: self.max_mutations_per_cycle]

        print(f"🧬 Generated {len(selected_mutations)} mutations:")
        for mutation in selected_mutations:
            print(f"  • {mutation.rationale}")

        # 5. Apply mutations to create evolved topology
        evolved_topology = self.topology_evolver.apply_mutations(
            selected_mutations, "emergent-system"
        )

        if evolved_topology:
            # 6. Deploy evolved topology
            evolved_namespace = f"emergent-system-evolved-{int(time.time())}"
            self.topology_dsl.deploy_topology(evolved_topology, evolved_namespace)

            print(f"🚀 Deployed evolved topology: {evolved_namespace}")

            # 7. Record evolution
            evolution_record = {
                "timestamp": time.time(),
                "trigger_patterns": len(evolution_worthy_patterns),
                "mutations_applied": len(selected_mutations),
                "namespace": evolved_namespace,
                "success": True,
            }

            self.evolution_history.append(evolution_record)
            self._persist_evolution_record(evolution_record)

            print("✅ Evolution cycle complete")
        else:
            print("❌ Failed to create evolved topology")

    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get evolution progress summary"""
        learning_summary = self.learning_engine.get_learning_summary()

        return {
            "evolution_cycles": len(self.evolution_history),
            "active_mutations": len(self.topology_evolver.active_mutations),
            "learning_progress": learning_summary,
            "last_evolution": (
                self.evolution_history[-1] if self.evolution_history else None
            ),
            "evolution_running": self.running,
        }

    def stop_evolution(self):
        """Stop evolution loop"""
        self.running = False
        print("🛑 Evolution loop stopped")


def demo_evolution_engine():
    """Demo the evolution engine"""
    print("🧬 EVOLUTION ENGINE DEMO")
    print("=" * 35)

    # Setup
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    engine = EvolutionEngine(redis_client)

    try:
        # Start evolution
        engine.start_evolution_loop()

        print("🔄 Evolution engine running...")
        print("The system is now:")
        print("  • Learning patterns from facade observations")
        print("  • Converting patterns to topology mutations")
        print("  • Evolving network architecture in real-time")
        print("  • Deploying evolved topologies automatically")

        # Let it run for demo
        time.sleep(45)

        # Show evolution summary
        summary = engine.get_evolution_summary()
        print(f"\n🧬 Evolution Summary:")
        print(f"   Evolution cycles: {summary['evolution_cycles']}")
        print(f"   Active mutations: {summary['active_mutations']}")
        print(f"   Patterns learned: {summary['learning_progress']['total_patterns']}")
        print(
            f"   Learning confidence: {summary['learning_progress']['average_confidence']:.2f}"
        )

        if summary["last_evolution"]:
            last = summary["last_evolution"]
            print(f"   Last evolution: {last['mutations_applied']} mutations applied")

    except KeyboardInterrupt:
        print("\n🛑 Stopping evolution...")

    finally:
        engine.stop_evolution()
        print("✅ Evolution engine demo complete")


if __name__ == "__main__":
    demo_evolution_engine()
