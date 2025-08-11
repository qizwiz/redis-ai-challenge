#!/usr/bin/env python3
"""
Semantic Understanding Engine - Learns from Real Usage Patterns
This engine analyzes keystroke patterns, discovers workflows, and builds semantic understanding.
"""

import asyncio
import json
import time
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from fixed_redis_coordinator import redis_coordinator
from robust_claude_integration import claude_integration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class KeystrokePattern:
    sequence: List[str]
    frequency: int
    context: Dict[str, Any]
    semantic_meaning: Optional[str] = None
    efficiency_score: float = 0.0


@dataclass
class WorkflowPattern:
    name: str
    steps: List[str]
    frequency: int
    success_rate: float
    average_duration: float
    semantic_intent: str


@dataclass
class SemanticMapping:
    input_pattern: str
    semantic_equivalent: str
    confidence: float
    usage_count: int
    context_tags: List[str]


class SemanticUnderstandingEngine:
    """Engine that learns semantic patterns from actual usage"""

    def __init__(self):
        self.coordinator = redis_coordinator
        self.running = False

        # Pattern storage
        self.keystroke_patterns: Dict[str, KeystrokePattern] = {}
        self.workflow_patterns: Dict[str, WorkflowPattern] = {}
        self.semantic_mappings: Dict[str, SemanticMapping] = {}

        # Learning state
        self.patterns_discovered = 0
        self.mappings_created = 0
        self.workflows_synthesized = 0

        # Analysis windows
        self.keystroke_window = []
        self.max_window_size = 50

        logger.info("🧠 Semantic Understanding Engine initialized")

    async def start_learning(self):
        """Start learning from user patterns"""
        self.running = True

        logger.info("🚀 Starting Semantic Understanding Engine")
        logger.info("📚 Learning patterns from real usage")

        # Start learning loops
        learning_tasks = [
            asyncio.create_task(self._analyze_keystroke_patterns()),
            asyncio.create_task(self._discover_workflow_patterns()),
            asyncio.create_task(self._build_semantic_mappings()),
            asyncio.create_task(self._synthesize_workflows()),
            asyncio.create_task(self._update_pattern_database()),
        ]

        try:
            await asyncio.gather(*learning_tasks)
        except Exception as e:
            logger.error(f"Learning error: {e}")

    async def _analyze_keystroke_patterns(self):
        """Analyze keystroke sequences to discover patterns"""
        while self.running:
            try:
                # Get recent keystrokes
                keystrokes = self.coordinator.get_recent_keystrokes(count=20)

                for keystroke in keystrokes:
                    self._add_to_keystroke_window(keystroke)

                    # Analyze patterns in current window
                    await self._detect_keystroke_patterns()

                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Keystroke pattern analysis error: {e}")
                await asyncio.sleep(5)

    def _add_to_keystroke_window(self, keystroke: Dict[str, Any]):
        """Add keystroke to analysis window"""
        self.keystroke_window.append(keystroke)

        # Maintain window size
        if len(self.keystroke_window) > self.max_window_size:
            self.keystroke_window.pop(0)

    async def _detect_keystroke_patterns(self):
        """Detect repeating patterns in keystroke sequences"""
        if len(self.keystroke_window) < 5:
            return

        # Extract key sequences
        key_sequence = [ks.get("key", "") for ks in self.keystroke_window[-10:]]

        # Look for patterns of length 2-5
        for pattern_length in range(2, 6):
            if len(key_sequence) >= pattern_length:
                pattern = tuple(key_sequence[-pattern_length:])
                pattern_str = "→".join(pattern)

                # Check if this pattern appears frequently
                pattern_count = self._count_pattern_in_window(pattern)

                if pattern_count >= 2:  # Pattern appears at least twice
                    await self._record_keystroke_pattern(pattern_str, pattern_count)

    def _count_pattern_in_window(self, pattern: Tuple[str, ...]) -> int:
        """Count occurrences of pattern in current window"""
        count = 0
        window_keys = [ks.get("key", "") for ks in self.keystroke_window]

        for i in range(len(window_keys) - len(pattern) + 1):
            if tuple(window_keys[i : i + len(pattern)]) == pattern:
                count += 1

        return count

    async def _record_keystroke_pattern(self, pattern_str: str, frequency: int):
        """Record discovered keystroke pattern"""
        if pattern_str in self.keystroke_patterns:
            self.keystroke_patterns[pattern_str].frequency += 1
        else:
            # Get context from last keystroke
            context = self.keystroke_window[-1] if self.keystroke_window else {}

            self.keystroke_patterns[pattern_str] = KeystrokePattern(
                sequence=pattern_str.split("→"),
                frequency=frequency,
                context={
                    "buffer": context.get("buffer", ""),
                    "major_mode": context.get("major_mode", ""),
                    "command": context.get("command", ""),
                },
            )

            self.patterns_discovered += 1
            logger.info(
                f"🔍 Discovered keystroke pattern: {pattern_str} (frequency: {frequency})"
            )

            # Try to understand semantic meaning
            await self._analyze_pattern_semantics(pattern_str)

    async def _analyze_pattern_semantics(self, pattern_str: str):
        """Analyze the semantic meaning of a keystroke pattern"""
        if not claude_integration.is_available():
            return

        try:
            prompt = f"""You are a semantic analysis engine for code editing patterns.

Keystroke pattern: {pattern_str}

This pattern was observed in a user's editing session. Analyze what this sequence of keystrokes likely represents in terms of:
1. User intent (what they're trying to accomplish)
2. Editing operation (navigation, insertion, deletion, etc.)
3. Efficiency level (is this an optimal way to achieve the intent?)

Respond with a brief semantic description (1-2 sentences) of what this pattern represents."""

            response = claude_integration.execute_prompt(prompt, timeout=10)

            if response.success:
                pattern = self.keystroke_patterns.get(pattern_str)
                if pattern:
                    pattern.semantic_meaning = response.content.strip()
                    logger.info(
                        f"🧠 Pattern meaning: {pattern_str} → {pattern.semantic_meaning}"
                    )

        except Exception as e:
            logger.error(f"Semantic analysis error: {e}")

    async def _discover_workflow_patterns(self):
        """Discover larger workflow patterns from command sequences"""
        while self.running:
            try:
                # Analyze command sequences from recent activity
                await self._analyze_command_workflows()

                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Workflow pattern discovery error: {e}")
                await asyncio.sleep(10)

    async def _analyze_command_workflows(self):
        """Analyze command sequences to identify workflows"""
        try:
            # Get recent keystrokes with commands
            keystrokes = self.coordinator.get_recent_keystrokes(count=30)

            # Extract command sequences
            commands = []
            for ks in keystrokes:
                command = ks.get("command", "")
                if command and command != "unknown":
                    commands.append(command)

            # Look for workflow patterns
            await self._identify_workflow_sequences(commands)

        except Exception as e:
            logger.error(f"Command workflow analysis error: {e}")

    async def _identify_workflow_sequences(self, commands: List[str]):
        """Identify workflow sequences from command list"""
        if len(commands) < 3:
            return

        # Look for sequences of 3-7 commands
        for seq_length in range(3, min(8, len(commands) + 1)):
            sequence = commands[-seq_length:]
            sequence_str = " → ".join(sequence)

            # Check if this represents a meaningful workflow
            if await self._is_meaningful_workflow(sequence):
                await self._record_workflow_pattern(sequence_str, sequence)

    async def _is_meaningful_workflow(self, sequence: List[str]) -> bool:
        """Determine if command sequence represents a meaningful workflow"""
        # Heuristics for meaningful workflows
        unique_commands = set(sequence)

        # Workflow should have some variety (not all same command)
        if len(unique_commands) < 2:
            return False

        # Should contain some navigational or editing commands
        editing_commands = {
            "self-insert-command",
            "newline",
            "delete-backward-char",
            "yank",
        }
        navigation_commands = {
            "forward-char",
            "backward-char",
            "next-line",
            "previous-line",
        }

        has_editing = any(cmd in editing_commands for cmd in sequence)
        has_navigation = any(cmd in navigation_commands for cmd in sequence)

        return has_editing or has_navigation

    async def _record_workflow_pattern(self, sequence_str: str, sequence: List[str]):
        """Record a discovered workflow pattern"""
        if sequence_str in self.workflow_patterns:
            self.workflow_patterns[sequence_str].frequency += 1
        else:
            self.workflow_patterns[sequence_str] = WorkflowPattern(
                name=f"workflow_{len(self.workflow_patterns)}",
                steps=sequence,
                frequency=1,
                success_rate=1.0,  # Assume successful since user completed it
                average_duration=5.0,  # Placeholder
                semantic_intent="Unknown workflow",
            )

            self.workflows_synthesized += 1
            logger.info(f"🔄 Discovered workflow: {sequence_str}")

            # Try to understand workflow semantics
            await self._analyze_workflow_semantics(sequence_str)

    async def _analyze_workflow_semantics(self, sequence_str: str):
        """Analyze the semantic meaning of a workflow"""
        if not claude_integration.is_available():
            return

        try:
            prompt = f"""You are a workflow analysis engine for code editing patterns.

Command sequence: {sequence_str}

This sequence represents a workflow the user performed. Analyze what this workflow accomplishes:
1. What is the likely intent? (e.g., "refactoring", "navigation", "text insertion")
2. What type of editing operation is this?
3. Is this an efficient workflow for the intent?

Respond with a brief description of the workflow's purpose (1-2 sentences)."""

            response = claude_integration.execute_prompt(prompt, timeout=10)

            if response.success:
                workflow = self.workflow_patterns.get(sequence_str)
                if workflow:
                    workflow.semantic_intent = response.content.strip()
                    logger.info(f"🎯 Workflow intent: {workflow.semantic_intent}")

        except Exception as e:
            logger.error(f"Workflow semantic analysis error: {e}")

    async def _build_semantic_mappings(self):
        """Build mappings between input patterns and semantic equivalents"""
        while self.running:
            try:
                await self._discover_semantic_equivalences()

                await asyncio.sleep(15)

            except Exception as e:
                logger.error(f"Semantic mapping error: {e}")
                await asyncio.sleep(15)

    async def _discover_semantic_equivalences(self):
        """Discover semantic equivalences in user patterns"""
        # Analyze keystroke patterns for semantic equivalences
        for pattern_str, pattern in self.keystroke_patterns.items():
            if pattern.frequency >= 3 and pattern.semantic_meaning:
                await self._create_semantic_mapping(
                    pattern_str, pattern.semantic_meaning
                )

    async def _create_semantic_mapping(self, input_pattern: str, semantic_meaning: str):
        """Create a semantic mapping from input to meaning"""
        mapping_key = f"{input_pattern}→{semantic_meaning}"

        if mapping_key not in self.semantic_mappings:
            self.semantic_mappings[mapping_key] = SemanticMapping(
                input_pattern=input_pattern,
                semantic_equivalent=semantic_meaning,
                confidence=0.8,
                usage_count=1,
                context_tags=[],
            )

            self.mappings_created += 1
            logger.info(
                f"🔗 Created semantic mapping: {input_pattern} → {semantic_meaning}"
            )

    async def _synthesize_workflows(self):
        """Synthesize new workflows from learned patterns"""
        while self.running:
            try:
                # Look for opportunities to synthesize new workflows
                await self._generate_workflow_suggestions()

                await asyncio.sleep(20)

            except Exception as e:
                logger.error(f"Workflow synthesis error: {e}")
                await asyncio.sleep(20)

    async def _generate_workflow_suggestions(self):
        """Generate suggestions for workflow improvements"""
        # Analyze frequently used but inefficient patterns
        for pattern_str, pattern in self.keystroke_patterns.items():
            if pattern.frequency >= 5 and pattern.semantic_meaning:
                # Look for more efficient alternatives
                await self._suggest_workflow_optimization(pattern_str, pattern)

    async def _suggest_workflow_optimization(
        self, pattern_str: str, pattern: KeystrokePattern
    ):
        """Suggest optimizations for frequently used patterns"""
        if not claude_integration.is_available():
            return

        try:
            prompt = f"""You are a workflow optimization engine.

Current pattern: {pattern_str}
Semantic meaning: {pattern.semantic_meaning}
Usage frequency: {pattern.frequency}

Suggest a more efficient way to accomplish the same task. Consider:
1. Keyboard shortcuts
2. Emacs commands
3. Macro possibilities

Respond with a brief optimization suggestion."""

            response = claude_integration.execute_prompt(prompt, timeout=10)

            if response.success:
                optimization = response.content.strip()
                logger.info(
                    f"💡 Optimization suggestion for {pattern_str}: {optimization}"
                )

                # Store optimization suggestion
                self.coordinator.store_pattern(
                    "optimization",
                    {
                        "original_pattern": pattern_str,
                        "optimization": optimization,
                        "frequency": pattern.frequency,
                    },
                )

        except Exception as e:
            logger.error(f"Workflow optimization error: {e}")

    async def _update_pattern_database(self):
        """Update persistent pattern database"""
        while self.running:
            try:
                # Store learned patterns in Redis
                await self._persist_patterns()

                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Pattern database update error: {e}")
                await asyncio.sleep(30)

    async def _persist_patterns(self):
        """Persist learned patterns to Redis"""
        try:
            # Store keystroke patterns
            for pattern_str, pattern in self.keystroke_patterns.items():
                pattern_data = {
                    "type": "keystroke_pattern",
                    "pattern": pattern_str,
                    "frequency": pattern.frequency,
                    "semantic_meaning": pattern.semantic_meaning or "",
                    "context": json.dumps(pattern.context),
                }
                self.coordinator.store_pattern("keystroke", pattern_data)

            # Store workflow patterns
            for workflow_str, workflow in self.workflow_patterns.items():
                workflow_data = {
                    "type": "workflow_pattern",
                    "sequence": workflow_str,
                    "frequency": workflow.frequency,
                    "semantic_intent": workflow.semantic_intent,
                    "steps": json.dumps(workflow.steps),
                }
                self.coordinator.store_pattern("workflow", workflow_data)

            logger.debug("💾 Patterns persisted to Redis")

        except Exception as e:
            logger.error(f"Pattern persistence error: {e}")

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            "running": self.running,
            "patterns_discovered": self.patterns_discovered,
            "workflows_synthesized": self.workflows_synthesized,
            "mappings_created": self.mappings_created,
            "active_keystroke_patterns": len(self.keystroke_patterns),
            "active_workflow_patterns": len(self.workflow_patterns),
            "active_semantic_mappings": len(self.semantic_mappings),
            "claude_available": claude_integration.is_available(),
        }

    def stop(self):
        """Stop the semantic understanding engine"""
        self.running = False
        logger.info("🛑 Semantic Understanding Engine stopped")

        stats = self.get_learning_stats()
        logger.info(
            f"📊 Learning stats: {stats['patterns_discovered']} patterns, {stats['workflows_synthesized']} workflows"
        )


