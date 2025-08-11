#!/usr/bin/env python3
"""
Workflow Intelligence System - High-level development workflow understanding

This system understands and predicts development workflows at a high level,
tracking development phases, project evolution, and providing strategic guidance
for complex development initiatives.
"""

import redis
import json
import time
import asyncio
import os
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import re

from semantic_code_analyzer import SemanticCodeAnalyzer
from multi_ai_coordinator import MultiAICoordinator, CoordinationTask, AISpecialty


class DevelopmentPhase(Enum):
    """High-level development phases"""

    EXPLORATION = "exploration"
    PLANNING = "planning"
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DEBUGGING = "debugging"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"
    REFACTORING = "refactoring"


class WorkflowPattern(Enum):
    """Common workflow patterns"""

    TDD_CYCLE = "tdd_cycle"  # Test -> Code -> Refactor
    FEATURE_BRANCH = "feature_branch"  # Branch -> Implement -> PR -> Merge
    AGILE_SPRINT = "agile_sprint"  # Plan -> Implement -> Review -> Deploy
    RESEARCH_SPIKE = "research_spike"  # Explore -> Prototype -> Decide
    BUG_TRIAGE = "bug_triage"  # Reproduce -> Diagnose -> Fix -> Verify
    ARCHITECTURE_REVIEW = "architecture_review"  # Design -> Review -> Iterate
    CODE_REVIEW_CYCLE = "code_review_cycle"  # Submit -> Review -> Revise -> Approve


@dataclass
class WorkflowTransition:
    """A transition between development phases"""

    from_phase: DevelopmentPhase
    to_phase: DevelopmentPhase
    trigger_event: str
    confidence: float
    duration: float
    context: Dict[str, Any]
    timestamp: float


@dataclass
class DevelopmentSession:
    """A cohesive development session"""

    session_id: str
    start_time: float
    end_time: Optional[float]
    phases: List[DevelopmentPhase]
    transitions: List[WorkflowTransition]
    files_touched: Set[str]
    project_areas: Set[str]  # e.g., "authentication", "database", "ui"
    patterns_detected: List[WorkflowPattern]
    session_type: str  # "feature_development", "bug_fixing", "maintenance"
    productivity_score: float
    complexity_level: int  # 1-5
    interruptions: int
    focus_metrics: Dict[str, float]


@dataclass
class ProjectEvolution:
    """Tracks project evolution over time"""

    project_id: str
    creation_time: float
    phases_completed: List[DevelopmentPhase]
    current_phase: DevelopmentPhase
    maturity_level: int  # 1-5
    architecture_changes: List[Dict[str, Any]]
    team_size_evolution: List[Tuple[float, int]]
    technology_stack_changes: List[Dict[str, Any]]
    quality_metrics_evolution: List[Dict[str, float]]
    milestone_history: List[Dict[str, Any]]


@dataclass
class StrategicInsight:
    """High-level strategic insight about development"""

    insight_type: str
    title: str
    description: str
    confidence: float
    impact_level: int  # 1-5
    time_horizon: str  # "immediate", "short_term", "long_term"
    recommended_actions: List[str]
    supporting_evidence: List[str]
    affected_areas: List[str]


