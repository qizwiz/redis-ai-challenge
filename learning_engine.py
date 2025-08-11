#!/usr/bin/env python3
"""
Learning Engine - Real pattern discovery from facade observations

This implements actual learning algorithms that discover patterns, predict
user behavior, and evolve the system's understanding of development workflows.
"""

import redis
import json
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta
import re


@dataclass
class Pattern:
    """A discovered behavioral pattern"""

    pattern_id: str
    pattern_type: str
    description: str
    confidence: float
    frequency: int
    last_seen: float
    conditions: Dict[str, Any] = field(default_factory=dict)
    outcomes: Dict[str, Any] = field(default_factory=dict)
    predictions: Dict[str, float] = field(default_factory=dict)


@dataclass
class LearningEvent:
    """A learning event from user behavior"""

    timestamp: float
    event_type: str
    context: Dict[str, Any]
    sequence_id: str
    user_intent: Optional[str] = None


class SequenceAnalyzer:
    """Analyzes sequences of user actions to discover patterns"""

    def __init__(self):
        self.sequences = defaultdict(list)
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.pattern_cache = {}

    def add_event(self, event: LearningEvent):
        """Add event to sequence analysis"""
        seq_id = event.sequence_id
        self.sequences[seq_id].append(event)

        # Update transition matrix
        if len(self.sequences[seq_id]) > 1:
            prev_event = self.sequences[seq_id][-2]
            current_event = event

            prev_type = f"{prev_event.event_type}:{prev_event.context.get('buffer_type', 'unknown')}"
            curr_type = f"{current_event.event_type}:{current_event.context.get('buffer_type', 'unknown')}"

            self.transitions[prev_type][curr_type] += 1

    def discover_sequences(self, min_frequency: int = 3) -> List[Pattern]:
        """Discover frequent sequences"""
        patterns = []

        # Find common sequences of length 2-5
        for length in range(2, 6):
            sequence_counts = defaultdict(int)

            for seq_id, events in self.sequences.items():
                if len(events) >= length:
                    for i in range(len(events) - length + 1):
                        subseq = tuple(e.event_type for e in events[i : i + length])
                        sequence_counts[subseq] += 1

            # Create patterns for frequent sequences
            for sequence, count in sequence_counts.items():
                if count >= min_frequency:
                    pattern_id = f"seq_{'_'.join(sequence)}_{count}"

                    patterns.append(
                        Pattern(
                            pattern_id=pattern_id,
                            pattern_type="sequence",
                            description=f"User often does: {' → '.join(sequence)}",
                            confidence=min(count / 10.0, 1.0),
                            frequency=count,
                            last_seen=time.time(),
                            conditions={"sequence": sequence, "length": length},
                            predictions={
                                "next_action": self._predict_next_action(sequence),
                                "completion_probability": count
                                / max(sum(sequence_counts.values()), 1),
                            },
                        )
                    )

        return patterns


