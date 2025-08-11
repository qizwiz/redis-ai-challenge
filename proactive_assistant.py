#!/usr/bin/env python3
"""
Proactive Development Assistant - AI that actively helps with development

This system uses semantic code analysis and learned patterns to proactively
suggest helpful actions, anticipate needs, and guide development workflows.
"""

import redis
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from semantic_code_analyzer import SemanticCodeAnalyzer
from intelligent_response_engine import IntelligentResponseEngine, DevelopmentContext


@dataclass
class ProactiveAction:
    """A proactive action suggestion"""

    action_id: str
    action_type: str  # suggestion, automation, warning, optimization
    title: str
    description: str
    reasoning: str
    confidence: float
    priority: int  # 1-5, 5 being highest
    context: Dict[str, Any] = field(default_factory=dict)
    prerequisites: List[str] = field(default_factory=list)
    estimated_time: Optional[str] = None
    category: str = "general"


@dataclass
class DevelopmentSession:
    """Tracks a development session for proactive assistance"""

    session_id: str
    start_time: float
    current_buffer: str
    files_touched: List[str] = field(default_factory=list)
    commands_executed: List[str] = field(default_factory=list)
    patterns_observed: List[str] = field(default_factory=list)
    errors_encountered: List[str] = field(default_factory=list)
    phase: str = "exploration"  # exploration, implementation, testing, debugging
    focus_area: str = "unknown"


class PatternBasedAssistant:
    """Provides assistance based on learned patterns"""

    def __init__(self):
        self.common_workflows = {
            "python_feature_development": [
                "Write function signature",
                "Implement logic",
                "Add docstring",
                "Write tests",
                "Run tests",
                "Handle edge cases",
            ],
            "api_development": [
                "Define endpoint",
                "Add validation",
                "Implement handler",
                "Add error handling",
                "Write tests",
                "Update documentation",
            ],
            "bug_fixing": [
                "Reproduce issue",
                "Identify root cause",
                "Implement fix",
                "Add regression test",
                "Verify fix",
                "Update documentation",
            ],
        }

    def suggest_next_steps(
        self, session: DevelopmentSession, project_context: Dict[str, Any]
    ) -> List[ProactiveAction]:
        """Suggest next steps based on patterns"""
        suggestions = []

        # Analyze current development phase
        if session.phase == "implementation":
            suggestions.extend(
                self._suggest_implementation_actions(session, project_context)
            )
        elif session.phase == "testing":
            suggestions.extend(self._suggest_testing_actions(session, project_context))
        elif session.phase == "debugging":
            suggestions.extend(
                self._suggest_debugging_actions(session, project_context)
            )

        return suggestions

    def _suggest_implementation_actions(
        self, session: DevelopmentSession, context: Dict[str, Any]
    ) -> List[ProactiveAction]:
        """Suggest implementation-related actions"""
        actions = []

        current_file = session.current_buffer

        # Test coverage suggestion
        if context["architecture"]["test_coverage"] < 0.5:  # Less than 50%
            actions.append(
                ProactiveAction(
                    action_id="suggest_write_tests",
                    action_type="suggestion",
                    title="Write Tests",
                    description=f"Consider writing tests for {current_file}. Your project has {context['architecture']['test_coverage']:.1%} test coverage.",
                    reasoning="Low test coverage detected, and you're actively implementing features",
                    confidence=0.8,
                    priority=4,
                    category="testing",
                    estimated_time="10-15 minutes",
                )
            )

        # Documentation suggestion
        if context["architecture"]["documentation_coverage"] < 0.8:
            actions.append(
                ProactiveAction(
                    action_id="suggest_add_docstrings",
                    action_type="suggestion",
                    title="Add Documentation",
                    description="Add docstrings to your functions and classes for better maintainability",
                    reasoning="Some functions lack documentation",
                    confidence=0.6,
                    priority=2,
                    category="documentation",
                    estimated_time="5-10 minutes",
                )
            )

        return actions


