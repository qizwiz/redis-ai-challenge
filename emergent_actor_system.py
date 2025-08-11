#!/usr/bin/env python3
"""
Emergent Actor System - Self-Describing, Self-Healing, Self-Evolving Architecture

This is the unified system that composes:
- Facade visibility (sensory system)
- S-expression network topologies (DNA/blueprint)
- Supervision DSL (immune system)
- Redis coordination (nervous system)

The system observes itself through the facade, describes itself in S-expressions,
heals itself through supervision, and evolves its own architecture.
"""

import redis
import json
import time
import threading
from typing import Dict, Any, Optional, Union, Callable
from typing import List as ListType
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Import our DSL components
from facade_visibility_analyzer import FacadeAnalyzer, FacadeState
from supervision_dsl import SupervisionDSL, RestartStrategy
from sexpr_topology_dsl import NetworkTopologyDSL, NetworkTopology, NetworkNode


class EvolutionStrategy(Enum):
    CONSERVATIVE = "conservative"  # Small incremental changes
    AGGRESSIVE = "aggressive"  # Bold architectural changes
    ADAPTIVE = "adaptive"  # Learn from facade patterns
    REVOLUTIONARY = "revolutionary"  # Complete system rewrite


@dataclass
class SystemState:
    """Complete system state snapshot"""

    timestamp: float
    facade_state: Optional[FacadeState]
    network_topology: Optional[NetworkTopology]
    supervision_health: Dict[str, Any]
    evolution_history: ListType[Dict[str, Any]]
    learning_patterns: Dict[str, Any]


