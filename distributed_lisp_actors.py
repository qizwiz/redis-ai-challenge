#!/usr/bin/env python3
"""
Distributed Lisp Actors - S-expressions as Fault-Tolerant Network Topology
Revolutionary programming model where code structure IS infrastructure
"""

import redis
import json
import asyncio
import time
import traceback
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import threading
from collections import defaultdict


class RestartStrategy(Enum):
    PERMANENT = "permanent"  # Always restart
    TRANSIENT = "transient"  # Restart only on abnormal exit
    TEMPORARY = "temporary"  # Never restart


class SupervisorStrategy(Enum):
    ONE_FOR_ONE = "one_for_one"  # Restart only failed actor
    ONE_FOR_ALL = "one_for_all"  # Restart all actors if one fails
    REST_FOR_ONE = "rest_for_one"  # Restart failed actor and all after it


@dataclass
class ActorDefinition:
    name: str
    actor_type: str = "process"  # process, mcp-server, minor-mode
    restart: RestartStrategy = RestartStrategy.PERMANENT
    behavior: Optional[Callable] = None
    children: List["ActorDefinition"] = field(default_factory=list)
    supervisor_strategy: Optional[SupervisorStrategy] = None

    def is_supervisor(self) -> bool:
        return len(self.children) > 0


class ActorRuntime:
    """Runtime for distributed Lisp actors across Redis + Emacs + MCP"""

    def __init__(self, redis_host="localhost", redis_port=6379):
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )
        self.actors: Dict[str, ActorDefinition] = {}
        self.running_processes: Dict[str, Any] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.supervision_trees: Dict[str, List[str]] = defaultdict(list)
        self.restart_counts: Dict[str, int] = defaultdict(int)
        self.running = True

    def parse_sexp_topology(self, sexp_text: str) -> ActorDefinition:
        """Parse S-expression into actor supervision topology

        Example input:
        (supervisor ai-system :strategy one-for-all
          (actor claude-coordinator :restart permanent
            (actor nlp-parser :type mcp-server :restart transient)
            (actor emacs-interface :type minor-mode)))
        """
        # Simple parser for our actor DSL
        tokens = self._tokenize_sexp(sexp_text)
        return self._parse_actor_definition(tokens)

    def _tokenize_sexp(self, text: str) -> List[str]:
        """Simple S-expression tokenizer"""
        tokens = []
        current_token = ""
        in_string = False

        for char in text:
            if char == '"' and not in_string:
                in_string = True
                current_token += char
            elif char == '"' and in_string:
                in_string = False
                current_token += char
            elif in_string:
                current_token += char
            elif char in "()":
                if current_token.strip():
                    tokens.append(current_token.strip())
                    current_token = ""
                tokens.append(char)
            elif char.isspace():
                if current_token.strip():
                    tokens.append(current_token.strip())
                    current_token = ""
            else:
                current_token += char

        if current_token.strip():
            tokens.append(current_token.strip())

        return tokens

    def _parse_actor_definition(self, tokens: List[str]) -> ActorDefinition:
        """Parse tokens into ActorDefinition tree"""
        if not tokens or tokens[0] != "(":
            raise ValueError("Invalid S-expression: must start with '('")

        tokens = tokens[1:]  # Skip opening paren

        if not tokens:
            raise ValueError("Empty S-expression")

        # First token is actor type (actor or supervisor)
        defn_type = tokens.pop(0)

        if defn_type not in ["actor", "supervisor"]:
            raise ValueError(f"Unknown definition type: {defn_type}")

        # Second token is name
        name = tokens.pop(0)

        # Parse keyword arguments
        kwargs = {}
        children = []

        while tokens and tokens[0] != ")":
            if tokens[0] == ":":
                tokens.pop(0)  # Skip :
                key = tokens.pop(0)
                value = tokens.pop(0)
                kwargs[key] = value
            elif tokens[0] == "(":
                # Parse child actor
                child_tokens = self._extract_balanced_sexp(tokens)
                child_actor = self._parse_actor_definition(child_tokens)
                children.append(child_actor)
            else:
                tokens.pop(0)  # Skip unknown tokens

        # Create ActorDefinition
        actor = ActorDefinition(
            name=name,
            actor_type=kwargs.get("type", "process"),
            restart=RestartStrategy(kwargs.get("restart", "permanent")),
            children=children,
        )

        if defn_type == "supervisor":
            strategy_str = kwargs.get("strategy", "one_for_one")
            actor.supervisor_strategy = SupervisorStrategy(strategy_str)

        return actor

    def _extract_balanced_sexp(self, tokens: List[str]) -> List[str]:
        """Extract a balanced S-expression from token stream"""
        if not tokens or tokens[0] != "(":
            return []

        result = []
        paren_count = 0

        for token in tokens:
            result.append(token)
            if token == "(":
                paren_count += 1
            elif token == ")":
                paren_count -= 1
                if paren_count == 0:
                    break

        # Remove extracted tokens from original list
        for _ in range(len(result)):
            if tokens:
                tokens.pop(0)

        return result

    def spawn_actor_tree(self, root_actor: ActorDefinition):
        """Spawn an entire actor supervision tree"""
        print(f"🚀 Spawning actor tree: {root_actor.name}")

        # Register actor
        self.actors[root_actor.name] = root_actor

        # Spawn this actor
        if root_actor.actor_type == "mcp-server":
            self._spawn_mcp_actor(root_actor)
        elif root_actor.actor_type == "minor-mode":
            self._spawn_emacs_actor(root_actor)
        elif root_actor.actor_type == "process":
            self._spawn_process_actor(root_actor)

        # Spawn children
        for child in root_actor.children:
            self.supervision_trees[root_actor.name].append(child.name)
            self.spawn_actor_tree(child)

        print(f"✅ Actor tree spawned: {root_actor.name}")

    def send_message(self, actor_name: str, message_type: str, data: Any):
        """Send message to actor via Redis streams"""
        message = {
            "type": message_type,
            "data": json.dumps(data),
            "timestamp": time.time(),
            "sender": "runtime",
        }

        stream_name = f"actor:{actor_name}:messages"
        self.redis.xadd(stream_name, message)
        print(f"📨 Sent {message_type} to {actor_name}")

    def monitor_actor_health(self):
        """Monitor actor health and restart on failures"""
        print("🔍 Starting actor health monitoring...")

        while self.running:
            try:
                for actor_name, process in list(self.running_processes.items()):
                    if process.poll() is not None:  # Process died
                        print(
                            f"💀 Actor {actor_name} died (exit code: {process.returncode})"
                        )
                        self._handle_actor_failure(actor_name)

                time.sleep(2)  # Check every 2 seconds

            except Exception as e:
                print(f"❌ Health monitor error: {e}")
                time.sleep(5)

    def _handle_actor_failure(self, failed_actor: str):
        """Handle actor failure according to supervision strategy"""
        if failed_actor not in self.actors:
            return

        actor = self.actors[failed_actor]

        # Find supervisor
        supervisor_name = self._find_supervisor(failed_actor)
        if not supervisor_name:
            print(f"⚠️ No supervisor found for {failed_actor}")
            return

        supervisor = self.actors[supervisor_name]
        strategy = supervisor.supervisor_strategy

        print(f"🔄 Handling failure of {failed_actor} with strategy {strategy}")

        if strategy == SupervisorStrategy.ONE_FOR_ONE:
            self._restart_actor(failed_actor)
        elif strategy == SupervisorStrategy.ONE_FOR_ALL:
            self._restart_all_children(supervisor_name)
        elif strategy == SupervisorStrategy.REST_FOR_ONE:
            self._restart_actor_and_rest(supervisor_name, failed_actor)

    def _restart_actor(self, actor_name: str):
        """Restart a single actor"""
        actor = self.actors[actor_name]

        # Check restart limits
        self.restart_counts[actor_name] += 1
        if self.restart_counts[actor_name] > 5:
            print(f"❌ Actor {actor_name} exceeded restart limit")
            return

        print(f"🔄 Restarting actor: {actor_name}")

        # Clean up old process
        if actor_name in self.running_processes:
            del self.running_processes[actor_name]

        # Respawn based on type
        if actor.actor_type == "mcp-server":
            self._spawn_mcp_actor(actor)
        elif actor.actor_type == "minor-mode":
            self._spawn_emacs_actor(actor)
        elif actor.actor_type == "process":
            self._spawn_process_actor(actor)

    def shutdown(self):
        """Gracefully shutdown all actors"""
        print("🛑 Shutting down actor runtime...")
        self.running = False

        for actor_name, process in self.running_processes.items():
            print(f"🛑 Terminating {actor_name}")
            process.terminate()

        print("✅ Actor runtime shutdown complete")