class ContextualAssistant:
    """Provides assistance based on current context"""

    def __init__(self, semantic_analyzer: SemanticCodeAnalyzer):
        self.semantic_analyzer = semantic_analyzer

    def analyze_current_context(
        self, session: DevelopmentSession
    ) -> List[ProactiveAction]:
        """Analyze current context for assistance opportunities"""
        actions = []

        current_file = session.current_buffer

        # File-specific suggestions
        if current_file.endswith(".py"):
            actions.extend(self._analyze_python_context(session))
        elif current_file.endswith(".md"):
            actions.extend(self._analyze_documentation_context(session))
        elif "test" in current_file.lower():
            actions.extend(self._analyze_test_context(session))

        return actions

    def _analyze_python_context(
        self, session: DevelopmentSession
    ) -> List[ProactiveAction]:
        """Analyze Python file context"""
        actions = []

        # Suggest imports if working on new functionality
        if any(
            cmd in session.commands_executed
            for cmd in ["self-insert-command", "newline"]
        ):
            actions.append(
                ProactiveAction(
                    action_id="suggest_imports",
                    action_type="suggestion",
                    title="Check Imports",
                    description="Make sure you have all necessary imports for the functionality you're implementing",
                    reasoning="Active coding detected",
                    confidence=0.6,
                    priority=2,
                    category="code_quality",
                )
            )

        # Suggest error handling
        if "def " in str(session.commands_executed):  # Function definition detected
            actions.append(
                ProactiveAction(
                    action_id="suggest_error_handling",
                    action_type="suggestion",
                    title="Add Error Handling",
                    description="Consider adding try/except blocks for robust error handling",
                    reasoning="New function detected",
                    confidence=0.7,
                    priority=3,
                    category="code_quality",
                    estimated_time="2-5 minutes",
                )
            )

        return actions


class WorkflowPredictor:
    """Predicts next steps in development workflow"""

    def __init__(self):
        self.workflow_patterns = {
            "feature_development": {
                "typical_sequence": [
                    "design",
                    "implement",
                    "test",
                    "document",
                    "review",
                ],
                "transition_probabilities": {
                    "design": {"implement": 0.8, "research": 0.2},
                    "implement": {"test": 0.6, "debug": 0.3, "document": 0.1},
                    "test": {"debug": 0.4, "document": 0.4, "review": 0.2},
                    "debug": {"test": 0.7, "implement": 0.3},
                    "document": {"review": 0.8, "implement": 0.2},
                },
            }
        }

    def predict_next_phase(
        self, current_phase: str, workflow_type: str = "feature_development"
    ) -> List[ProactiveAction]:
        """Predict next workflow phase"""
        actions = []

        if workflow_type in self.workflow_patterns:
            transitions = self.workflow_patterns[workflow_type][
                "transition_probabilities"
            ]

            if current_phase in transitions:
                for next_phase, probability in transitions[current_phase].items():
                    if probability > 0.5:  # High probability transition
                        action = self._create_phase_transition_action(
                            current_phase, next_phase, probability
                        )
                        actions.append(action)

        return actions

    def _create_phase_transition_action(
        self, current: str, next_phase: str, probability: float
    ) -> ProactiveAction:
        """Create action for phase transition"""

        phase_descriptions = {
            "implement": "Start implementing the planned functionality",
            "test": "Write tests for your implementation",
            "debug": "Debug and fix any issues",
            "document": "Update documentation for your changes",
            "review": "Review your changes before committing",
        }

        return ProactiveAction(
            action_id=f"transition_to_{next_phase}",
            action_type="suggestion",
            title=f"Consider {next_phase.title()}",
            description=phase_descriptions.get(
                next_phase, f"Move to {next_phase} phase"
            ),
            reasoning=f"Common next step after {current} ({probability:.0%} probability)",
            confidence=probability,
            priority=int(probability * 5),
            category="workflow",
        )