class BufferPatternAnalyzer:
    """Analyzes patterns within different buffer types"""

    def __init__(self):
        self.buffer_behaviors = defaultdict(lambda: defaultdict(list))
        self.code_patterns = defaultdict(int)
        self.editing_patterns = defaultdict(list)

    def analyze_buffer_event(self, event: LearningEvent) -> List[Pattern]:
        """Analyze event within buffer context"""
        patterns = []

        buffer_name = event.context.get("buffer", "unknown")
        buffer_type = self._classify_buffer(buffer_name)

        # Store behavior by buffer type
        self.buffer_behaviors[buffer_type]["events"].append(event)

        # Analyze code editing patterns
        if buffer_type in ["python", "javascript", "elisp"]:
            patterns.extend(self._analyze_code_patterns(event, buffer_type))

        # Analyze navigation patterns
        if event.event_type in ["point_movement", "buffer_switch"]:
            patterns.extend(self._analyze_navigation_patterns(event))

        return patterns

    def _analyze_code_patterns(
        self, event: LearningEvent, buffer_type: str
    ) -> List[Pattern]:
        """Analyze code editing patterns"""
        patterns = []

        # Look for common coding sequences
        recent_commands = event.context.get("recent_commands", [])
        if len(recent_commands) >= 2:
            command_seq = tuple(recent_commands[-2:])

            pattern_key = f"{buffer_type}_{command_seq}"
            self.code_patterns[pattern_key] += 1

            if self.code_patterns[pattern_key] >= 3:  # Seen at least 3 times
                patterns.append(
                    Pattern(
                        pattern_id=f"code_{pattern_key}",
                        pattern_type="coding_habit",
                        description=f"In {buffer_type} files, user often: {' then '.join(command_seq)}",
                        confidence=min(self.code_patterns[pattern_key] / 10.0, 1.0),
                        frequency=self.code_patterns[pattern_key],
                        last_seen=time.time(),
                        conditions={
                            "buffer_type": buffer_type,
                            "command_sequence": command_seq,
                        },
                    )
                )

        return patterns

    def _analyze_navigation_patterns(self, event: LearningEvent) -> List[Pattern]:
        """Analyze navigation patterns"""
        patterns = []

        # Track common navigation sequences
        if event.event_type == "buffer_switch":
            from_buffer = event.context.get("from_buffer")
            to_buffer = event.context.get("to_buffer")

            if from_buffer and to_buffer:
                nav_key = f"{from_buffer}→{to_buffer}"

                # Store navigation
                self.editing_patterns["navigation"].append(
                    {"from": from_buffer, "to": to_buffer, "timestamp": event.timestamp}
                )

                # Count frequency
                nav_count = sum(
                    1
                    for nav in self.editing_patterns["navigation"]
                    if f"{nav['from']}→{nav['to']}" == nav_key
                )

                if nav_count >= 3:
                    patterns.append(
                        Pattern(
                            pattern_id=f"nav_{nav_key}",
                            pattern_type="navigation_pattern",
                            description=f"User frequently switches from {from_buffer} to {to_buffer}",
                            confidence=min(nav_count / 10.0, 1.0),
                            frequency=nav_count,
                            last_seen=time.time(),
                            conditions={
                                "from_buffer": from_buffer,
                                "to_buffer": to_buffer,
                            },
                        )
                    )

        return patterns


class WorkflowAnalyzer:
    """Analyzes high-level development workflows"""

    def __init__(self):
        self.workflow_sessions = []
        self.project_patterns = defaultdict(list)
        self.time_patterns = defaultdict(list)

    def analyze_workflow_session(self, events: List[LearningEvent]) -> List[Pattern]:
        """Analyze a complete workflow session"""
        patterns = []

        if len(events) < 5:  # Need meaningful session
            return patterns

        session_start = min(e.timestamp for e in events)
        session_end = max(e.timestamp for e in events)
        session_duration = session_end - session_start

        # Classify session type
        session_type = self._classify_session(events)

        # Analyze session patterns
        patterns.extend(self._analyze_session_flow(events, session_type))
        patterns.extend(self._analyze_productivity_patterns(events, session_duration))

        return patterns

    def _analyze_session_flow(
        self, events: List[LearningEvent], session_type: str
    ) -> List[Pattern]:
        """Analyze flow within session"""
        patterns = []

        # Look for common workflow phases
        phases = self._identify_workflow_phases(events)

        if len(phases) >= 2:
            phase_sequence = tuple(phase["type"] for phase in phases)

            patterns.append(
                Pattern(
                    pattern_id=f"workflow_{session_type}_{'_'.join(phase_sequence)}",
                    pattern_type="workflow_pattern",
                    description=f"During {session_type} sessions, user workflow: {' → '.join(phase_sequence)}",
                    confidence=0.8,
                    frequency=1,  # Would accumulate over time
                    last_seen=time.time(),
                    conditions={"session_type": session_type, "phases": phase_sequence},
                    predictions={
                        "estimated_duration": sum(p["duration"] for p in phases)
                    },
                )
            )

        return patterns

    def _identify_workflow_phases(
        self, events: List[LearningEvent]
    ) -> List[Dict[str, Any]]:
        """Identify distinct phases in workflow"""
        phases = []

        if not events:
            return phases

        current_phase = {
            "type": "exploration",
            "start": events[0].timestamp,
            "events": [],
        }

        for event in events:
            buffer_type = event.context.get("buffer_type", "unknown")

            # Determine phase type
            if buffer_type in ["python", "javascript", "elisp"]:
                phase_type = "coding"
            elif buffer_type == "git":
                phase_type = "version_control"
            elif event.event_type in ["buffer_switch", "point_movement"]:
                phase_type = "exploration"
            else:
                phase_type = "other"

            # Check if phase changed
            if phase_type != current_phase["type"]:
                # Finish current phase
                current_phase["end"] = event.timestamp
                current_phase["duration"] = (
                    current_phase["end"] - current_phase["start"]
                )
                phases.append(current_phase)

                # Start new phase
                current_phase = {
                    "type": phase_type,
                    "start": event.timestamp,
                    "events": [],
                }

            current_phase["events"].append(event)

        # Finish last phase
        if current_phase["events"]:
            current_phase["end"] = events[-1].timestamp
            current_phase["duration"] = current_phase["end"] - current_phase["start"]
            phases.append(current_phase)

        return phases

    def _analyze_productivity_patterns(
        self, events: List[LearningEvent], duration: float
    ) -> List[Pattern]:
        """Analyze productivity patterns"""
        patterns = []

        # Calculate activity metrics
        events_per_minute = len(events) / (duration / 60) if duration > 0 else 0
        unique_buffers = len(set(e.context.get("buffer", "") for e in events))

        # Classify productivity level
        if events_per_minute > 5 and unique_buffers > 3:
            productivity = "high"
        elif events_per_minute > 2:
            productivity = "medium"
        else:
            productivity = "low"

        patterns.append(
            Pattern(
                pattern_id=f"productivity_{productivity}_{int(duration)}s",
                pattern_type="productivity_pattern",
                description=f"User shows {productivity} productivity: {events_per_minute:.1f} actions/min across {unique_buffers} buffers",
                confidence=0.7,
                frequency=1,
                last_seen=time.time(),
                conditions={
                    "productivity_level": productivity,
                    "session_duration": duration,
                },
                predictions={"expected_actions_per_minute": events_per_minute},
            )
        )

        return patterns