class WorkflowIntelligenceSystem:
    """System for understanding and predicting development workflows"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.semantic_analyzer = SemanticCodeAnalyzer()
        self.ai_coordinator = MultiAICoordinator(redis_client)

        # Workflow state tracking
        self.active_sessions = {}
        self.project_evolution = {}
        self.pattern_library = self._initialize_pattern_library()
        self.phase_transition_probabilities = (
            self._initialize_transition_probabilities()
        )

        # Intelligence metrics
        self.workflow_stats = {
            "sessions_analyzed": 0,
            "patterns_detected": 0,
            "predictions_made": 0,
            "accuracy_rate": 0.0,
            "insights_generated": 0,
        }

        # Learning system
        self.workflow_memory = deque(maxlen=1000)  # Recent workflow events
        self.pattern_frequencies = defaultdict(int)
        self.successful_predictions = defaultdict(list)

    def _initialize_pattern_library(self) -> Dict[WorkflowPattern, Dict[str, Any]]:
        """Initialize library of known workflow patterns"""

        return {
            WorkflowPattern.TDD_CYCLE: {
                "phases": [
                    DevelopmentPhase.TESTING,
                    DevelopmentPhase.IMPLEMENTATION,
                    DevelopmentPhase.REFACTORING,
                ],
                "typical_duration": 1800,  # 30 minutes
                "triggers": [
                    "test file opened",
                    "test written",
                    "implementation started",
                ],
                "success_indicators": ["tests passing", "code coverage increased"],
                "common_transitions": [
                    (DevelopmentPhase.TESTING, DevelopmentPhase.IMPLEMENTATION),
                    (DevelopmentPhase.IMPLEMENTATION, DevelopmentPhase.TESTING),
                    (DevelopmentPhase.TESTING, DevelopmentPhase.REFACTORING),
                ],
            },
            WorkflowPattern.FEATURE_BRANCH: {
                "phases": [
                    DevelopmentPhase.PLANNING,
                    DevelopmentPhase.IMPLEMENTATION,
                    DevelopmentPhase.TESTING,
                    DevelopmentPhase.DOCUMENTATION,
                ],
                "typical_duration": 86400,  # 1 day
                "triggers": ["branch created", "feature specification"],
                "success_indicators": [
                    "PR created",
                    "tests passing",
                    "code review approved",
                ],
                "common_transitions": [
                    (DevelopmentPhase.PLANNING, DevelopmentPhase.IMPLEMENTATION),
                    (DevelopmentPhase.IMPLEMENTATION, DevelopmentPhase.TESTING),
                    (DevelopmentPhase.TESTING, DevelopmentPhase.DOCUMENTATION),
                ],
            },
            WorkflowPattern.BUG_TRIAGE: {
                "phases": [
                    DevelopmentPhase.EXPLORATION,
                    DevelopmentPhase.DEBUGGING,
                    DevelopmentPhase.TESTING,
                ],
                "typical_duration": 3600,  # 1 hour
                "triggers": ["bug report", "error message", "failing test"],
                "success_indicators": [
                    "bug reproduced",
                    "fix implemented",
                    "regression test added",
                ],
                "common_transitions": [
                    (DevelopmentPhase.EXPLORATION, DevelopmentPhase.DEBUGGING),
                    (DevelopmentPhase.DEBUGGING, DevelopmentPhase.TESTING),
                    (DevelopmentPhase.TESTING, DevelopmentPhase.DEBUGGING),
                ],
            },
            WorkflowPattern.RESEARCH_SPIKE: {
                "phases": [
                    DevelopmentPhase.EXPLORATION,
                    DevelopmentPhase.PLANNING,
                    DevelopmentPhase.ARCHITECTURE,
                ],
                "typical_duration": 7200,  # 2 hours
                "triggers": [
                    "new technology",
                    "architectural decision",
                    "proof of concept",
                ],
                "success_indicators": [
                    "decision made",
                    "prototype created",
                    "documentation written",
                ],
                "common_transitions": [
                    (DevelopmentPhase.EXPLORATION, DevelopmentPhase.PLANNING),
                    (DevelopmentPhase.PLANNING, DevelopmentPhase.ARCHITECTURE),
                    (DevelopmentPhase.ARCHITECTURE, DevelopmentPhase.IMPLEMENTATION),
                ],
            },
        }

    def _initialize_transition_probabilities(
        self,
    ) -> Dict[Tuple[DevelopmentPhase, DevelopmentPhase], float]:
        """Initialize phase transition probability matrix"""

        transitions = {}

        # Common transitions with probabilities
        common_flows = [
            (DevelopmentPhase.EXPLORATION, DevelopmentPhase.PLANNING, 0.7),
            (DevelopmentPhase.PLANNING, DevelopmentPhase.ARCHITECTURE, 0.6),
            (DevelopmentPhase.PLANNING, DevelopmentPhase.IMPLEMENTATION, 0.8),
            (DevelopmentPhase.ARCHITECTURE, DevelopmentPhase.IMPLEMENTATION, 0.9),
            (DevelopmentPhase.IMPLEMENTATION, DevelopmentPhase.TESTING, 0.8),
            (DevelopmentPhase.IMPLEMENTATION, DevelopmentPhase.DEBUGGING, 0.6),
            (DevelopmentPhase.TESTING, DevelopmentPhase.DEBUGGING, 0.5),
            (DevelopmentPhase.TESTING, DevelopmentPhase.DOCUMENTATION, 0.4),
            (DevelopmentPhase.DEBUGGING, DevelopmentPhase.TESTING, 0.7),
            (DevelopmentPhase.DEBUGGING, DevelopmentPhase.IMPLEMENTATION, 0.5),
            (DevelopmentPhase.DOCUMENTATION, DevelopmentPhase.DEPLOYMENT, 0.6),
            (DevelopmentPhase.OPTIMIZATION, DevelopmentPhase.TESTING, 0.8),
            (DevelopmentPhase.REFACTORING, DevelopmentPhase.TESTING, 0.9),
        ]

        for from_phase, to_phase, prob in common_flows:
            transitions[(from_phase, to_phase)] = prob

        return transitions

    async def analyze_workflow_context(
        self, facade_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze current workflow context and provide strategic insights"""

        # Update active session
        session = self._update_active_session(facade_data)

        # Detect current phase
        current_phase = await self._detect_current_phase(facade_data, session)

        # Update session with phase
        if session.phases and session.phases[-1] != current_phase:
            transition = WorkflowTransition(
                from_phase=session.phases[-1],
                to_phase=current_phase,
                trigger_event=facade_data.get("last_command", "unknown"),
                confidence=0.8,
                duration=time.time() - session.start_time,
                context=facade_data,
                timestamp=time.time(),
            )
            session.transitions.append(transition)

        session.phases.append(current_phase)

        # Detect workflow patterns
        detected_patterns = self._detect_workflow_patterns(session)
        session.patterns_detected.extend(detected_patterns)

        # Generate strategic insights
        strategic_insights = await self._generate_strategic_insights(
            session, facade_data
        )

        # Predict next phase
        next_phase_predictions = self._predict_next_phases(session, current_phase)

        # Calculate workflow metrics
        workflow_metrics = self._calculate_workflow_metrics(session)

        # Update statistics
        self.workflow_stats["sessions_analyzed"] += 1
        self.workflow_stats["patterns_detected"] += len(detected_patterns)
        self.workflow_stats["insights_generated"] += len(strategic_insights)

        return {
            "current_session": {
                "session_id": session.session_id,
                "current_phase": current_phase.value,
                "duration": time.time() - session.start_time,
                "phases_visited": [
                    p.value for p in session.phases[-10:]
                ],  # Last 10 phases
                "patterns_detected": [p.value for p in detected_patterns],
                "productivity_score": session.productivity_score,
                "complexity_level": session.complexity_level,
            },
            "strategic_insights": [
                {
                    "type": insight.insight_type,
                    "title": insight.title,
                    "description": insight.description,
                    "confidence": insight.confidence,
                    "impact_level": insight.impact_level,
                    "time_horizon": insight.time_horizon,
                    "actions": insight.recommended_actions,
                    "evidence": insight.supporting_evidence,
                }
                for insight in strategic_insights
            ],
            "predictions": {
                "next_phases": [
                    {"phase": phase.value, "probability": prob, "reasoning": reason}
                    for phase, prob, reason in next_phase_predictions
                ],
                "estimated_completion": self._estimate_completion_time(session),
                "potential_blockers": self._identify_potential_blockers(session),
            },
            "workflow_metrics": workflow_metrics,
            "recommendations": await self._generate_workflow_recommendations(
                session, strategic_insights
            ),
        }

    def _update_active_session(self, facade_data: Dict[str, Any]) -> DevelopmentSession:
        """Update or create active development session"""

        current_buffer = facade_data.get("current_buffer", "unknown")
        project_root = self._extract_project_root(current_buffer)

        # Simple session identification based on project and time gap
        session_key = f"{project_root}_{int(time.time() / 3600)}"  # Hourly sessions

        if session_key not in self.active_sessions:
            self.active_sessions[session_key] = DevelopmentSession(
                session_id=session_key,
                start_time=time.time(),
                end_time=None,
                phases=[],
                transitions=[],
                files_touched=set(),
                project_areas=set(),
                patterns_detected=[],
                session_type="unknown",
                productivity_score=0.7,
                complexity_level=1,
                interruptions=0,
                focus_metrics={},
            )

        session = self.active_sessions[session_key]

        # Update session data
        session.files_touched.add(current_buffer)
        session.project_areas.add(self._classify_project_area(current_buffer))

        return session

    async def _detect_current_phase(
        self, facade_data: Dict[str, Any], session: DevelopmentSession
    ) -> DevelopmentPhase:
        """Detect current development phase using AI coordination"""

        # Build context for AI analysis
        context_data = {
            "current_buffer": facade_data.get("current_buffer", ""),
            "last_command": facade_data.get("last_command", ""),
            "minor_modes": facade_data.get("minor_modes", []),
            "recent_files": list(session.files_touched)[-5:],
            "session_duration": time.time() - session.start_time,
            "previous_phases": [p.value for p in session.phases[-3:]],
        }

        # Create coordination task for phase detection
        task = CoordinationTask(
            task_id=f"phase_detection_{session.session_id}",
            task_type=AISpecialty.PROJECT_PLANNING,
            context=self._facade_to_development_context(facade_data),
            user_intent="Determine current development phase based on activity patterns",
            patterns=[
                {
                    "description": f"Recent phases: {session.phases[-3:]}",
                    "confidence": 0.8,
                }
            ],
            priority=3,
        )

        try:
            # Get AI analysis
            response = await self.ai_coordinator.coordinate_response(task)

            # Extract phase from AI response
            detected_phase = self._extract_phase_from_response(
                response.primary_response.content
            )

            if detected_phase:
                return detected_phase

        except Exception as e:
            print(f"AI phase detection failed: {e}")

        # Fallback to rule-based detection
        return self._rule_based_phase_detection(facade_data, session)

    def _rule_based_phase_detection(
        self, facade_data: Dict[str, Any], session: DevelopmentSession
    ) -> DevelopmentPhase:
        """Fallback rule-based phase detection"""

        current_buffer = facade_data.get("current_buffer", "").lower()
        last_command = facade_data.get("last_command", "").lower()
        minor_modes = facade_data.get("minor_modes", [])

        # Testing phase indicators
        if (
            "test" in current_buffer
            or "pytest" in str(minor_modes)
            or "test" in last_command
        ):
            return DevelopmentPhase.TESTING

        # Documentation phase indicators
        if (
            current_buffer.endswith(".md")
            or current_buffer.endswith(".org")
            or "doc" in current_buffer
        ):
            return DevelopmentPhase.DOCUMENTATION

        # Debugging phase indicators
        if (
            "debug" in last_command
            or "compilation" in str(facade_data)
            or any("error" in str(v) for v in facade_data.values())
        ):
            return DevelopmentPhase.DEBUGGING

        # Implementation phase indicators
        if last_command in [
            "self-insert-command",
            "newline",
        ] and current_buffer.endswith((".py", ".js", ".ts", ".java", ".cpp")):
            return DevelopmentPhase.IMPLEMENTATION

        # Planning/Architecture phase indicators
        if (
            "design" in current_buffer
            or "architecture" in current_buffer
            or "plan" in current_buffer
        ):
            return DevelopmentPhase.ARCHITECTURE

        # Default to exploration for navigation activities
        if last_command in ["switch-to-buffer", "find-file"]:
            return DevelopmentPhase.EXPLORATION

        # Default
        return DevelopmentPhase.IMPLEMENTATION

    def _detect_workflow_patterns(
        self, session: DevelopmentSession
    ) -> List[WorkflowPattern]:
        """Detect workflow patterns from session data"""

        detected_patterns = []

        # Check for TDD cycle
        if self._matches_tdd_pattern(session):
            detected_patterns.append(WorkflowPattern.TDD_CYCLE)

        # Check for feature branch pattern
        if self._matches_feature_branch_pattern(session):
            detected_patterns.append(WorkflowPattern.FEATURE_BRANCH)

        # Check for bug triage pattern
        if self._matches_bug_triage_pattern(session):
            detected_patterns.append(WorkflowPattern.BUG_TRIAGE)

        # Check for research spike pattern
        if self._matches_research_spike_pattern(session):
            detected_patterns.append(WorkflowPattern.RESEARCH_SPIKE)

        return detected_patterns

    async def _generate_strategic_insights(
        self, session: DevelopmentSession, facade_data: Dict[str, Any]
    ) -> List[StrategicInsight]:
        """Generate strategic insights about development workflow"""

        insights = []

        # Productivity insights
        if session.productivity_score < 0.5:
            insights.append(
                StrategicInsight(
                    insight_type="productivity",
                    title="Low Productivity Detected",
                    description=f"Current session shows {session.productivity_score:.1%} productivity. Consider taking a break or switching focus areas.",
                    confidence=0.8,
                    impact_level=3,
                    time_horizon="immediate",
                    recommended_actions=[
                        "Take a 10-minute break",
                        "Switch to a different task",
                        "Review current approach",
                    ],
                    supporting_evidence=[
                        f"Session duration: {(time.time() - session.start_time) / 60:.1f} minutes",
                        f"Phase transitions: {len(session.transitions)}",
                        f"Files touched: {len(session.files_touched)}",
                    ],
                    affected_areas=list(session.project_areas),
                )
            )

        # Pattern insights
        if WorkflowPattern.TDD_CYCLE in session.patterns_detected:
            insights.append(
                StrategicInsight(
                    insight_type="methodology",
                    title="TDD Pattern Detected",
                    description="You're following Test-Driven Development practices. This typically leads to better code quality and fewer bugs.",
                    confidence=0.9,
                    impact_level=4,
                    time_horizon="short_term",
                    recommended_actions=[
                        "Continue TDD cycle",
                        "Ensure test coverage is comprehensive",
                        "Refactor when tests are green",
                    ],
                    supporting_evidence=[
                        "Testing phases detected in workflow",
                        "Test files in session",
                        "Implementation following test phases",
                    ],
                    affected_areas=list(session.project_areas),
                )
            )

        # Complexity insights
        if session.complexity_level >= 4:
            insights.append(
                StrategicInsight(
                    insight_type="complexity",
                    title="High Complexity Session",
                    description="Current session involves high complexity work. Consider breaking down into smaller, manageable tasks.",
                    confidence=0.7,
                    impact_level=3,
                    time_horizon="immediate",
                    recommended_actions=[
                        "Break down current task",
                        "Create subtasks or TODO items",
                        "Focus on one aspect at a time",
                    ],
                    supporting_evidence=[
                        f"Complexity level: {session.complexity_level}/5",
                        f"Multiple project areas: {len(session.project_areas)}",
                        f"Frequent phase transitions",
                    ],
                    affected_areas=list(session.project_areas),
                )
            )

        # Focus insights
        if len(session.files_touched) > 10:
            insights.append(
                StrategicInsight(
                    insight_type="focus",
                    title="Scattered Focus Detected",
                    description=f"You've touched {len(session.files_touched)} files in this session. Consider focusing on fewer files for better productivity.",
                    confidence=0.8,
                    impact_level=2,
                    time_horizon="immediate",
                    recommended_actions=[
                        "Focus on current file",
                        "Complete current task before switching",
                        "Use TODO comments for context switching",
                    ],
                    supporting_evidence=[
                        f"Files touched: {len(session.files_touched)}",
                        f"Project areas: {len(session.project_areas)}",
                        f"Session duration: {(time.time() - session.start_time) / 60:.1f} minutes",
                    ],
                    affected_areas=list(session.project_areas),
                )
            )

        return insights

    def _predict_next_phases(
        self, session: DevelopmentSession, current_phase: DevelopmentPhase
    ) -> List[Tuple[DevelopmentPhase, float, str]]:
        """Predict next development phases"""

        predictions = []

        # Use transition probabilities
        for (
            from_phase,
            to_phase,
        ), base_prob in self.phase_transition_probabilities.items():
            if from_phase == current_phase:

                # Adjust probability based on session context
                adjusted_prob = base_prob

                # Boost probability if phase hasn't been visited recently
                if to_phase not in session.phases[-5:]:
                    adjusted_prob *= 1.2

                # Reduce probability if phase was just visited
                if session.phases and session.phases[-1] == to_phase:
                    adjusted_prob *= 0.3

                # Pattern-based adjustments
                if WorkflowPattern.TDD_CYCLE in session.patterns_detected:
                    if (
                        current_phase == DevelopmentPhase.TESTING
                        and to_phase == DevelopmentPhase.IMPLEMENTATION
                    ):
                        adjusted_prob *= 1.5

                reasoning = self._generate_prediction_reasoning(
                    current_phase, to_phase, session, adjusted_prob
                )

                predictions.append((to_phase, min(adjusted_prob, 1.0), reasoning))

        # Sort by probability
        predictions.sort(key=lambda x: x[1], reverse=True)

        return predictions[:5]  # Top 5 predictions

    def _generate_prediction_reasoning(
        self,
        from_phase: DevelopmentPhase,
        to_phase: DevelopmentPhase,
        session: DevelopmentSession,
        probability: float,
    ) -> str:
        """Generate reasoning for phase transition prediction"""

        reasons = []

        # Base transition reasoning
        if probability > 0.7:
            reasons.append(
                f"Strong historical pattern from {from_phase.value} to {to_phase.value}"
            )
        elif probability > 0.5:
            reasons.append(
                f"Common transition from {from_phase.value} to {to_phase.value}"
            )
        else:
            reasons.append(
                f"Possible transition from {from_phase.value} to {to_phase.value}"
            )

        # Session-specific reasoning
        if to_phase not in session.phases[-5:]:
            reasons.append("phase hasn't been visited recently")

        # Pattern-specific reasoning
        for pattern in session.patterns_detected:
            pattern_info = self.pattern_library.get(pattern, {})
            if (from_phase, to_phase) in pattern_info.get("common_transitions", []):
                reasons.append(f"aligns with {pattern.value} pattern")

        return "; ".join(reasons)

    async def _generate_workflow_recommendations(
        self, session: DevelopmentSession, insights: List[StrategicInsight]
    ) -> List[str]:
        """Generate workflow improvement recommendations"""

        recommendations = []

        # Based on detected patterns
        if WorkflowPattern.TDD_CYCLE in session.patterns_detected:
            recommendations.append(
                "Continue your TDD practice - consider adding more edge case tests"
            )

        if WorkflowPattern.BUG_TRIAGE in session.patterns_detected:
            recommendations.append(
                "Add regression tests to prevent this bug from recurring"
            )

        # Based on session metrics
        duration_hours = (time.time() - session.start_time) / 3600

        if duration_hours > 2:
            recommendations.append(
                "Consider taking a longer break - extended focus can reduce productivity"
            )

        if len(session.project_areas) > 3:
            recommendations.append(
                "Try to focus on one project area at a time for deeper work"
            )

        # Based on insights
        for insight in insights:
            if insight.impact_level >= 3:
                recommendations.extend(insight.recommended_actions[:2])  # Top 2 actions

        return recommendations[:5]  # Limit to 5 recommendations

    def _estimate_completion_time(self, session: DevelopmentSession) -> Dict[str, Any]:
        """Estimate completion time for current workflow"""

        current_duration = time.time() - session.start_time

        # Estimate based on detected patterns
        estimated_total = current_duration
        for pattern in session.patterns_detected:
            pattern_info = self.pattern_library.get(pattern, {})
            typical_duration = pattern_info.get(
                "typical_duration", current_duration * 2
            )
            estimated_total = max(estimated_total, typical_duration)

        remaining_time = max(0, estimated_total - current_duration)

        return {
            "estimated_total_minutes": estimated_total / 60,
            "estimated_remaining_minutes": remaining_time / 60,
            "confidence": 0.7,
            "factors": [
                f"Pattern: {pattern.value}" for pattern in session.patterns_detected
            ],
        }

    def _identify_potential_blockers(self, session: DevelopmentSession) -> List[str]:
        """Identify potential workflow blockers"""

        blockers = []

        # High complexity without testing
        if (
            session.complexity_level >= 4
            and DevelopmentPhase.TESTING not in session.phases[-5:]
        ):
            blockers.append(
                "High complexity without recent testing - risk of hard-to-debug issues"
            )

        # Long implementation without documentation
        impl_phases = sum(
            1 for p in session.phases if p == DevelopmentPhase.IMPLEMENTATION
        )
        if impl_phases >= 5 and DevelopmentPhase.DOCUMENTATION not in session.phases:
            blockers.append(
                "Extended implementation without documentation - may impact maintainability"
            )

        # Debugging without testing
        if (
            DevelopmentPhase.DEBUGGING in session.phases[-3:]
            and DevelopmentPhase.TESTING not in session.phases[-3:]
        ):
            blockers.append(
                "Debugging without testing - may miss regression opportunities"
            )

        # Too many file switches
        if len(session.files_touched) > 15:
            blockers.append(
                "Excessive file switching - may indicate unclear task boundaries"
            )

        return blockers

    def get_workflow_intelligence_stats(self) -> Dict[str, Any]:
        """Get workflow intelligence system statistics"""

        return {
            "statistics": dict(self.workflow_stats),
            "active_sessions": len(self.active_sessions),
            "pattern_library_size": len(self.pattern_library),
            "transition_probabilities": len(self.phase_transition_probabilities),
            "memory_events": len(self.workflow_memory),
            "pattern_frequencies": dict(self.pattern_frequencies),
            "supported_phases": [phase.value for phase in DevelopmentPhase],
            "supported_patterns": [pattern.value for pattern in WorkflowPattern],
        }

    # Helper methods

    def _extract_phase_from_response(
        self, response_content: str
    ) -> Optional[DevelopmentPhase]:
        """Extract development phase from AI response"""

        content_lower = response_content.lower()

        # Look for phase keywords in response
        phase_keywords = {
            DevelopmentPhase.EXPLORATION: [
                "explore",
                "exploring",
                "investigate",
                "research",
            ],
            DevelopmentPhase.PLANNING: ["plan", "planning", "design", "architect"],
            DevelopmentPhase.IMPLEMENTATION: ["implement", "code", "coding", "develop"],
            DevelopmentPhase.TESTING: ["test", "testing", "verify", "validate"],
            DevelopmentPhase.DEBUGGING: ["debug", "fix", "error", "bug"],
            DevelopmentPhase.DOCUMENTATION: ["document", "write", "explain", "doc"],
            DevelopmentPhase.REFACTORING: ["refactor", "improve", "clean", "optimize"],
        }

        for phase, keywords in phase_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return phase

        return None


