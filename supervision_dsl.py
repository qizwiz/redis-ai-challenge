#!/usr/bin/env python3
"""
Supervision DSL - Beautiful fault-tolerant process supervision

Inspired by claude-flow patterns, this DSL provides elegant syntax for
building supervision trees with Redis-coordinated distributed actors.
"""

import redis
import json
import time
import threading
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager


class RestartStrategy(Enum):
    ONE_FOR_ONE = "one_for_one"  # Restart only failed actor
    ONE_FOR_ALL = "one_for_all"  # Restart all actors in group
    REST_FOR_ONE = "rest_for_one"  # Restart failed + all started after it
    PERMANENT = "permanent"  # Never stop, always restart
    TEMPORARY = "temporary"  # Never restart
    TRANSIENT = "transient"  # Restart only on abnormal exit


@dataclass
class SupervisionSpec:
    name: str
    strategy: RestartStrategy = RestartStrategy.ONE_FOR_ONE
    max_restarts: int = 5
    restart_window: int = 60  # seconds
    timeout: int = 30
    restart_delay: float = 1.0
    backoff_multiplier: float = 2.0
    max_backoff: float = 30.0
    hooks: Dict[str, List[Callable]] = field(default_factory=dict)


@dataclass
class ActorSpec:
    name: str
    handler: Callable
    restart_strategy: RestartStrategy = RestartStrategy.PERMANENT
    dependencies: List[str] = field(default_factory=list)
    health_check: Optional[Callable] = None
    startup_timeout: int = 10
    shutdown_timeout: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)


class SupervisionDSL:
    def __init__(self, redis_host="localhost", redis_port=6379):
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )
        self.supervisors = {}
        self.actors = {}
        self.running = False

    # Beautiful DSL syntax
    def supervisor(self, name: str):
        """DSL: Create supervision context"""
        return SupervisorBuilder(self, name)

    def actor(self, name: str):
        """DSL: Create actor"""
        return ActorBuilder(self, name)

    def spawn(self, supervision_tree):
        """DSL: Spawn entire supervision tree"""
        self.running = True
        return SupervisionRunner(self, supervision_tree)


class SupervisorBuilder:
    def __init__(self, dsl: SupervisionDSL, name: str):
        self.dsl = dsl
        self.spec = SupervisionSpec(name)

    def strategy(self, strategy: RestartStrategy):
        """DSL: Set restart strategy"""
        self.spec.strategy = strategy
        return self

    def max_restarts(self, count: int, window: int = 60):
        """DSL: Set restart limits"""
        self.spec.max_restarts = count
        self.spec.restart_window = window
        return self

    def timeout(self, seconds: int):
        """DSL: Set operation timeout"""
        self.spec.timeout = seconds
        return self

    def backoff(
        self, initial: float = 1.0, multiplier: float = 2.0, max_delay: float = 30.0
    ):
        """DSL: Set exponential backoff"""
        self.spec.restart_delay = initial
        self.spec.backoff_multiplier = multiplier
        self.spec.max_backoff = max_delay
        return self

    def on(self, event: str, handler: Callable):
        """DSL: Add event hook"""
        if event not in self.spec.hooks:
            self.spec.hooks[event] = []
        self.spec.hooks[event].append(handler)
        return self

    def supervising(self, *actors):
        """DSL: Add actors to supervision"""
        self.actors = actors
        return self

    def build(self):
        """DSL: Build supervisor"""
        supervisor = FaultTolerantSupervisor(self.dsl.redis, self.spec)
        self.dsl.supervisors[self.spec.name] = supervisor
        return supervisor


class ActorBuilder:
    def __init__(self, dsl: SupervisionDSL, name: str):
        self.dsl = dsl
        self.spec = ActorSpec(name, None)

    def handler(self, func: Callable):
        """DSL: Set actor handler function"""
        self.spec.handler = func
        return self

    def restart(self, strategy: RestartStrategy):
        """DSL: Set restart strategy"""
        self.spec.restart_strategy = strategy
        return self

    def depends_on(self, *dependencies):
        """DSL: Set dependencies"""
        self.spec.dependencies = list(dependencies)
        return self

    def health_check(self, func: Callable):
        """DSL: Set health check function"""
        self.spec.health_check = func
        return self

    def timeout(self, startup: int = 10, shutdown: int = 5):
        """DSL: Set timeouts"""
        self.spec.startup_timeout = startup
        self.spec.shutdown_timeout = shutdown
        return self

    def metadata(self, **kwargs):
        """DSL: Add metadata"""
        self.spec.metadata.update(kwargs)
        return self

    def build(self):
        """DSL: Build actor"""
        actor = SupervisedActor(self.dsl.redis, self.spec)
        self.dsl.actors[self.spec.name] = actor
        return actor