class LearningEngine:
    """Main learning engine that coordinates all analyzers"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

        # Analyzers
        self.sequence_analyzer = SequenceAnalyzer()
        self.buffer_analyzer = BufferPatternAnalyzer()
        self.workflow_analyzer = WorkflowAnalyzer()

        # Learning state
        self.discovered_patterns = {}
        self.learning_events = deque(maxlen=1000)  # Keep recent events
        self.active_sessions = {}

        # Pattern storage
        self.patterns_key = "learning:patterns"
        self.events_key = "learning:events"

    def process_facade_observation(self, facade_data: Dict[str, Any]) -> List[Pattern]:
        """Process facade observation and discover patterns"""
        # Convert facade data to learning event
        event = self._create_learning_event(facade_data)

        if not event:
            return []

        # Add to analyzers
        self.sequence_analyzer.add_event(event)
        self.learning_events.append(event)

        # Discover patterns
        new_patterns = []

        # Sequence patterns
        new_patterns.extend(self.sequence_analyzer.discover_sequences())

        # Buffer patterns
        new_patterns.extend(self.buffer_analyzer.analyze_buffer_event(event))

        # Workflow patterns (analyze recent session)
        recent_events = list(self.learning_events)[-20:]  # Last 20 events
        if len(recent_events) >= 10:
            new_patterns.extend(
                self.workflow_analyzer.analyze_workflow_session(recent_events)
            )

        # Store new patterns
        for pattern in new_patterns:
            self.discovered_patterns[pattern.pattern_id] = pattern
            self._persist_pattern(pattern)

        return new_patterns

    def _create_learning_event(
        self, facade_data: Dict[str, Any]
    ) -> Optional[LearningEvent]:
        """Convert facade data to learning event"""
        if not facade_data:
            return None

        # Determine event type
        current_buffer = facade_data.get("current_buffer", "")
        last_command = facade_data.get("last_command", "none")

        if last_command and last_command != "none":
            event_type = "command_execution"
        elif current_buffer:
            event_type = "buffer_activity"
        else:
            event_type = "idle"

        # Create context
        context = {
            "buffer": current_buffer,
            "buffer_type": self.buffer_analyzer._classify_buffer(current_buffer),
            "point": facade_data.get("cursor_position", 0),
            "line": facade_data.get("cursor_line", 0),
            "column": facade_data.get("cursor_column", 0),
            "major_mode": facade_data.get("major_mode", ""),
            "minor_modes_count": len(facade_data.get("minor_modes", [])),
            "window_count": facade_data.get("window_count", 1),
            "last_command": last_command,
            "recent_commands": [last_command] if last_command != "none" else [],
        }

        # Generate sequence ID (session-like grouping)
        session_id = f"session_{int(time.time() / 600)}"  # 10-minute sessions

        return LearningEvent(
            timestamp=facade_data.get("timestamp", time.time()),
            event_type=event_type,
            context=context,
            sequence_id=session_id,
        )

    def get_discovered_patterns(self, pattern_type: str = None) -> List[Pattern]:
        """Get discovered patterns"""
        if pattern_type:
            return [
                p
                for p in self.discovered_patterns.values()
                if p.pattern_type == pattern_type
            ]
        return list(self.discovered_patterns.values())

    def predict_next_action(
        self, current_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Predict user's next action based on learned patterns"""
        # Find relevant patterns
        relevant_patterns = []

        for pattern in self.discovered_patterns.values():
            if self._pattern_matches_context(pattern, current_context):
                relevant_patterns.append(pattern)

        if not relevant_patterns:
            return None

        # Get highest confidence pattern
        best_pattern = max(relevant_patterns, key=lambda p: p.confidence)

        return {
            "predicted_action": best_pattern.predictions.get("next_action", "unknown"),
            "confidence": best_pattern.confidence,
            "pattern_description": best_pattern.description,
            "pattern_type": best_pattern.pattern_type,
        }

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learning progress"""
        patterns_by_type = defaultdict(int)
        total_confidence = 0

        for pattern in self.discovered_patterns.values():
            patterns_by_type[pattern.pattern_type] += 1
            total_confidence += pattern.confidence

        avg_confidence = (
            total_confidence / len(self.discovered_patterns)
            if self.discovered_patterns
            else 0
        )

        return {
            "total_patterns": len(self.discovered_patterns),
            "patterns_by_type": dict(patterns_by_type),
            "average_confidence": avg_confidence,
            "total_events_processed": len(self.learning_events),
            "learning_active": True,
        }


def demo_learning_engine():
    """Demo the learning engine with simulated data"""
    print("🧠 LEARNING ENGINE DEMO")
    print("=" * 30)

    # Setup
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    engine = LearningEngine(redis_client)

    # Simulate facade observations
    print("📊 Processing simulated facade observations...")

    # Simulate coding session
    observations = [
        {
            "timestamp": time.time(),
            "current_buffer": "main.py",
            "cursor_position": 100,
            "last_command": "self-insert-command",
        },
        {
            "timestamp": time.time() + 1,
            "current_buffer": "main.py",
            "cursor_position": 150,
            "last_command": "newline",
        },
        {
            "timestamp": time.time() + 2,
            "current_buffer": "test.py",
            "cursor_position": 50,
            "last_command": "buffer-switch",
        },
        {
            "timestamp": time.time() + 3,
            "current_buffer": "test.py",
            "cursor_position": 80,
            "last_command": "self-insert-command",
        },
        {
            "timestamp": time.time() + 4,
            "current_buffer": "main.py",
            "cursor_position": 200,
            "last_command": "buffer-switch",
        },
    ]

    # Process observations
    all_patterns = []
    for obs in observations:
        patterns = engine.process_facade_observation(obs)
        all_patterns.extend(patterns)

    print(f"📈 Discovered {len(all_patterns)} patterns:")
    for pattern in all_patterns:
        print(f"  • {pattern.description} (confidence: {pattern.confidence:.2f})")

    # Test prediction
    print("\n🔮 Testing prediction...")
    current_context = {"buffer": "main.py", "last_command": "self-insert-command"}
    prediction = engine.predict_next_action(current_context)

    if prediction:
        print(
            f"   Predicted: {prediction['predicted_action']} (confidence: {prediction['confidence']:.2f})"
        )
        print(f"   Based on: {prediction['pattern_description']}")
    else:
        print("   No prediction available yet")

    # Show learning summary
    summary = engine.get_learning_summary()
    print(f"\n📊 Learning Summary:")
    print(f"   Total patterns: {summary['total_patterns']}")
    print(f"   Average confidence: {summary['average_confidence']:.2f}")
    print(f"   Events processed: {summary['total_events_processed']}")

    print("\n✅ Learning engine demo complete")


if __name__ == "__main__":
    demo_learning_engine()
