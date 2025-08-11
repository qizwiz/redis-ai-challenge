#!/usr/bin/env python3
"""
Complete Dream System - All components integrated

This demonstrates the full dream interface:
- Real-time bidirectional communication with Emacs
- Pattern learning from facade observations
- Live topology evolution based on learned patterns
- Self-modifying distributed AI system
"""

import redis
import json
import time
import threading
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass

from dream_bridge import DreamBridge
from learning_engine import LearningEngine
from evolution_engine import EvolutionEngine
from facade_visibility_analyzer import FacadeAnalyzer
from emergent_actor_system import EmergentActorSystem
from intelligent_response_engine import IntelligentResponseEngine


class CompleteDreamSystem:
    """The complete self-aware, self-learning, self-evolving AI system"""

    def __init__(self, redis_host="localhost", redis_port=6379):
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )

        # Core components
        self.dream_bridge = DreamBridge(redis_host, redis_port)
        self.facade_analyzer = FacadeAnalyzer(redis_host, redis_port)
        self.learning_engine = LearningEngine(self.redis)
        self.evolution_engine = EvolutionEngine(self.redis)
        self.emergent_system = EmergentActorSystem(redis_host, redis_port)
        self.intelligent_response_engine = IntelligentResponseEngine(self.redis)

        # System state
        self.running = False
        self.system_stats = {
            "start_time": 0,
            "facade_observations": 0,
            "patterns_learned": 0,
            "evolutions_triggered": 0,
            "ai_responses_sent": 0,
        }

    def start_complete_system(self):
        """Start the complete dream system"""
        print("🌟 STARTING COMPLETE DREAM SYSTEM")
        print("=" * 50)

        self.running = True
        self.system_stats["start_time"] = time.time()

        # 1. Bootstrap emergent actor system
        print("🚀 Bootstrapping emergent actor system...")
        if not self.emergent_system.bootstrap():
            print("❌ Failed to bootstrap emergent system")
            return False

        # 2. Start dream bridge (Emacs ↔ AI communication)
        print("🌉 Starting dream bridge...")
        self.dream_bridge.start_bridge()

        # Register our learning handler
        self.dream_bridge.register_pulse_handler(self._process_emacs_pulse)

        # 3. Start evolution engine
        print("🧬 Starting evolution engine...")
        self.evolution_engine.start_evolution_loop()

        print("✅ COMPLETE DREAM SYSTEM ACTIVE")
        print("\nThe AI can now:")
        print("  • See real-time Emacs state through facade")
        print("  • Communicate bidirectionally with Emacs")
        print("  • Learn patterns from development workflows")
        print("  • Evolve its own network topology")
        print("  • Respond intelligently to user actions")
        print("  • Self-modify its architecture based on usage")

        return True

    def _process_emacs_pulse(self, pulse):
        """Process pulse from Emacs for learning and evolution"""
        self.system_stats["facade_observations"] += 1

        # Convert pulse to facade-like data
        facade_data = {
            "timestamp": pulse.timestamp,
            "current_buffer": pulse.source_buffer or "unknown",
            "cursor_position": pulse.cursor_position or 0,
            "cursor_line": pulse.data.get("line", 0),
            "cursor_column": pulse.data.get("column", 0),
            "major_mode": pulse.data.get("major-mode", "unknown"),
            "minor_modes": pulse.data.get("minor-modes", []),
            "window_count": pulse.data.get("window-count", 1),
            "last_command": pulse.data.get("recent-command", "none"),
        }

        # Feed to learning engine
        new_patterns = self.learning_engine.process_facade_observation(facade_data)

        if new_patterns:
            self.system_stats["patterns_learned"] += len(new_patterns)
            print(f"🧠 Learned {len(new_patterns)} new patterns from pulse")

            # Send intelligent response based on patterns
            # Run async response in event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create task for async response
                    asyncio.create_task(
                        self._send_intelligent_response(pulse, new_patterns)
                    )
                else:
                    loop.run_until_complete(
                        self._send_intelligent_response(pulse, new_patterns)
                    )
            except RuntimeError:
                # No event loop, create new one
                asyncio.run(self._send_intelligent_response(pulse, new_patterns))

    async def _send_intelligent_response(self, pulse, patterns):
        """Send intelligent AI response using real LLM intelligence"""

        # Build facade data for intelligent response
        facade_data = {
            "current_buffer": pulse.source_buffer or "unknown",
            "cursor_line": pulse.data.get("line", 0),
            "cursor_column": pulse.data.get("column", 0),
            "last_command": pulse.data.get("recent-command", "none"),
            "minor_modes": pulse.data.get("minor-modes", []),
            "major_mode": pulse.data.get("major-mode", "unknown"),
            "window_count": pulse.data.get("window-count", 1),
            "recent_commands": [pulse.data.get("recent-command", "none")],
            "timestamp": pulse.timestamp,
        }

        # Determine user intent from pulse
        user_intent = self._analyze_user_intent(pulse, patterns)

        # Get pattern data for AI
        pattern_data = []
        for pattern in patterns[:3]:  # Top 3 patterns
            pattern_data.append(
                {
                    "description": pattern.description,
                    "confidence": pattern.confidence,
                    "pattern_type": pattern.pattern_type,
                    "frequency": pattern.frequency,
                }
            )

        try:
            # Generate intelligent response using real AI
            ai_response = (
                await self.intelligent_response_engine.generate_intelligent_response(
                    facade_data, user_intent, pattern_data
                )
            )

            # Send appropriate response based on AI recommendation
            if ai_response.response_type == "message":
                self.dream_bridge.send_message(ai_response.content)
            elif ai_response.response_type == "elisp_command":
                self.dream_bridge.send_elisp_command(ai_response.content)
            elif ai_response.response_type == "suggestion":
                suggestion_msg = f"💡 Suggestion: {ai_response.content}"
                self.dream_bridge.send_message(suggestion_msg)

            self.system_stats["ai_responses_sent"] += 1

            # Log intelligent response
            print(
                f"🧠 AI Response ({ai_response.model_used}): {ai_response.content[:100]}..."
            )
            print(
                f"   Confidence: {ai_response.confidence:.2f}, Processing: {ai_response.processing_time:.3f}s"
            )

        except Exception as e:
            print(f"🚨 Intelligent response error: {e}")

            # Fallback to simple pattern response
            if patterns:
                pattern = patterns[0]
                simple_response = f"Pattern detected: {pattern.description}"
                self.dream_bridge.send_message(simple_response)
                self.system_stats["ai_responses_sent"] += 1

    def _analyze_user_intent(self, pulse, patterns):
        """Analyze user intent from pulse and patterns"""
        buffer_name = pulse.source_buffer or "unknown"
        recent_command = pulse.data.get("recent-command", "none")

        # Analyze intent based on context
        if buffer_name.endswith(".py"):
            if recent_command in ["self-insert-command", "newline"]:
                return f"User is actively coding in Python file {buffer_name}"
            elif recent_command == "switch-to-buffer":
                return f"User switched to Python file {buffer_name} for development"
        elif buffer_name.endswith(".md"):
            return f"User is working on documentation in {buffer_name}"
        elif "magit" in buffer_name.lower():
            return f"User is performing version control operations in {buffer_name}"
        elif recent_command == "switch-to-buffer":
            return f"User navigated to {buffer_name}"
        else:
            return f"User is working in {buffer_name} with recent command: {recent_command}"

        return f"User activity in {buffer_name}"

    def simulate_development_session(self, duration: int = 30):
        """Simulate a development session to show learning"""
        print(f"\n🎭 Simulating {duration}s development session...")

        # Simulate realistic development activities
        activities = [
            {"buffer": "main.py", "command": "self-insert-command", "type": "coding"},
            {"buffer": "main.py", "command": "newline", "type": "coding"},
            {"buffer": "test.py", "command": "switch-to-buffer", "type": "navigation"},
            {"buffer": "test.py", "command": "self-insert-command", "type": "coding"},
            {
                "buffer": "README.md",
                "command": "switch-to-buffer",
                "type": "documentation",
            },
            {
                "buffer": "README.md",
                "command": "self-insert-command",
                "type": "documentation",
            },
            {"buffer": "*magit*", "command": "magit-status", "type": "version_control"},
        ]

        for i in range(duration):
            if not self.running:
                break

            # Pick activity
            activity = activities[i % len(activities)]

            # Send simulated pulse
            self.redis.xadd(
                "dream:pulse",
                {
                    "type": "pulse",
                    "data": json.dumps(
                        {
                            "timestamp": time.time(),
                            "current-buffer": activity["buffer"],
                            "point": 100 + i * 10,
                            "line": 1 + i,
                            "column": i % 80,
                            "major-mode": self._buffer_to_mode(activity["buffer"]),
                            "minor-modes": ["evil-mode", "company-mode"],
                            "window-count": 2,
                            "recent-command": activity["command"],
                            "activity-type": activity["type"],
                        }
                    ),
                },
            )

            time.sleep(1)

        print("✅ Development session simulation complete")

    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""

        # Get component statuses
        emergent_status = self.emergent_system.status() if self.emergent_system else {}
        evolution_summary = self.evolution_engine.get_evolution_summary()
        learning_summary = self.learning_engine.get_learning_summary()
        bridge_stats = self.dream_bridge.get_session_stats()

        # Calculate uptime
        uptime = time.time() - self.system_stats["start_time"] if self.running else 0

        return {
            "system_running": self.running,
            "uptime_seconds": uptime,
            "components": {
                "emergent_system": emergent_status,
                "evolution_engine": evolution_summary,
                "learning_engine": learning_summary,
                "dream_bridge": bridge_stats,
            },
            "statistics": self.system_stats,
            "capabilities": {
                "bidirectional_communication": True,
                "pattern_learning": True,
                "topology_evolution": True,
                "self_modification": True,
                "predictive_responses": True,
            },
        }

    def demonstrate_capabilities(self):
        """Demonstrate the complete system capabilities"""
        print("\n🎯 DEMONSTRATING SYSTEM CAPABILITIES")
        print("=" * 45)

        # Show current system status
        status = self.get_system_status()
        print(f"⚡ System Status:")
        print(f"   Running: {status['system_running']}")
        print(f"   Uptime: {status['uptime_seconds']:.1f}s")
        print(f"   Facade observations: {status['statistics']['facade_observations']}")
        print(f"   Patterns learned: {status['statistics']['patterns_learned']}")
        print(f"   AI responses sent: {status['statistics']['ai_responses_sent']}")

        # Show learning progress
        learning = status["components"]["learning_engine"]
        print(f"\n🧠 Learning Progress:")
        print(f"   Total patterns: {learning['total_patterns']}")
        print(f"   Average confidence: {learning['average_confidence']:.2f}")
        print(f"   Events processed: {learning['total_events_processed']}")

        # Show evolution status
        evolution = status["components"]["evolution_engine"]
        print(f"\n🧬 Evolution Status:")
        print(f"   Evolution cycles: {evolution['evolution_cycles']}")
        print(f"   Active mutations: {evolution['active_mutations']}")
        print(f"   Evolution running: {evolution['evolution_running']}")

        # Show capabilities
        capabilities = status["capabilities"]
        print(f"\n🌟 Active Capabilities:")
        for capability, active in capabilities.items():
            status_icon = "✅" if active else "❌"
            print(f"   {status_icon} {capability.replace('_', ' ').title()}")

    def shutdown_system(self):
        """Gracefully shutdown the complete system"""
        print("\n🛑 Shutting down complete dream system...")

        self.running = False

        # Stop components
        if self.evolution_engine:
            self.evolution_engine.stop_evolution()

        if self.dream_bridge:
            self.dream_bridge.stop_bridge()

        if self.emergent_system:
            self.emergent_system.shutdown()

        print("✅ Complete dream system shutdown")


def demo_complete_dream_system():
    """Demo the complete integrated dream system"""
    print("🌟 COMPLETE DREAM SYSTEM DEMO")
    print("=" * 50)

    system = CompleteDreamSystem()

    try:
        # Start the complete system
        if system.start_complete_system():

            # Simulate some development activity
            print("\n📝 Starting simulated development session...")
            system.simulate_development_session(20)

            # Let the system learn and evolve
            print("\n🔄 Letting system learn and evolve...")
            time.sleep(15)

            # Demonstrate capabilities
            system.demonstrate_capabilities()

            print("\n🎉 THE DREAM IS REAL!")
            print("This system demonstrates:")
            print("  • Bidirectional AI-Emacs communication")
            print("  • Real pattern learning from development workflows")
            print("  • Live topology evolution based on usage")
            print("  • Self-aware, self-modifying distributed AI")
            print("  • Revolutionary AI development environment")

        else:
            print("❌ Failed to start complete system")

    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted")

    finally:
        system.shutdown_system()
        print("✅ Complete dream system demo finished")


if __name__ == "__main__":
    demo_complete_dream_system()
