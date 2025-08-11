#!/usr/bin/env python3
"""
Workflow Learning Agent with Pattern Recognition
Learns from user behavior patterns and predicts workflow sequences
"""

import redis
import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import re
import fastmcp


@dataclass
class WorkflowEvent:
    timestamp: float
    event_type: str  # 'buffer_switch', 'command_execute', 'text_insert', 'navigation'
    context: Dict[str, str]  # buffer, command, position, etc.
    session_id: str
    sequence_id: int


@dataclass
class WorkflowPattern:
    pattern_id: str
    events: List[str]  # sequence of event types
    frequency: int
    confidence: float
    contexts: List[Dict[str, str]]
    last_seen: float
    success_rate: float


class PatternRecognizer:
    def __init__(self, min_pattern_length: int = 2, max_pattern_length: int = 8):
        self.min_length = min_pattern_length
        self.max_length = max_pattern_length
        self.patterns = {}
        self.sequence_buffer = deque(maxlen=50)  # Recent events for pattern matching

    def add_event(self, event: WorkflowEvent):
        """Add event to sequence buffer for pattern analysis"""
        self.sequence_buffer.append(event)
        self._update_patterns()

    def _update_patterns(self):
        """Analyze recent events for patterns"""
        if len(self.sequence_buffer) < self.min_length:
            return

        # Extract event type sequences
        event_types = [event.event_type for event in self.sequence_buffer]

        # Find patterns of different lengths
        for length in range(
            self.min_length, min(self.max_length + 1, len(event_types))
        ):
            for i in range(len(event_types) - length + 1):
                pattern_seq = tuple(event_types[i : i + length])
                pattern_id = hashlib.md5(str(pattern_seq).encode()).hexdigest()[:12]

                if pattern_id in self.patterns:
                    self.patterns[pattern_id].frequency += 1
                    self.patterns[pattern_id].last_seen = time.time()
                else:
                    # Extract contexts for this pattern
                    contexts = [
                        event.context
                        for event in list(self.sequence_buffer)[i : i + length]
                    ]

                    self.patterns[pattern_id] = WorkflowPattern(
                        pattern_id=pattern_id,
                        events=list(pattern_seq),
                        frequency=1,
                        confidence=0.1,  # Start low, increase with frequency
                        contexts=contexts,
                        last_seen=time.time(),
                        success_rate=1.0,
                    )

    def get_frequent_patterns(self, min_frequency: int = 3) -> List[WorkflowPattern]:
        """Get patterns that occur frequently"""
        frequent = []
        for pattern in self.patterns.values():
            if pattern.frequency >= min_frequency:
                # Update confidence based on frequency and recency
                recency_factor = max(
                    0.1, 1.0 - (time.time() - pattern.last_seen) / (24 * 3600)
                )
                pattern.confidence = min(0.95, pattern.frequency * 0.1 * recency_factor)
                frequent.append(pattern)

        return sorted(frequent, key=lambda p: p.confidence, reverse=True)

    def predict_next_event(
        self, recent_events: List[str]
    ) -> Optional[Tuple[str, float]]:
        """Predict next event type based on recent sequence"""
        if not recent_events:
            return None

        best_match = None
        best_confidence = 0.0

        for pattern in self.patterns.values():
            if pattern.frequency < 2:  # Skip rare patterns
                continue

            # Check if recent events match start of this pattern
            pattern_events = pattern.events
            for i in range(len(pattern_events) - 1):
                if (
                    len(recent_events) >= i + 1
                    and recent_events[-i - 1 :] == pattern_events[: i + 1]
                ):

                    next_event = pattern_events[i + 1]
                    confidence = pattern.confidence * (pattern.frequency / 10.0)

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = next_event

        return (best_match, best_confidence) if best_match else None