class ProactiveDevelopmentAssistant:
    """Main proactive assistant that coordinates all assistance"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.semantic_analyzer = SemanticCodeAnalyzer()
        self.pattern_assistant = PatternBasedAssistant()
        self.contextual_assistant = ContextualAssistant(self.semantic_analyzer)
        self.workflow_predictor = WorkflowPredictor()

        # Session tracking
        self.active_sessions = {}
        self.suggestion_history = {}

    async def analyze_and_suggest(
        self, facade_data: Dict[str, Any], project_root: str
    ) -> List[ProactiveAction]:
        """Analyze current state and provide proactive suggestions"""

        # Get or create session
        session = self._get_or_create_session(facade_data)

        # Update session with current data
        self._update_session(session, facade_data)

        # Get project context
        project_context = self.semantic_analyzer.analyze_project_context(project_root)

        # Gather suggestions from all assistants
        all_suggestions = []

        # Pattern-based suggestions
        pattern_suggestions = self.pattern_assistant.suggest_next_steps(
            session, project_context
        )
        all_suggestions.extend(pattern_suggestions)

        # Contextual suggestions
        contextual_suggestions = self.contextual_assistant.analyze_current_context(
            session
        )
        all_suggestions.extend(contextual_suggestions)

        # Workflow predictions
        workflow_suggestions = self.workflow_predictor.predict_next_phase(session.phase)
        all_suggestions.extend(workflow_suggestions)

        # Project-specific suggestions
        project_suggestions = self._get_project_specific_suggestions(
            session, project_context
        )
        all_suggestions.extend(project_suggestions)

        # Filter and rank suggestions
        filtered_suggestions = self._filter_and_rank_suggestions(
            all_suggestions, session
        )

        # Store suggestions
        self._store_suggestions(session.session_id, filtered_suggestions)

        return filtered_suggestions

    def _infer_development_phase(
        self, session: DevelopmentSession, facade_data: Dict[str, Any]
    ) -> str:
        """Infer current development phase"""

        current_buffer = facade_data.get("current_buffer", "")
        recent_commands = session.commands_executed[-10:]

        # Testing phase
        if "test" in current_buffer.lower() or any(
            "test" in cmd for cmd in recent_commands
        ):
            return "testing"

        # Debugging phase
        if session.errors_encountered or any("debug" in cmd for cmd in recent_commands):
            return "debugging"

        # Implementation phase
        if any(cmd in recent_commands for cmd in ["self-insert-command", "newline"]):
            return "implementation"

        # Documentation phase
        if current_buffer.endswith(".md") or current_buffer.endswith(".org"):
            return "documentation"

        # Default to exploration
        return "exploration"


async def demo_proactive_assistance():
    """Demo proactive development assistance"""
    print("🤖 PROACTIVE DEVELOPMENT ASSISTANCE DEMO")
    print("=" * 50)

    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    assistant = ProactiveDevelopmentAssistant(redis_client)

    # Simulate different development scenarios
    scenarios = [
        {
            "name": "Python Feature Development",
            "facade_data": {
                "current_buffer": "src/handlers.py",
                "last_command": "self-insert-command",
                "cursor_line": 45,
                "minor_modes": ["python-mode", "company-mode"],
            },
            "project_root": os.getcwd(),
        },
        {
            "name": "Test Writing Session",
            "facade_data": {
                "current_buffer": "tests/test_handlers.py",
                "last_command": "newline",
                "cursor_line": 12,
                "minor_modes": ["python-mode", "pytest-mode"],
            },
            "project_root": os.getcwd(),
        },
        {
            "name": "Documentation Update",
            "facade_data": {
                "current_buffer": "README.md",
                "last_command": "self-insert-command",
                "cursor_line": 8,
                "minor_modes": ["markdown-mode"],
            },
            "project_root": os.getcwd(),
        },
    ]

    for scenario in scenarios:
        print(f"\n🎯 SCENARIO: {scenario['name']}")
        print(f"   Context: {scenario['facade_data']['current_buffer']}")

        suggestions = await assistant.analyze_and_suggest(
            scenario["facade_data"], scenario["project_root"]
        )

        print(f"   📋 PROACTIVE SUGGESTIONS:")
        for suggestion in suggestions:
            priority_icon = (
                "🔥"
                if suggestion.priority >= 4
                else "💡" if suggestion.priority >= 3 else "ℹ️"
            )
            print(f"      {priority_icon} {suggestion.title}")
            print(f"         {suggestion.description}")
            print(
                f"         Category: {suggestion.category} | Confidence: {suggestion.confidence:.1%}"
            )
            if suggestion.estimated_time:
                print(f"         Estimated time: {suggestion.estimated_time}")

    print(f"\n✨ PROACTIVE ASSISTANCE CAPABILITIES:")
    print(f"   ✅ Context-aware suggestions based on current development phase")
    print(f"   ✅ Project-specific recommendations (CLI tools, APIs, etc.)")
    print(f"   ✅ Workflow-aware assistance (feature dev → testing → docs)")
    print(f"   ✅ Pattern-based predictions from learned behavior")
    print(f"   ✅ Prioritized suggestions with confidence scoring")
    print(f"   ✅ Time estimates for suggested actions")

    print(f"\n🚀 This creates a truly helpful AI assistant that:")
    print(f"   • Anticipates what you need before you ask")
    print(f"   • Provides actionable, specific suggestions")
    print(f"   • Understands your project architecture and goals")
    print(f"   • Adapts to your development workflow patterns")
    print(f"   • Guides you through best practices automatically")


if __name__ == "__main__":
    import os

    asyncio.run(demo_proactive_assistance())