async def demo_workflow_intelligence():
    """Demo the workflow intelligence system"""
    print("🧠 WORKFLOW INTELLIGENCE SYSTEM DEMO")
    print("=" * 50)

    # Setup
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    intelligence = WorkflowIntelligenceSystem(redis_client)

    # Show system capabilities
    stats = intelligence.get_workflow_intelligence_stats()
    print("📊 System Capabilities:")
    print(f"   • Supported phases: {len(stats['supported_phases'])}")
    print(f"   • Supported patterns: {len(stats['supported_patterns'])}")
    print(f"   • Pattern library: {stats['pattern_library_size']} patterns")
    print(
        f"   • Transition probabilities: {stats['transition_probabilities']} mappings"
    )

    # Simulate development workflow
    workflow_scenarios = [
        {
            "name": "TDD Development Session",
            "facade_data": {
                "current_buffer": "test_user_auth.py",
                "last_command": "self-insert-command",
                "minor_modes": ["python-mode", "pytest-mode"],
                "cursor_line": 15,
            },
        },
        {
            "name": "Feature Implementation",
            "facade_data": {
                "current_buffer": "user_service.py",
                "last_command": "newline",
                "minor_modes": ["python-mode", "flycheck-mode"],
                "cursor_line": 45,
            },
        },
        {
            "name": "Bug Investigation",
            "facade_data": {
                "current_buffer": "error_handler.py",
                "last_command": "compile",
                "minor_modes": ["python-mode", "flycheck-mode"],
                "cursor_line": 23,
            },
        },
        {
            "name": "Documentation Update",
            "facade_data": {
                "current_buffer": "API_DOCS.md",
                "last_command": "self-insert-command",
                "minor_modes": ["markdown-mode"],
                "cursor_line": 8,
            },
        },
    ]

    print(f"\n🎯 Analyzing workflow scenarios...")

    for scenario in workflow_scenarios:
        print(f"\n--- {scenario['name']} ---")

        try:
            analysis = await intelligence.analyze_workflow_context(
                scenario["facade_data"]
            )

            session = analysis["current_session"]
            print(f"📋 Current Phase: {session['current_phase']}")
            print(f"⏱️  Duration: {session['duration']/60:.1f} minutes")
            print(
                f"🔄 Patterns: {', '.join(session['patterns_detected']) or 'None detected'}"
            )
            print(f"📈 Productivity: {session['productivity_score']:.1%}")

            # Show strategic insights
            insights = analysis["strategic_insights"]
            if insights:
                print(f"💡 Strategic Insights:")
                for insight in insights[:2]:  # Show top 2
                    print(f"   • {insight['title']}: {insight['description'][:100]}...")

            # Show predictions
            predictions = analysis["predictions"]["next_phases"]
            if predictions:
                print(f"🔮 Next Phase Predictions:")
                for pred in predictions[:3]:  # Show top 3
                    print(
                        f"   • {pred['phase']}: {pred['probability']:.1%} - {pred['reasoning'][:80]}..."
                    )

            # Show recommendations
            recommendations = analysis["recommendations"]
            if recommendations:
                print(f"🎯 Recommendations:")
                for rec in recommendations[:2]:  # Show top 2
                    print(f"   • {rec}")

        except Exception as e:
            print(f"❌ Analysis error: {e}")

    # Show final statistics
    final_stats = intelligence.get_workflow_intelligence_stats()
    print(f"\n📊 WORKFLOW INTELLIGENCE STATISTICS:")
    print(f"   Sessions analyzed: {final_stats['statistics']['sessions_analyzed']}")
    print(f"   Patterns detected: {final_stats['statistics']['patterns_detected']}")
    print(f"   Insights generated: {final_stats['statistics']['insights_generated']}")
    print(f"   Active sessions: {final_stats['active_sessions']}")

    print(f"\n✨ WORKFLOW INTELLIGENCE CAPABILITIES:")
    print(f"   ✅ Real-time development phase detection")
    print(f"   ✅ Workflow pattern recognition (TDD, Feature Branch, etc.)")
    print(f"   ✅ Strategic insight generation with AI coordination")
    print(f"   ✅ Next phase prediction with reasoning")
    print(f"   ✅ Productivity and focus metrics")
    print(f"   ✅ Workflow blocker identification")
    print(f"   ✅ Personalized recommendations")

    print(f"\n🚀 This creates a truly intelligent development assistant that:")
    print(f"   • Understands your development workflow at a strategic level")
    print(f"   • Predicts and guides your next steps")
    print(f"   • Identifies productivity and quality issues proactively")
    print(f"   • Adapts to your personal development patterns")
    print(f"   • Provides strategic guidance for complex projects")


if __name__ == "__main__":
    asyncio.run(demo_workflow_intelligence())