class WorkflowLearningAgent:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.Redis(decode_responses=True)
        self.pattern_recognizer = PatternRecognizer()
        self.session_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:12]
        self.sequence_counter = 0
        self.active_workflows = {}  # Track ongoing workflow sequences

    def record_event(self, event_type: str, context: Dict[str, str]) -> str:
        """Record a workflow event"""
        self.sequence_counter += 1

        event = WorkflowEvent(
            timestamp=time.time(),
            event_type=event_type,
            context=context,
            session_id=self.session_id,
            sequence_id=self.sequence_counter,
        )

        # Add to pattern recognizer
        self.pattern_recognizer.add_event(event)

        # Store in Redis (convert to strings for Redis)
        event_data = {
            "timestamp": str(event.timestamp),
            "event_type": event.event_type,
            "context": json.dumps(event.context),
            "session_id": event.session_id,
            "sequence_id": str(event.sequence_id),
        }
        self.redis_client.xadd("workflow:events", event_data)

        # Update pattern storage in Redis
        self._update_redis_patterns()

        return f"event_{self.sequence_counter}"

    def get_workflow_predictions(
        self, recent_context: List[Dict[str, str]]
    ) -> List[Dict[str, any]]:
        """Get predictions for next workflow steps"""
        # Extract recent event types
        recent_events = [
            self._classify_event_from_context(ctx) for ctx in recent_context
        ]

        predictions = []

        # Get pattern-based prediction
        next_prediction = self.pattern_recognizer.predict_next_event(recent_events)
        if next_prediction:
            event_type, confidence = next_prediction
            predictions.append(
                {
                    "type": "pattern_based",
                    "predicted_event": event_type,
                    "confidence": confidence,
                    "reasoning": f"Pattern match based on {len(recent_events)} recent events",
                }
            )

        # Get context-based predictions
        context_predictions = self._get_context_predictions(recent_context)
        predictions.extend(context_predictions)

        return sorted(predictions, key=lambda p: p["confidence"], reverse=True)

    def _get_context_predictions(
        self, recent_context: List[Dict[str, str]]
    ) -> List[Dict[str, any]]:
        """Get predictions based on context analysis"""
        predictions = []

        if not recent_context:
            return predictions

        latest_context = recent_context[-1]

        # Buffer-based predictions
        if "buffer" in latest_context:
            buffer_name = latest_context["buffer"]

            if buffer_name.endswith(".py"):
                predictions.append(
                    {
                        "type": "context_based",
                        "predicted_event": "command_execute",
                        "confidence": 0.7,
                        "reasoning": "Python file suggests testing or running code",
                        "suggested_commands": ["python", "pytest", "run-python"],
                    }
                )
            elif buffer_name.endswith(".org"):
                predictions.append(
                    {
                        "type": "context_based",
                        "predicted_event": "navigation",
                        "confidence": 0.6,
                        "reasoning": "Org file suggests section navigation or TODO management",
                        "suggested_commands": ["org-next-visible-heading", "org-todo"],
                    }
                )

        # Command sequence predictions
        if len(recent_context) >= 2:
            last_two = recent_context[-2:]
            if all("command" in ctx for ctx in last_two):
                commands = [ctx["command"] for ctx in last_two]
                if "save-buffer" in commands:
                    predictions.append(
                        {
                            "type": "sequence_based",
                            "predicted_event": "command_execute",
                            "confidence": 0.8,
                            "reasoning": "Save often followed by git or test commands",
                            "suggested_commands": ["magit-status", "compile", "test"],
                        }
                    )

        return predictions

    def get_workflow_insights(self) -> Dict[str, any]:
        """Get insights about learned workflow patterns"""
        patterns = self.pattern_recognizer.get_frequent_patterns()

        # Analyze pattern types
        pattern_types = defaultdict(int)
        command_sequences = []
        buffer_switches = []

        for pattern in patterns:
            # Classify pattern
            if "command_execute" in pattern.events:
                pattern_types["command_heavy"] += 1
                if all(e == "command_execute" for e in pattern.events):
                    command_sequences.append(pattern)
            if "buffer_switch" in pattern.events:
                pattern_types["navigation_heavy"] += 1
                if all(e in ["buffer_switch", "navigation"] for e in pattern.events):
                    buffer_switches.append(pattern)

        # Find most common patterns
        top_patterns = patterns[:5]

        return {
            "total_patterns": len(patterns),
            "pattern_types": dict(pattern_types),
            "top_patterns": [
                {
                    "events": p.events,
                    "frequency": p.frequency,
                    "confidence": p.confidence,
                }
                for p in top_patterns
            ],
            "command_sequences": len(command_sequences),
            "navigation_patterns": len(buffer_switches),
            "session_events": self.sequence_counter,
        }