# Global semantic engine
semantic_understanding_engine = SemanticUnderstandingEngine()


async def main():
    """Demo the Semantic Understanding Engine"""
    print("🧠 SEMANTIC UNDERSTANDING ENGINE")
    print("=" * 60)
    print("Learning patterns from real usage")
    print("=" * 60)

    # Start learning
    learning_task = asyncio.create_task(semantic_understanding_engine.start_learning())

    print("✅ Semantic learning started")
    print(
        "🧠 Claude integration:",
        "✅ Active" if claude_integration.is_available() else "❌ Unavailable",
    )
    print("📚 Learning keystroke patterns and workflows")
    print("🔍 Discovering semantic equivalences")
    print("💡 Generating optimization suggestions")
    print("🛑 Press Ctrl+C to stop")

    try:
        while True:
            await asyncio.sleep(15)

            # Show learning stats
            stats = semantic_understanding_engine.get_learning_stats()
            if stats["patterns_discovered"] > 0 or stats["workflows_synthesized"] > 0:
                print(
                    f"📊 Learning: {stats['patterns_discovered']} patterns, "
                    f"{stats['workflows_synthesized']} workflows, "
                    f"{stats['mappings_created']} mappings"
                )

    except KeyboardInterrupt:
        print("\n🛑 Stopping Semantic Understanding Engine...")
        semantic_understanding_engine.stop()
        await learning_task
        print("✅ Semantic Understanding Engine stopped")


if __name__ == "__main__":
    asyncio.run(main())