class FaultTolerantSupervisor:
    def __init__(self, redis_client: redis.Redis, spec: SupervisionSpec):
        self.redis = redis_client
        self.spec = spec
        self.actors = {}
        self.restart_counts = {}
        self.last_restart = {}
        self.running = False

    def add_actor(self, actor: "SupervisedActor"):
        """Add actor to supervision"""
        self.actors[actor.spec.name] = actor
        self.restart_counts[actor.spec.name] = 0
        self.last_restart[actor.spec.name] = 0

    def start(self):
        """Start supervision"""
        self.running = True
        self._call_hooks("supervisor_start")

        for actor in self.actors.values():
            self._start_actor(actor)

        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()

    def _restart_actor(self, actor: "SupervisedActor"):
        """Restart single actor with backoff"""
        name = actor.spec.name
        restart_count = self.restart_counts.get(name, 0)

        # Calculate backoff delay
        delay = min(
            self.spec.restart_delay * (self.spec.backoff_multiplier**restart_count),
            self.spec.max_backoff,
        )

        self._log(f"Restarting {name} in {delay}s (attempt {restart_count + 1})")
        time.sleep(delay)

        try:
            actor.stop()
            actor.start()

            self.restart_counts[name] = restart_count + 1
            self.last_restart[name] = time.time()

            self._call_hooks("actor_restart", actor=actor)

        except Exception as e:
            self._log(f"Failed to restart {name}: {e}")

    def _log(self, message: str):
        """Log message to Redis"""
        timestamp = time.time()
        log_entry = {
            "timestamp": timestamp,
            "supervisor": self.spec.name,
            "message": message,
        }
        self.redis.lpush("supervision:logs", json.dumps(log_entry))
        self.redis.ltrim("supervision:logs", 0, 999)  # Keep last 1000 logs
        print(f"[{self.spec.name}] {message}")


class SupervisedActor:
    def __init__(self, redis_client: redis.Redis, spec: ActorSpec):
        self.redis = redis_client
        self.spec = spec
        self.running = False
        self.thread = None

    def start(self):
        """Start actor"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

        # Set heartbeat
        self.redis.setex(f"actor:{self.spec.name}:heartbeat", 10, "alive")

    def stop(self):
        """Stop actor"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=self.spec.shutdown_timeout)

    def _log(self, message: str):
        """Log message"""
        print(f"[{self.spec.name}] {message}")


class SupervisionRunner:
    def __init__(self, dsl: SupervisionDSL, tree):
        self.dsl = dsl
        self.tree = tree

    def __enter__(self):
        """Start supervision tree"""
        for supervisor in self.dsl.supervisors.values():
            supervisor.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop supervision tree"""
        self.dsl.running = False


# Beautiful DSL usage example
def create_example_supervision():
    """Example of beautiful supervision DSL"""
    dsl = SupervisionDSL()

    # Define actors with beautiful syntax
    message_actor = (
        dsl.actor("message-processor")
        .handler(lambda: print("Processing messages..."))
        .restart(RestartStrategy.PERMANENT)
        .health_check(lambda: True)
        .timeout(startup=5, shutdown=3)
        .metadata(role="processor", priority="high")
        .build()
    )

    facade_actor = (
        dsl.actor("facade-monitor")
        .handler(lambda: print("Monitoring facade..."))
        .restart(RestartStrategy.PERMANENT)
        .depends_on("message-processor")
        .health_check(lambda: True)
        .build()
    )

    # Define supervisor with beautiful syntax
    supervisor = (
        dsl.supervisor("main-supervisor")
        .strategy(RestartStrategy.ONE_FOR_ONE)
        .max_restarts(5, window=60)
        .timeout(30)
        .backoff(initial=1.0, multiplier=2.0, max_delay=30.0)
        .on("supervisor_start", lambda: print("🚀 Supervisor started"))
        .on(
            "actor_failure",
            lambda actor, error: print(f"💥 {actor.spec.name} failed: {error}"),
        )
        .on("actor_restart", lambda actor: print(f"🔄 {actor.spec.name} restarted"))
        .supervising(message_actor, facade_actor)
        .build()
    )

    # Add actors to supervisor
    supervisor.add_actor(message_actor)
    supervisor.add_actor(facade_actor)

    return dsl


if __name__ == "__main__":
    # Beautiful DSL in action
    print("🎭 Supervision DSL Demo")

    dsl = create_example_supervision()

    # Spawn supervision tree with context manager
    with dsl.spawn(dsl.supervisors):
        print("✅ Supervision tree running...")
        print("Press Ctrl+C to stop")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping supervision tree...")

    print("✅ Supervision DSL demo complete")