# FastMCP Server
mcp = fastmcp.FastMCP("workflow-learning")
agent = WorkflowLearningAgent()


@mcp.tool()
def record_workflow_event(event_type: str, context: dict) -> str:
    """Record a workflow event for pattern learning"""
    event_id = agent.record_event(event_type, context)
    return f"✅ Recorded {event_type} event: {event_id}"


@mcp.tool()
def get_workflow_predictions(recent_context: list) -> str:
    """Get predictions for next workflow steps based on recent activity"""
    predictions = agent.get_workflow_predictions(recent_context or [])

    if not predictions:
        return "🔮 No workflow predictions available yet. Need more events to learn patterns."

    result = "🔮 **WORKFLOW PREDICTIONS**\n\n"

    for i, pred in enumerate(predictions[:3], 1):
        result += f"**{i}. {pred['predicted_event']}**\n"
        result += f"   Confidence: {pred['confidence']:.2f}\n"
        result += f"   Type: {pred['type']}\n"
        result += f"   Reasoning: {pred['reasoning']}\n"

        if "suggested_commands" in pred:
            result += f"   Suggested: {', '.join(pred['suggested_commands'])}\n"
        result += "\n"

    return result


@mcp.tool()
def get_workflow_patterns() -> str:
    """Get learned workflow patterns and insights"""
    insights = agent.get_workflow_insights()

    result = "📊 **WORKFLOW LEARNING INSIGHTS**\n\n"
    result += f"**Total Patterns Learned:** {insights['total_patterns']}\n"
    result += f"**Session Events:** {insights['session_events']}\n"
    result += f"**Command Sequences:** {insights['command_sequences']}\n"
    result += f"**Navigation Patterns:** {insights['navigation_patterns']}\n\n"

    if insights["top_patterns"]:
        result += "**Top Patterns:**\n"
        for i, pattern in enumerate(insights["top_patterns"], 1):
            events_str = " → ".join(pattern["events"])
            result += f"{i}. {events_str} (×{pattern['frequency']}, {pattern['confidence']:.2f})\n"

    return result


@mcp.tool()
def simulate_workflow_learning() -> str:
    """Simulate workflow learning with sample events"""
    # Simulate common development workflow
    sample_events = [
        ("buffer_switch", {"buffer": "main.py", "previous_buffer": "*scratch*"}),
        (
            "text_insert",
            {"buffer": "main.py", "text": "def hello():", "position": "100"},
        ),
        ("command_execute", {"command": "save-buffer", "buffer": "main.py"}),
        ("buffer_switch", {"buffer": "*shell*", "previous_buffer": "main.py"}),
        ("command_execute", {"command": "shell-command", "text": "python main.py"}),
        ("buffer_switch", {"buffer": "main.py", "previous_buffer": "*shell*"}),
        (
            "text_insert",
            {"buffer": "main.py", "text": 'print("Hello")', "position": "120"},
        ),
        ("command_execute", {"command": "save-buffer", "buffer": "main.py"}),
        ("command_execute", {"command": "shell-command", "text": "python main.py"}),
    ]

    for event_type, context in sample_events:
        agent.record_event(event_type, context)
        time.sleep(0.1)  # Small delay to create time sequence

    insights = agent.get_workflow_insights()
    return f"✅ Simulated {len(sample_events)} workflow events. Learned {insights['total_patterns']} patterns."


@mcp.tool()
def clear_workflow_data() -> str:
    """Clear all workflow learning data"""
    agent.pattern_recognizer.patterns.clear()
    agent.pattern_recognizer.sequence_buffer.clear()
    agent.sequence_counter = 0

    # Clear Redis data
    try:
        keys = agent.redis_client.keys("workflow:*")
        if keys:
            agent.redis_client.delete(*keys)
    except Exception as e:
        pass  # Redis might not be available

    return "🧹 Cleared all workflow learning data"


if __name__ == "__main__":
    print("🧠 Starting Workflow Learning Agent FastMCP Server")
    mcp.run()