def demo_distributed_actors():
    """Demonstrate distributed Lisp actors in action"""
    print("🚀 DISTRIBUTED LISP ACTORS DEMO")
    print("=" * 40)

    # Create runtime
    runtime = ActorRuntime()

    # Define actor topology as S-expression
    sexp_topology = """
    (supervisor ai-development-system :strategy one-for-all
      (actor claude-coordinator :restart permanent
        (actor nlp-processor :type mcp-server :restart transient)
        (actor redis-stream-monitor :type process :restart permanent))
      (actor emacs-interface :type minor-mode :restart permanent
        (actor facade-updater :type minor-mode :restart transient)))
    """

    print("📋 Parsing S-expression topology...")
    try:
        root_actor = runtime.parse_sexp_topology(sexp_topology)
        print(
            f"✅ Parsed topology: {root_actor.name} with {len(root_actor.children)} children"
        )

        print("🚀 Spawning actor supervision tree...")
        runtime.spawn_actor_tree(root_actor)

        print("📨 Testing message passing...")
        runtime.send_message(
            "claude-coordinator", "process_command", {"text": "split window"}
        )
        runtime.send_message(
            "nlp-processor", "parse_intent", {"input": "create new buffer"}
        )

        print("🔍 Starting health monitoring...")
        monitor_thread = threading.Thread(target=runtime.monitor_actor_health)
        monitor_thread.daemon = True
        monitor_thread.start()

        print("⏱️ Running for 10 seconds...")
        time.sleep(10)

        runtime.shutdown()
        print("✅ Demo completed successfully!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        traceback.print_exc()
        runtime.shutdown()


if __name__ == "__main__":
    demo_distributed_actors()
