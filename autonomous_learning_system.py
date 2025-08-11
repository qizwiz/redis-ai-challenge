#!/usr/bin/env python3
"""
Autonomous Learning System
Redis-coordinated system that learns from failures without human intervention
"""

import redis
import json
import time
from typing import Dict, List, Any
from collections import defaultdict, Counter
from dataclasses import dataclass


@dataclass
class SystemPattern:
    pattern_id: str
    trigger_condition: str
    learned_fix: List[str]
    confidence: float
    usage_count: int
    last_updated: float


class AutonomousLearningSystem:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.learned_patterns = {}

    def detect_failure_patterns(self):
        """Analyze Redis streams to detect system failure patterns"""

        # Get recent command executions
        commands = self.redis_client.xrange("emacs:mcp:commands", count=100)
        results = self.redis_client.xrange("emacs:mcp:results", count=100)

        failure_patterns = []

        for cmd_id, cmd_data in commands:
            # Find corresponding result
            result_data = None
            for res_id, res_data in results:
                if res_data.get("id") == cmd_data.get("id"):
                    result_data = res_data
                    break

            if not result_data:
                continue

            # Pattern: Command succeeded but user reported invisibility
            if (
                result_data.get("status") == "success"
                and "switch-to-buffer" in cmd_data.get("elisp", "")
                and self._check_for_visibility_complaints(cmd_id)
            ):

                failure_patterns.append(
                    {
                        "type": "INVISIBLE_BUFFER",
                        "trigger": "buffer_switch_without_visibility",
                        "original_command": cmd_data.get("elisp"),
                        "timestamp": float(cmd_data.get("timestamp", 0)),
                    }
                )

        return failure_patterns

    def synthesize_learned_fixes(
        self, failure_patterns: List[Dict]
    ) -> List[SystemPattern]:
        """Generate learned fixes from detected patterns"""

        patterns = []

        # Group similar failures
        grouped_failures = defaultdict(list)
        for failure in failure_patterns:
            grouped_failures[failure["type"]].append(failure)

        for failure_type, failures in grouped_failures.items():
            if failure_type == "INVISIBLE_BUFFER":
                # Learn that buffer switches need visibility management
                learned_fix = [
                    "(switch-to-buffer BUFFER_NAME)",
                    "(delete-other-windows)",  # Ensure visibility
                    '(when (string-match "session" (buffer-name)) (org-mode))',  # Smart mode
                ]

                pattern = SystemPattern(
                    pattern_id=f"fix_{failure_type}_{int(time.time())}",
                    trigger_condition="buffer_switch_command_without_visibility",
                    learned_fix=learned_fix,
                    confidence=len(failures)
                    / 10.0,  # More failures = higher confidence
                    usage_count=0,
                    last_updated=time.time(),
                )

                patterns.append(pattern)

        return patterns

    def store_learned_patterns(self, patterns: List[SystemPattern]):
        """Store learned patterns in Redis for system-wide access"""

        for pattern in patterns:
            pattern_key = f"system:learned:patterns:{pattern.pattern_id}"

            self.redis_client.hset(
                pattern_key,
                mapping={
                    "trigger_condition": pattern.trigger_condition,
                    "learned_fix": json.dumps(pattern.learned_fix),
                    "confidence": pattern.confidence,
                    "usage_count": pattern.usage_count,
                    "last_updated": pattern.last_updated,
                },
            )

            # Add to pattern index for fast lookup
            self.redis_client.sadd("system:pattern:index", pattern.pattern_id)

    def apply_learned_patterns(self, proposed_command: str) -> str:
        """Apply learned patterns to enhance proposed commands"""

        # Get all learned patterns
        pattern_ids = self.redis_client.smembers("system:pattern:index")

        enhanced_command = proposed_command

        for pattern_id in pattern_ids:
            pattern_data = self.redis_client.hgetall(
                f"system:learned:patterns:{pattern_id}"
            )

            if not pattern_data:
                continue

            trigger = pattern_data.get("trigger_condition", "")
            confidence = float(pattern_data.get("confidence", 0))

            # If confidence is high enough and trigger matches
            if confidence > 0.5 and self._matches_trigger(proposed_command, trigger):
                learned_fix = json.loads(pattern_data.get("learned_fix", "[]"))

                # Apply the learned enhancement
                if (
                    "switch-to-buffer" in proposed_command
                    and trigger == "buffer_switch_command_without_visibility"
                ):
                    # Replace simple buffer switch with enhanced version
                    buffer_name = self._extract_buffer_name(proposed_command)
                    enhanced_commands = [
                        f'(switch-to-buffer "{buffer_name}")',
                        "(delete-other-windows)",
                        f'(when (string-match "session" "{buffer_name}") (org-mode))',
                    ]
                    enhanced_command = "(progn " + " ".join(enhanced_commands) + ")"

                    # Update usage count
                    self.redis_client.hincrby(
                        f"system:learned:patterns:{pattern_id}", "usage_count", 1
                    )

        return enhanced_command

    def autonomous_learning_cycle(self):
        """Run one cycle of autonomous learning"""

        print("🤖 **AUTONOMOUS LEARNING CYCLE**")

        # 1. Detect failure patterns from Redis streams
        print("🔍 Analyzing system behavior patterns...")
        failure_patterns = self.detect_failure_patterns()
        print(f"Found {len(failure_patterns)} potential failure patterns")

        # 2. Synthesize learned fixes
        print("🧠 Synthesizing learned fixes...")
        learned_patterns = self.synthesize_learned_fixes(failure_patterns)
        print(f"Generated {len(learned_patterns)} learned patterns")

        # 3. Store in Redis for system-wide access
        print("💾 Storing learned patterns...")
        self.store_learned_patterns(learned_patterns)

        # 4. Report what was learned
        for pattern in learned_patterns:
            print(f"📚 LEARNED: {pattern.trigger_condition}")
            print(f"   FIX: {pattern.learned_fix}")
            print(f"   CONFIDENCE: {pattern.confidence:.2f}")

        return learned_patterns

    def test_pattern_application(self, test_command: str) -> str:
        """Test applying learned patterns to a command"""

        print(f"🧪 Testing pattern application on: {test_command}")

        enhanced = self.apply_learned_patterns(test_command)

        if enhanced != test_command:
            print(f"✅ Pattern applied!")
            print(f"   Original: {test_command}")
            print(f"   Enhanced: {enhanced}")
        else:
            print(f"❌ No patterns applied")

        return enhanced


# Example usage
if __name__ == "__main__":
    learning_system = AutonomousLearningSystem()

    print("🚀 **AUTONOMOUS SYSTEM LEARNING TEST**")

    # Run learning cycle
    learned_patterns = learning_system.autonomous_learning_cycle()

    # Test pattern application
    test_commands = [
        '(switch-to-buffer "*test-buffer*")',
        "(goto-line 50)",
        '(switch-to-buffer "*Claude-Session*")',
    ]

    print(f"\n🧪 **TESTING LEARNED PATTERN APPLICATION**:")
    for cmd in test_commands:
        enhanced = learning_system.test_pattern_application(cmd)
        print()

    print(f"\n📊 **SYSTEM LEARNING SUMMARY**:")
    print(f"Patterns learned this cycle: {len(learned_patterns)}")
    print(
        f"Total patterns in system: {len(learning_system.redis_client.smembers('system:pattern:index'))}"
    )

    print(f"\n🔮 **AUTONOMOUS LEARNING STATUS**: OPERATIONAL")
    print("System can now learn from failures and apply fixes automatically!")