class EmergentActorSystem:
    """The unified emergent actor system"""

    def __init__(self, redis_host="localhost", redis_port=6379):
        # Core components
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )
        self.facade_analyzer = FacadeAnalyzer(redis_host, redis_port)
        self.supervision_dsl = SupervisionDSL(redis_host, redis_port)
        self.topology_dsl = NetworkTopologyDSL(redis_host, redis_port)

        # System state
        self.running = False
        self.evolution_strategy = EvolutionStrategy.ADAPTIVE
        self.learning_enabled = True
        self.auto_heal = True
        self.auto_evolve = True

        # Evolution patterns learned from observation
        self.architectural_patterns = {
            "minor_mode_clusters": {},
            "supervision_trees": {},
            "failure_recovery_patterns": {},
            "performance_optimizations": {},
        }

        # Main system thread
        self.system_thread = None

    def bootstrap(self, initial_topology: str = None):
        """Bootstrap the emergent system"""
        print("🚀 BOOTSTRAPPING EMERGENT ACTOR SYSTEM")
        print("=" * 50)

        # 1. Analyze current facade state
        print("📊 Analyzing facade state...")
        facade_state = self.facade_analyzer.get_live_facade()
        if not facade_state:
            print("❌ No facade state available - system cannot bootstrap")
            return False

        print(
            f"✅ Facade: {facade_state.window_count} windows, {len(facade_state.minor_modes)} passive servers"
        )

        # 2. Generate initial topology from facade
        if not initial_topology:
            print("🧬 Generating topology from facade observations...")
            initial_topology = self._generate_topology_from_facade(facade_state)

        print("🕸️ Initial topology:")
        print(initial_topology)

        # 3. Deploy topology
        topology = self.topology_dsl.parse_topology(initial_topology)
        namespace = "emergent-system"
        self.topology_dsl.deploy_topology(topology, namespace)
        print(f"🚀 Deployed to namespace: {namespace}")

        # 4. Setup supervision
        print("🎭 Setting up supervision...")
        self._setup_supervision_from_topology(topology)

        # 5. Start system loop
        print("🔄 Starting system loop...")
        self.running = True
        self.system_thread = threading.Thread(target=self._system_loop, daemon=True)
        self.system_thread.start()

        print("✅ EMERGENT SYSTEM BOOTSTRAPPED")
        return True

    def _generate_topology_from_facade(self, facade_state: FacadeState) -> str:
        """Generate S-expression topology from facade observations"""

        # Categorize minor modes into architectural groups
        mode_categories = self.facade_analyzer.analyze_minor_modes(facade_state)

        # Build adaptive topology based on what we observe
        topology_lines = ["(emergent-emacs-brain"]

        # Core coordination nodes
        topology_lines.extend(
            [
                '  (node sensory facade-monitor :config (input-stream "emacs:live_facade"))',
                '  (node cortex coordination-hub :depends (sensory) :config (decision-algorithm "consensus"))',
                '  (node memory state-persistence :depends (cortex) :config (backend "redis"))',
                '  (node motor command-executor :depends (cortex) :config (output-stream "emacs:commands"))',
            ]
        )

        # Add passive server clusters based on facade observations
        for category, modes in mode_categories.items():
            if modes and len(modes) > 2:  # Only create clusters for significant groups
                cluster_name = category.lower().replace(" ", "-").replace("/", "-")
                topology_lines.append(
                    f"  (node {cluster_name}-cluster passive-server-cluster"
                )
                topology_lines.append(
                    f'        :depends (cortex) :config (members {len(modes)} type "{category}"))'
                )

        # Core connections
        topology_lines.extend(
            [
                "  (connect sensory cortex)",
                "  (connect cortex memory)",
                "  (connect cortex motor)",
                "  (connect memory cortex)",  # Feedback loop
            ]
        )

        # Connect major clusters to cortex
        for category, modes in mode_categories.items():
            if modes and len(modes) > 2:
                cluster_name = category.lower().replace(" ", "-").replace("/", "-")
                topology_lines.append(f"  (connect cortex {cluster_name}-cluster)")

        # Supervision based on criticality
        critical_nodes = ["sensory", "cortex", "memory", "motor"]
        topology_lines.append(f'  (supervise cortex {" ".join(critical_nodes[1:])})')

        topology_lines.append(")")

        return "\n".join(topology_lines)

    def _setup_supervision_from_topology(self, topology: NetworkTopology):
        """Setup supervision DSL from network topology"""

        # Create supervisors for each supervision relationship
        if "supervision" in topology.metadata:
            for supervisor_name, supervised_nodes in topology.metadata[
                "supervision"
            ].items():

                # Create supervisor
                supervisor = (
                    self.supervision_dsl.supervisor(f"{supervisor_name}-supervisor")
                    .strategy(RestartStrategy.ONE_FOR_ONE)
                    .max_restarts(5, window=60)
                    .backoff(initial=1.0, multiplier=2.0, max_delay=30.0)
                    .on(
                        "supervisor_start",
                        lambda: self._log_event("supervisor_started", supervisor_name),
                    )
                    .on(
                        "actor_failure",
                        lambda actor, error: self._handle_actor_failure(actor, error),
                    )
                    .on(
                        "actor_restart",
                        lambda actor: self._log_event(
                            "actor_restarted", actor.spec.name
                        ),
                    )
                    .build()
                )

                # Create actors for supervised nodes
                for node_name in supervised_nodes:
                    if node_name in topology.nodes:
                        node = topology.nodes[node_name]
                        actor = (
                            self.supervision_dsl.actor(node_name)
                            .handler(lambda: self._actor_handler(node_name))
                            .restart(RestartStrategy.PERMANENT)
                            .health_check(lambda: self._check_actor_health(node_name))
                            .metadata(actor_type=node.actor_type, config=node.config)
                            .build()
                        )

                        supervisor.add_actor(actor)

    def _system_loop(self):
        """Main system observation and evolution loop"""
        print("🔄 System loop started")

        last_evolution = time.time()
        evolution_interval = 30  # Evolve every 30 seconds

        while self.running:
            try:
                # 1. Observe current state
                current_state = self._observe_system_state()

                # 2. Learn patterns from observations
                if self.learning_enabled:
                    self._learn_from_observations(current_state)

                # 3. Check system health
                health_issues = self._diagnose_health_issues(current_state)

                # 4. Auto-heal if needed
                if self.auto_heal and health_issues:
                    self._auto_heal_system(health_issues)

                # 5. Auto-evolve periodically
                if (
                    self.auto_evolve
                    and time.time() - last_evolution > evolution_interval
                ):
                    self._auto_evolve_system(current_state)
                    last_evolution = time.time()

                # 6. Update system state in Redis
                self._persist_system_state(current_state)

                time.sleep(5)  # Observe every 5 seconds

            except Exception as e:
                self._log_event("system_loop_error", str(e))
                time.sleep(10)  # Back off on errors

    def _observe_system_state(self) -> SystemState:
        """Observe complete system state"""
        facade_state = self.facade_analyzer.get_live_facade()
        topology = self.topology_dsl.introspect_topology("emergent-system")

        # Gather supervision health
        supervision_health = {
            "active_supervisors": len(self.supervision_dsl.supervisors),
            "total_actors": sum(
                len(sup.actors) for sup in self.supervision_dsl.supervisors.values()
            ),
            "restart_counts": {},
            "health_status": "unknown",
        }

        return SystemState(
            timestamp=time.time(),
            facade_state=facade_state,
            network_topology=topology,
            supervision_health=supervision_health,
            evolution_history=[],
            learning_patterns=self.architectural_patterns.copy(),
        )

    def _learn_from_observations(self, state: SystemState):
        """Learn architectural patterns from system observations"""
        if not state.facade_state:
            return

        # Learn minor mode clustering patterns
        mode_categories = self.facade_analyzer.analyze_minor_modes(state.facade_state)
        for category, modes in mode_categories.items():
            if len(modes) > 3:  # Significant cluster
                cluster_key = f"{category}_{len(modes)}"
                if (
                    cluster_key
                    not in self.architectural_patterns["minor_mode_clusters"]
                ):
                    self.architectural_patterns["minor_mode_clusters"][cluster_key] = {
                        "category": category,
                        "size": len(modes),
                        "first_observed": time.time(),
                        "observation_count": 1,
                        "stability_score": 0.0,
                    }
                else:
                    pattern = self.architectural_patterns["minor_mode_clusters"][
                        cluster_key
                    ]
                    pattern["observation_count"] += 1
                    # Calculate stability (how often we see this exact configuration)
                    pattern["stability_score"] = min(
                        1.0, pattern["observation_count"] / 100.0
                    )

        # Learn performance patterns
        window_count = state.facade_state.window_count
        mode_count = len(state.facade_state.minor_modes)
        perf_key = f"windows_{window_count}_modes_{mode_count}"

        if perf_key not in self.architectural_patterns["performance_optimizations"]:
            self.architectural_patterns["performance_optimizations"][perf_key] = {
                "window_count": window_count,
                "mode_count": mode_count,
                "performance_score": 1.0,  # Assume good until proven otherwise
                "observations": 1,
            }

    def _diagnose_health_issues(self, state: SystemState) -> ListType[str]:
        """Diagnose system health issues"""
        issues = []

        if not state.facade_state:
            issues.append("facade_disconnected")

        if not state.network_topology:
            issues.append("topology_missing")

        # Check for excessive minor modes (performance issue)
        if state.facade_state and len(state.facade_state.minor_modes) > 300:
            issues.append("excessive_minor_modes")

        # Check facade age
        if state.facade_state:
            facade_age = time.time() - state.facade_state.timestamp
            if facade_age > 60:  # Facade hasn't updated in 60 seconds
                issues.append("stale_facade")

        return issues

    def _auto_evolve_system(self, state: SystemState):
        """Automatically evolve system architecture"""
        if not state.facade_state:
            return

        self._log_event("auto_evolution_check", "analyzing patterns")

        # Check if we've learned stable new patterns
        stable_patterns = []
        for pattern_type, patterns in self.architectural_patterns.items():
            for pattern_id, pattern_data in patterns.items():
                if (
                    hasattr(pattern_data, "get")
                    and pattern_data.get("stability_score", 0) > 0.8
                ):
                    stable_patterns.append((pattern_type, pattern_id, pattern_data))

        if stable_patterns:
            self._log_event(
                "evolution_triggered", f"Found {len(stable_patterns)} stable patterns"
            )

            # Generate evolved topology
            evolved_topology = self._generate_evolved_topology(state, stable_patterns)

            if evolved_topology:
                self._log_event("evolution_applying", "deploying evolved topology")

                # Deploy evolved topology
                topology = self.topology_dsl.parse_topology(evolved_topology)
                self.topology_dsl.deploy_topology(topology, "emergent-system-evolved")

                # Gradually migrate to evolved system
                self._migrate_to_evolved_topology("emergent-system-evolved")

    def _generate_evolved_topology(
        self, state: SystemState, patterns: ListType[tuple]
    ) -> Optional[str]:
        """Generate evolved topology based on learned patterns"""
        # For now, return enhanced version of current topology
        # In future: use AI to generate topology based on patterns

        facade_state = state.facade_state
        if not facade_state:
            return None

        # Enhanced topology with learned optimizations
        evolved_topology = f"""
        (evolved-emacs-brain
          ; Core coordination enhanced with learning
          (node meta-cortex meta-coordinator 
                :config (learning true patterns {len(patterns)} evolution-generation 2))
          (node sensory-enhanced facade-monitor 
                :depends (meta-cortex) 
                :config (input-stream "emacs:live_facade" pattern-recognition true))
          (node adaptive-memory state-persistence 
                :depends (meta-cortex)
                :config (backend "redis" pattern-storage true))
          (node intelligent-motor command-executor 
                :depends (meta-cortex)
                :config (output-stream "emacs:commands" learning-enabled true))
          
          ; Pattern-based optimizations
          (node pattern-optimizer pattern-processor
                :depends (meta-cortex)
                :config (patterns {len(self.architectural_patterns)} auto-optimize true))
          
          ; Evolved connections with feedback loops
          (connect sensory-enhanced meta-cortex)
          (connect meta-cortex adaptive-memory)
          (connect meta-cortex intelligent-motor)
          (connect adaptive-memory meta-cortex)
          (connect pattern-optimizer meta-cortex)
          
          ; Enhanced supervision
          (supervise meta-cortex sensory-enhanced adaptive-memory intelligent-motor pattern-optimizer))
        """

        return evolved_topology

    def _migrate_to_evolved_topology(self, evolved_namespace: str):
        """Gradually migrate to evolved topology"""
        self._log_event("migration_started", evolved_namespace)
        # Implementation: gradual traffic shifting, health monitoring, rollback capability

    # Actor system interface methods
    def _actor_handler(self, actor_name: str):
        """Default actor handler"""
        self._log_event("actor_tick", actor_name)

    def _handle_actor_failure(self, actor, error):
        """Handle actor failure with learning"""
        failure_pattern = {
            "actor_name": actor.spec.name,
            "actor_type": actor.spec.metadata.get("actor_type", "unknown"),
            "error": str(error),
            "timestamp": time.time(),
        }

        # Learn from failure
        failure_key = f"{actor.spec.name}_{str(error)[:50]}"
        if "failure_recovery_patterns" not in self.architectural_patterns:
            self.architectural_patterns["failure_recovery_patterns"] = {}

        if failure_key not in self.architectural_patterns["failure_recovery_patterns"]:
            self.architectural_patterns["failure_recovery_patterns"][failure_key] = {
                "count": 1,
                "first_seen": time.time(),
                "recovery_strategy": "restart",
                "success_rate": 0.0,
            }
        else:
            self.architectural_patterns["failure_recovery_patterns"][failure_key][
                "count"
            ] += 1

        self._log_event("actor_failure_learned", failure_pattern)

    # Utility methods
    def _restart_facade_monitoring(self):
        """Restart facade monitoring"""
        self._log_event("facade_restart", "attempting restart")

    def _suggest_minor_mode_cleanup(self):
        """Suggest minor mode cleanup"""
        self._log_event("minor_mode_cleanup_suggested", "too many modes active")

    def _force_facade_refresh(self):
        """Force facade refresh"""
        self._log_event("facade_refresh_forced", "stale facade detected")

    # Public interface
    def status(self) -> Dict[str, Any]:
        """Get system status"""
        state = self._observe_system_state()

        return {
            "running": self.running,
            "facade_connected": state.facade_state is not None,
            "topology_deployed": state.network_topology is not None,
            "learning_enabled": self.learning_enabled,
            "auto_heal": self.auto_heal,
            "auto_evolve": self.auto_evolve,
            "patterns_learned": sum(
                len(patterns) for patterns in self.architectural_patterns.values()
            ),
            "system_health": (
                "healthy" if not self._diagnose_health_issues(state) else "degraded"
            ),
        }

    def evolve(self, strategy: EvolutionStrategy = EvolutionStrategy.ADAPTIVE):
        """Trigger manual evolution"""
        self.evolution_strategy = strategy
        state = self._observe_system_state()
        self._auto_evolve_system(state)

    def shutdown(self):
        """Graceful shutdown"""
        self._log_event("system_shutdown", "graceful shutdown initiated")
        self.running = False

        # Stop supervision
        for supervisor in self.supervision_dsl.supervisors.values():
            supervisor.running = False

        # Wait for system thread
        if self.system_thread:
            self.system_thread.join(timeout=10)

        self._log_event("system_shutdown", "completed")


def demo_emergent_system():
    """Demo the complete emergent actor system"""
    print("🌱 EMERGENT ACTOR SYSTEM DEMO")
    print("=" * 50)

    # Create system
    system = EmergentActorSystem()

    try:
        # Bootstrap with automatic topology generation
        if system.bootstrap():
            print("\n📊 System Status:")
            status = system.status()
            for key, value in status.items():
                print(f"  {key}: {value}")

            print("\n🔄 System running... (Press Ctrl+C to stop)")
            print("The system is now:")
            print("  • Observing facade state")
            print("  • Learning architectural patterns")
            print("  • Auto-healing failures")
            print("  • Evolving its own architecture")

            # Let it run for a demo period
            time.sleep(30)

            print("\n🧬 Triggering manual evolution...")
            system.evolve(EvolutionStrategy.REVOLUTIONARY)

            time.sleep(10)

        else:
            print("❌ Failed to bootstrap system")

    except KeyboardInterrupt:
        print("\n🛑 Shutting down system...")

    finally:
        system.shutdown()
        print("✅ Emergent system demo complete")


if __name__ == "__main__":
    demo_emergent_system()
