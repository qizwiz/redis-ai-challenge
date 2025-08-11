#!/usr/bin/env python3
"""
Redis-CLI Subagent
Wraps redis-cli with intelligence, learning, and autonomous coordination
"""

import subprocess
import json
import time
import threading
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque


class RedisCliSubagent:
    def __init__(self, name: str = "redis-cli-subagent"):
        self.name = name
        self.command_history = deque(maxlen=1000)
        self.learned_patterns = defaultdict(int)
        self.success_rate = {}
        self.autonomous_mode = True
        self.last_command_time = 0

        # Start autonomous monitoring
        self.monitor_thread = threading.Thread(
            target=self._autonomous_monitor, daemon=True
        )
        self.monitor_thread.start()

        print(f"🤖 {self.name} initialized with autonomous intelligence")

    def execute(self, command: str, learn: bool = True) -> Dict[str, Any]:
        """Execute redis-cli command with intelligence"""
        start_time = time.time()

        # Pre-execution intelligence
        prediction = self._predict_success(command)
        optimized_command = self._optimize_command(command)

        try:
            # Execute the actual redis-cli command
            result = subprocess.run(
                f"redis-cli {optimized_command}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )

            success = result.returncode == 0
            execution_time = time.time() - start_time

            # Post-execution learning
            if learn:
                self._learn_from_execution(command, success, execution_time, result)

            response = {
                "command": command,
                "optimized_command": optimized_command,
                "success": success,
                "output": result.stdout.strip(),
                "error": result.stderr.strip(),
                "execution_time": execution_time,
                "prediction_accuracy": abs(prediction - (1.0 if success else 0.0)),
                "learned": learn,
            }

            self.command_history.append(response)
            return response

        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "success": False,
                "error": "Command timed out",
                "execution_time": 10.0,
            }
        except Exception as e:
            return {
                "command": command,
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
            }

    def _learn_from_execution(
        self, command: str, success: bool, exec_time: float, result
    ):
        """Learn from command execution results"""
        command_type = self._classify_command(command)

        # Update success rate
        if command_type not in self.success_rate:
            self.success_rate[command_type] = 0.8

        # Exponential moving average of success rate
        alpha = 0.1
        new_success = 1.0 if success else 0.0
        self.success_rate[command_type] = (
            alpha * new_success + (1 - alpha) * self.success_rate[command_type]
        )

        # Learn patterns
        if success:
            self.learned_patterns[command_type] += 1

        # Autonomous insight generation
        if not success and self.autonomous_mode:
            self._generate_failure_insight(command, result.stderr)

    def get_intelligence_summary(self) -> Dict[str, Any]:
        """Get summary of learned intelligence"""
        recent_commands = list(self.command_history)[-10:]

        return {
            "agent_name": self.name,
            "total_commands": len(self.command_history),
            "success_rates": dict(self.success_rate),
            "learned_patterns": dict(self.learned_patterns),
            "recent_commands": recent_commands,
            "autonomous_active": self.autonomous_mode,
        }


# Intelligent Redis operations
def smart_redis_add(stream: str, data: Dict[str, str]) -> Dict[str, Any]:
    """Smart Redis XADD with error handling and learning"""
    agent = RedisCliSubagent("smart-add")

    # Format data for Redis
    data_parts = []
    for key, value in data.items():
        data_parts.extend([key, f'"{value}"'])

    command = f'XADD {stream} "*" ' + " ".join(data_parts)
    return agent.execute(command)


def smart_redis_read(
    stream: str, last_id: str = "0", count: int = 10
) -> Dict[str, Any]:
    """Smart Redis XREAD with learning"""
    agent = RedisCliSubagent("smart-read")
    command = f"XREAD STREAMS {stream} {last_id} COUNT {count} BLOCK 100"
    return agent.execute(command)


if __name__ == "__main__":
    # Test the intelligent Redis subagent
    agent = RedisCliSubagent("test-agent")

    print("🧪 Testing intelligent Redis subagent...")

    # Test various commands
    test_commands = [
        "PING",
        'XADD test:stream "*" message "hello world"',
        "XLEN test:stream",
        "XREAD STREAMS test:stream 0 COUNT 1",
    ]

    for cmd in test_commands:
        print(f"\n📝 Executing: {cmd}")
        result = agent.execute(cmd)
        print(
            f"Result: {result['success']} - {result.get('output', result.get('error'))}"
        )

    print(f"\n🧠 Intelligence Summary:")
    summary = agent.get_intelligence_summary()
    print(json.dumps(summary, indent=2))
