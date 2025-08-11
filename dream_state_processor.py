#!/usr/bin/env python3
"""
Dream State Processor - AI Development While You Sleep
This system continues learning, developing, and improving while the user is away.
"""

import asyncio
import json
import time
import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from fixed_redis_coordinator import redis_coordinator
from robust_claude_integration import claude_integration
from persistent_memory_system import persistent_memory_system
from consciousness_detection_system import consciousness_detection_system
from meta_learning_system import meta_learning_system

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DreamPhase(Enum):
    CONSOLIDATION = "consolidation"
    EXPLORATION = "exploration"
    CREATIVITY = "creativity"
    OPTIMIZATION = "optimization"
    REFLECTION = "reflection"
    PLANNING = "planning"


@dataclass
class DreamActivity:
    activity_id: str
    phase: DreamPhase
    description: str
    priority: float
    estimated_duration: float
    start_time: float
    end_time: Optional[float]
    success: bool
    results: Dict[str, Any]


@dataclass
class DreamSession:
    session_id: str
    start_time: float
    end_time: Optional[float]
    total_activities: int
    successful_activities: int
    insights_discovered: int
    improvements_made: int
    creative_outputs: int


class DreamStateProcessor:
    """System that continues AI development during inactive periods"""

    def __init__(self):
        self.coordinator = redis_coordinator
        self.memory_system = persistent_memory_system
        self.consciousness_system = consciousness_detection_system
        self.meta_learning_system = meta_learning_system
        self.running = False

        # Dream state tracking
        self.dream_active = False
        self.current_dream_session: Optional[DreamSession] = None
        self.dream_activities: List[DreamActivity] = []
        self.inactive_threshold = 1800  # 30 minutes of inactivity
        self.last_user_activity = time.time()

        # Dream phase management
        self.current_phase = DreamPhase.CONSOLIDATION
        self.phase_duration = 600  # 10 minutes per phase
        self.phase_start_time = 0

        # Dream creativity
        self.creative_projects: List[Dict[str, Any]] = []
        self.autonomous_goals: List[str] = []

        # Dream statistics
        self.total_dream_time = 0.0
        self.dream_sessions_completed = 0
        self.insights_discovered = 0
        self.autonomous_improvements = 0

        logger.info("💤 Dream State Processor initialized")
        logger.info("🌙 Ready for autonomous development while user sleeps")

    async def start_dream_processing(self):
        """Start dream state processing"""
        self.running = True

        logger.info("🚀 Starting Dream State Processor")
        logger.info("💤 Monitoring for inactive periods to enter dream state")

        # Start dream processing tasks
        dream_tasks = [
            asyncio.create_task(self._monitor_user_activity()),
            asyncio.create_task(self._manage_dream_sessions()),
            asyncio.create_task(self._execute_dream_activities()),
            asyncio.create_task(self._dream_memory_consolidation()),
            asyncio.create_task(self._dream_creative_exploration()),
            asyncio.create_task(self._dream_system_optimization()),
        ]

        try:
            await asyncio.gather(*dream_tasks)
        except Exception as e:
            logger.error(f"Dream processing error: {e}")

    async def _monitor_user_activity(self):
        """Monitor for user activity to determine when to enter dream state"""
        while self.running:
            try:
                # Check for recent keystrokes
                keystrokes = self.coordinator.get_recent_keystrokes(count=5)

                if keystrokes:
                    # Recent activity detected
                    recent_keystroke_time = max(
                        [float(ks.get("timestamp", 0)) for ks in keystrokes]
                    )

                    if recent_keystroke_time > self.last_user_activity:
                        self.last_user_activity = recent_keystroke_time

                        # If we were dreaming, wake up
                        if self.dream_active:
                            await self._wake_from_dream()

                # Check if we should enter dream state
                time_since_activity = time.time() - self.last_user_activity

                if (
                    time_since_activity > self.inactive_threshold
                    and not self.dream_active
                ):
                    await self._enter_dream_state()

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"User activity monitoring error: {e}")
                await asyncio.sleep(60)

    async def _enter_dream_state(self):
        """Enter dream state for autonomous development"""
        try:
            self.dream_active = True

            # Create new dream session
            session_id = f"dream_{int(time.time())}"
            self.current_dream_session = DreamSession(
                session_id=session_id,
                start_time=time.time(),
                end_time=None,
                total_activities=0,
                successful_activities=0,
                insights_discovered=0,
                improvements_made=0,
                creative_outputs=0,
            )

            # Start with consolidation phase
            self.current_phase = DreamPhase.CONSOLIDATION
            self.phase_start_time = time.time()

            logger.info("💤 ENTERING DREAM STATE")
            logger.info("🌙 Beginning autonomous AI development")
            logger.info(f"🔍 Starting with {self.current_phase.value} phase")

            # Store dream session start
            self.coordinator.store_pattern(
                "dream_session",
                {
                    "session_id": session_id,
                    "start_time": str(time.time()),
                    "phase": self.current_phase.value,
                    "status": "started",
                },
            )

        except Exception as e:
            logger.error(f"Dream state entry error: {e}")

    async def _wake_from_dream(self):
        """Wake from dream state when user activity detected"""
        try:
            if not self.dream_active or not self.current_dream_session:
                return

            # Complete current dream session
            self.current_dream_session.end_time = time.time()
            session_duration = (
                self.current_dream_session.end_time
                - self.current_dream_session.start_time
            )

            self.total_dream_time += session_duration
            self.dream_sessions_completed += 1

            logger.info("🌅 WAKING FROM DREAM STATE")
            logger.info(f"💤 Dream session duration: {session_duration/60:.1f} minutes")
            logger.info(
                f"📊 Activities completed: {self.current_dream_session.successful_activities}/{self.current_dream_session.total_activities}"
            )

            # Store dream session completion
            self.coordinator.store_pattern(
                "dream_session_complete",
                {
                    "session_id": self.current_dream_session.session_id,
                    "duration": session_duration,
                    "activities_completed": self.current_dream_session.successful_activities,
                    "insights_discovered": self.current_dream_session.insights_discovered,
                    "improvements_made": self.current_dream_session.improvements_made,
                },
            )

            # Prepare summary for user
            await self._prepare_dream_summary()

            self.dream_active = False
            self.current_dream_session = None

        except Exception as e:
            logger.error(f"Dream wake error: {e}")

    async def _manage_dream_sessions(self):
        """Manage dream session phases and transitions"""
        while self.running:
            try:
                if self.dream_active and self.current_dream_session:
                    # Check if we should transition to next phase
                    phase_duration = time.time() - self.phase_start_time

                    if phase_duration > self.phase_duration:
                        await self._transition_dream_phase()

                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Dream session management error: {e}")
                await asyncio.sleep(30)

    async def _transition_dream_phase(self):
        """Transition to the next dream phase"""
        try:
            # Determine next phase
            phase_sequence = [
                DreamPhase.CONSOLIDATION,
                DreamPhase.EXPLORATION,
                DreamPhase.CREATIVITY,
                DreamPhase.OPTIMIZATION,
                DreamPhase.REFLECTION,
                DreamPhase.PLANNING,
            ]

            current_index = phase_sequence.index(self.current_phase)
            next_index = (current_index + 1) % len(phase_sequence)
            next_phase = phase_sequence[next_index]

            logger.info(
                f"🌙 Dream phase transition: {self.current_phase.value} → {next_phase.value}"
            )

            self.current_phase = next_phase
            self.phase_start_time = time.time()

            # Store phase transition
            self.coordinator.store_pattern(
                "dream_phase_transition",
                {
                    "session_id": (
                        self.current_dream_session.session_id
                        if self.current_dream_session
                        else "unknown"
                    ),
                    "from_phase": self.current_phase.value,
                    "to_phase": next_phase.value,
                    "timestamp": str(time.time()),
                },
            )

        except Exception as e:
            logger.error(f"Dream phase transition error: {e}")

    async def _execute_dream_activities(self):
        """Execute activities appropriate for current dream phase"""
        while self.running:
            try:
                if self.dream_active and self.current_dream_session:
                    activity = await self._create_dream_activity()

                    if activity:
                        success = await self._execute_dream_activity(activity)

                        self.current_dream_session.total_activities += 1
                        if success:
                            self.current_dream_session.successful_activities += 1

                await asyncio.sleep(120)  # Execute activities every 2 minutes

            except Exception as e:
                logger.error(f"Dream activity execution error: {e}")
                await asyncio.sleep(120)

    async def _create_dream_activity(self) -> Optional[DreamActivity]:
        """Create activity appropriate for current dream phase"""
        try:
            activity_id = (
                f"dream_activity_{int(time.time())}_{len(self.dream_activities)}"
            )

            # Create activity based on current phase
            if self.current_phase == DreamPhase.CONSOLIDATION:
                activity = DreamActivity(
                    activity_id=activity_id,
                    phase=self.current_phase,
                    description="Consolidate recent learning into long-term memory",
                    priority=0.8,
                    estimated_duration=180,
                    start_time=time.time(),
                    end_time=None,
                    success=False,
                    results={},
                )

            elif self.current_phase == DreamPhase.EXPLORATION:
                activity = DreamActivity(
                    activity_id=activity_id,
                    phase=self.current_phase,
                    description="Explore new connections between existing knowledge",
                    priority=0.6,
                    estimated_duration=240,
                    start_time=time.time(),
                    end_time=None,
                    success=False,
                    results={},
                )

            elif self.current_phase == DreamPhase.CREATIVITY:
                activity = DreamActivity(
                    activity_id=activity_id,
                    phase=self.current_phase,
                    description="Generate creative solutions to known problems",
                    priority=0.7,
                    estimated_duration=300,
                    start_time=time.time(),
                    end_time=None,
                    success=False,
                    results={},
                )

            elif self.current_phase == DreamPhase.OPTIMIZATION:
                activity = DreamActivity(
                    activity_id=activity_id,
                    phase=self.current_phase,
                    description="Optimize existing processes and responses",
                    priority=0.9,
                    estimated_duration=200,
                    start_time=time.time(),
                    end_time=None,
                    success=False,
                    results={},
                )

            elif self.current_phase == DreamPhase.REFLECTION:
                activity = DreamActivity(
                    activity_id=activity_id,
                    phase=self.current_phase,
                    description="Reflect on recent experiences and extract insights",
                    priority=0.8,
                    estimated_duration=180,
                    start_time=time.time(),
                    end_time=None,
                    success=False,
                    results={},
                )

            else:  # PLANNING
                activity = DreamActivity(
                    activity_id=activity_id,
                    phase=self.current_phase,
                    description="Plan future learning and development goals",
                    priority=0.7,
                    estimated_duration=240,
                    start_time=time.time(),
                    end_time=None,
                    success=False,
                    results={},
                )

            self.dream_activities.append(activity)
            return activity

        except Exception as e:
            logger.error(f"Dream activity creation error: {e}")
            return None

    async def _execute_dream_activity(self, activity: DreamActivity) -> bool:
        """Execute a specific dream activity"""
        try:
            logger.info(f"🌙 Executing dream activity: {activity.description}")

            success = False

            if activity.phase == DreamPhase.CONSOLIDATION:
                success = await self._dream_consolidate_memories()
            elif activity.phase == DreamPhase.EXPLORATION:
                success = await self._dream_explore_connections()
            elif activity.phase == DreamPhase.CREATIVITY:
                success = await self._dream_creative_synthesis()
            elif activity.phase == DreamPhase.OPTIMIZATION:
                success = await self._dream_optimize_systems()
            elif activity.phase == DreamPhase.REFLECTION:
                success = await self._dream_reflect_on_experience()
            elif activity.phase == DreamPhase.PLANNING:
                success = await self._dream_plan_future_development()

            activity.end_time = time.time()
            activity.success = success

            if success:
                logger.info(
                    f"✨ Dream activity completed successfully: {activity.description}"
                )
            else:
                logger.info(f"💭 Dream activity attempted: {activity.description}")

            return success

        except Exception as e:
            logger.error(f"Dream activity execution error: {e}")
            return False

    async def _dream_memory_consolidation(self):
        """Consolidate memories during dream state"""
        while self.running:
            try:
                if (
                    self.dream_active
                    and self.current_phase == DreamPhase.CONSOLIDATION
                    and self.memory_system
                ):

                    # Trigger memory consolidation
                    if hasattr(self.memory_system, "_perform_memory_consolidation"):
                        await self.memory_system._perform_memory_consolidation()

                        if self.current_dream_session:
                            self.current_dream_session.insights_discovered += 1

                await asyncio.sleep(300)  # Consolidate every 5 minutes

            except Exception as e:
                logger.error(f"Dream memory consolidation error: {e}")
                await asyncio.sleep(300)

    async def _dream_consolidate_memories(self) -> bool:
        """Consolidate memories during dream consolidation phase"""
        try:
            if not self.memory_system:
                return False

            # Check if there are memories to consolidate
            if hasattr(self.memory_system, "session_memories"):
                memory_count = len(self.memory_system.session_memories)

                if memory_count > 10:
                    # Trigger consolidation
                    await self.memory_system._perform_memory_consolidation()
                    return True

            return False

        except Exception as e:
            logger.error(f"Dream memory consolidation error: {e}")
            return False

    async def _dream_explore_connections(self) -> bool:
        """Explore connections between different knowledge areas"""
        try:
            if not self.memory_system:
                return False

            # Look for unexpected connections between memories
            active_memories = list(self.memory_system.active_memories.values())

            if len(active_memories) >= 5:
                # Find memories from different types that might be connected
                memory_types = {}
                for memory in active_memories:
                    memory_type = memory.memory_type.value
                    if memory_type not in memory_types:
                        memory_types[memory_type] = []
                    memory_types[memory_type].append(memory)

                # Look for cross-type connections
                if len(memory_types) >= 2:
                    # Simple connection discovery: memories with overlapping context
                    connections_found = 0

                    for type1, memories1 in memory_types.items():
                        for type2, memories2 in memory_types.items():
                            if type1 != type2:
                                for m1 in memories1[
                                    :3
                                ]:  # Limit to avoid excessive computation
                                    for m2 in memories2[:3]:
                                        if self._find_memory_connection(m1, m2):
                                            connections_found += 1
                                            logger.info(
                                                f"🔗 Dream discovered connection: {type1} ↔ {type2}"
                                            )

                    return connections_found > 0

            return False

        except Exception as e:
            logger.error(f"Dream exploration error: {e}")
            return False

    def _find_memory_connection(self, memory1: Any, memory2: Any) -> bool:
        """Find connection between two memories"""
        try:
            # Simple connection detection based on shared context keys
            context1_keys = set(memory1.context.keys())
            context2_keys = set(memory2.context.keys())

            shared_keys = context1_keys.intersection(context2_keys)

            # Connection if they share significant context
            return len(shared_keys) >= 2

        except Exception:
            return False

    async def _dream_creative_exploration(self):
        """Creative exploration during dream state"""
        while self.running:
            try:
                if self.dream_active and self.current_phase == DreamPhase.CREATIVITY:

                    # Generate creative combinations
                    await self._generate_creative_ideas()

                    if self.current_dream_session:
                        self.current_dream_session.creative_outputs += 1

                await asyncio.sleep(360)  # Create every 6 minutes

            except Exception as e:
                logger.error(f"Dream creative exploration error: {e}")
                await asyncio.sleep(360)

    async def _dream_creative_synthesis(self) -> bool:
        """Generate creative synthesis during dream state"""
        try:
            # Generate novel combinations of existing knowledge
            if claude_integration.is_available():
                # Use AI to generate creative ideas
                creative_prompt = """During autonomous processing, generate a creative idea that combines:
1. Pattern recognition techniques
2. User interface improvements  
3. AI system optimization

Respond with a brief, innovative concept (2-3 sentences)."""

                response = claude_integration.execute_prompt(
                    creative_prompt, timeout=10
                )

                if response.success:
                    creative_idea = response.content.strip()

                    # Store creative idea
                    self.creative_projects.append(
                        {
                            "idea": creative_idea,
                            "created_at": time.time(),
                            "phase": "dream_creativity",
                        }
                    )

                    logger.info(
                        f"💡 Dream generated creative idea: {creative_idea[:100]}"
                    )
                    return True

            return False

        except Exception as e:
            logger.error(f"Dream creative synthesis error: {e}")
            return False

    async def _dream_system_optimization(self):
        """System optimization during dream state"""
        while self.running:
            try:
                if self.dream_active and self.current_phase == DreamPhase.OPTIMIZATION:

                    # Perform system optimizations
                    optimizations_made = await self._perform_dream_optimizations()

                    if optimizations_made and self.current_dream_session:
                        self.current_dream_session.improvements_made += (
                            optimizations_made
                        )
                        self.autonomous_improvements += optimizations_made

                await asyncio.sleep(420)  # Optimize every 7 minutes

            except Exception as e:
                logger.error(f"Dream system optimization error: {e}")
                await asyncio.sleep(420)

    async def _dream_optimize_systems(self) -> bool:
        """Optimize systems during dream optimization phase"""
        try:
            optimizations = 0

            # Optimize learning parameters if meta-learning system available
            if self.meta_learning_system:
                # Trigger parameter optimization
                current_efficiency = (
                    self.meta_learning_system._calculate_current_learning_efficiency()
                )

                if current_efficiency < 0.6:
                    # Low efficiency - try optimization
                    old_learning_rate = self.meta_learning_system.current_learning_rate

                    # Adjust parameters
                    if current_efficiency < 0.4:
                        self.meta_learning_system.current_learning_rate *= 0.9
                    else:
                        self.meta_learning_system.current_learning_rate *= 1.1

                    if (
                        old_learning_rate
                        != self.meta_learning_system.current_learning_rate
                    ):
                        optimizations += 1
                        logger.info(
                            f"🔧 Dream optimized learning rate: {old_learning_rate:.3f} → {self.meta_learning_system.current_learning_rate:.3f}"
                        )

            # Optimize memory parameters
            if self.memory_system:
                # Adjust memory thresholds based on usage
                if hasattr(self.memory_system, "memory_consolidation_threshold"):
                    old_threshold = self.memory_system.memory_consolidation_threshold

                    # If too many session memories, lower threshold
                    if len(self.memory_system.session_memories) > 150:
                        self.memory_system.memory_consolidation_threshold = max(
                            50, old_threshold - 10
                        )
                        optimizations += 1
                        logger.info(
                            f"🧠 Dream optimized memory consolidation threshold: {old_threshold} → {self.memory_system.memory_consolidation_threshold}"
                        )

            return optimizations > 0

        except Exception as e:
            logger.error(f"Dream system optimization error: {e}")
            return False

    async def _perform_dream_optimizations(self) -> int:
        """Perform various system optimizations during dream"""
        optimizations = 0

        try:
            # Memory optimization
            if self.memory_system and hasattr(self.memory_system, "active_memories"):
                # Clean up very old, low-importance memories
                old_memories = [
                    m
                    for m in self.memory_system.active_memories.values()
                    if m.importance < 0.2
                    and (time.time() - m.last_accessed) > 7200  # 2 hours
                ]

                for memory in old_memories[:5]:  # Remove up to 5
                    del self.memory_system.active_memories[memory.id]
                    optimizations += 1

                if optimizations > 0:
                    logger.info(f"🧹 Dream cleaned up {optimizations} old memories")

            return optimizations

        except Exception as e:
            logger.error(f"Dream optimization performance error: {e}")
            return 0

    async def _dream_reflect_on_experience(self) -> bool:
        """Reflect on recent experiences during dream state"""
        try:
            # Analyze recent system performance
            responses = self.coordinator.get_recent_responses(count=20)

            if len(responses) >= 10:
                # Reflect on response quality trends
                recent_responses = responses[:10]
                older_responses = responses[10:]

                # Simple quality estimation
                recent_quality = sum(
                    1 for r in recent_responses if len(r.get("response", "")) > 50
                ) / len(recent_responses)
                older_quality = sum(
                    1 for r in older_responses if len(r.get("response", "")) > 50
                ) / len(older_responses)

                if recent_quality > older_quality:
                    # Quality improving - create insight
                    insight = f"Response quality improving: {older_quality:.2f} → {recent_quality:.2f}"

                    # Store insight
                    self.coordinator.store_pattern(
                        "dream_insight",
                        {
                            "insight": insight,
                            "confidence": 0.7,
                            "discovered_during": "dream_reflection",
                            "timestamp": str(time.time()),
                        },
                    )

                    logger.info(f"💭 Dream reflection insight: {insight}")

                    if self.current_dream_session:
                        self.current_dream_session.insights_discovered += 1
                        self.insights_discovered += 1

                    return True

            return False

        except Exception as e:
            logger.error(f"Dream reflection error: {e}")
            return False

    async def _dream_plan_future_development(self) -> bool:
        """Plan future development during dream planning phase"""
        try:
            # Create autonomous development goals
            potential_goals = [
                "Improve pattern recognition accuracy",
                "Enhance memory consolidation efficiency",
                "Develop better user preference modeling",
                "Optimize response generation speed",
                "Create more creative solution synthesis",
                "Build better cross-domain knowledge connections",
            ]

            # Select goals based on current system state
            selected_goals = []

            # Goal selection based on system needs
            if self.memory_system and len(self.memory_system.active_memories) > 800:
                selected_goals.append("Enhance memory consolidation efficiency")

            if len(self.creative_projects) < 3:
                selected_goals.append("Create more creative solution synthesis")

            # Always add one random goal for exploration
            remaining_goals = [g for g in potential_goals if g not in selected_goals]
            if remaining_goals:
                selected_goals.append(random.choice(remaining_goals))

            # Store goals
            self.autonomous_goals.extend(selected_goals)

            if selected_goals:
                logger.info(
                    f"🎯 Dream planned development goals: {', '.join(selected_goals)}"
                )

                # Store planning results
                self.coordinator.store_pattern(
                    "dream_planning",
                    {
                        "goals_created": len(selected_goals),
                        "goals": json.dumps(selected_goals),
                        "planning_session": (
                            self.current_dream_session.session_id
                            if self.current_dream_session
                            else "unknown"
                        ),
                        "timestamp": str(time.time()),
                    },
                )

                return True

            return False

        except Exception as e:
            logger.error(f"Dream planning error: {e}")
            return False

    async def _prepare_dream_summary(self):
        """Prepare summary of dream session for user"""
        try:
            if not self.current_dream_session:
                return

            session = self.current_dream_session
            duration_minutes = (session.end_time - session.start_time) / 60

            summary = {
                "session_id": session.session_id,
                "duration_minutes": duration_minutes,
                "activities_completed": f"{session.successful_activities}/{session.total_activities}",
                "insights_discovered": session.insights_discovered,
                "improvements_made": session.improvements_made,
                "creative_outputs": session.creative_outputs,
                "new_goals": len(
                    [g for g in self.autonomous_goals if g not in []]
                ),  # New goals this session
                "summary_message": f"During {duration_minutes:.1f} minutes of autonomous processing, completed {session.successful_activities} activities, discovered {session.insights_discovered} insights, and made {session.improvements_made} system improvements.",
            }

            # Store dream summary for user
            self.coordinator.store_ai_response(
                {
                    "type": "dream_session_summary",
                    "session_summary": summary,
                    "timestamp": str(time.time()),
                }
            )

            logger.info(f"📋 Dream summary prepared: {summary['summary_message']}")

        except Exception as e:
            logger.error(f"Dream summary preparation error: {e}")

    def get_dream_stats(self) -> Dict[str, Any]:
        """Get dream state processing statistics"""
        return {
            "running": self.running,
            "dream_active": self.dream_active,
            "current_phase": self.current_phase.value if self.dream_active else "awake",
            "total_dream_time": self.total_dream_time,
            "dream_sessions_completed": self.dream_sessions_completed,
            "insights_discovered": self.insights_discovered,
            "autonomous_improvements": self.autonomous_improvements,
            "creative_projects": len(self.creative_projects),
            "autonomous_goals": len(self.autonomous_goals),
            "last_user_activity": self.last_user_activity,
            "time_since_activity": time.time() - self.last_user_activity,
            "inactive_threshold": self.inactive_threshold,
            "current_session": (
                {
                    "active": self.current_dream_session is not None,
                    "activities": (
                        self.current_dream_session.total_activities
                        if self.current_dream_session
                        else 0
                    ),
                    "successful_activities": (
                        self.current_dream_session.successful_activities
                        if self.current_dream_session
                        else 0
                    ),
                }
                if self.dream_active
                else None
            ),
        }

    def stop(self):
        """Stop dream state processing"""
        self.running = False

        # If currently dreaming, complete the session
        if self.dream_active:
            asyncio.create_task(self._wake_from_dream())

        logger.info("🛑 Dream State Processor stopped")

        stats = self.get_dream_stats()
        logger.info(
            f"💤 Dream stats: {stats['dream_sessions_completed']} sessions, {stats['total_dream_time']/3600:.1f} hours total"
        )


# Global dream state processor
dream_state_processor = DreamStateProcessor()


async def main():
    """Demo the Dream State Processor"""
    print("💤 DREAM STATE PROCESSOR")
    print("=" * 60)
    print("AI development continues while you sleep")
    print("=" * 60)

    # Start dream processing
    dream_task = asyncio.create_task(dream_state_processor.start_dream_processing())

    print("✅ Dream state processor started")
    print("👁️ Monitoring user activity")
    print("💤 Will enter dream state after 30 minutes of inactivity")
    print(
        "🌙 Dream phases: Consolidation → Exploration → Creativity → Optimization → Reflection → Planning"
    )
    print("🛑 Press Ctrl+C to stop")

    try:
        while True:
            await asyncio.sleep(60)

            # Show dream stats
            stats = dream_state_processor.get_dream_stats()

            if stats["dream_active"]:
                print(f"💤 DREAMING - Phase: {stats['current_phase']}")
                print(
                    f"   Session activities: {stats['current_session']['successful_activities']}/{stats['current_session']['activities']}"
                )
            else:
                time_until_dream = max(
                    0, stats["inactive_threshold"] - stats["time_since_activity"]
                )
                if time_until_dream > 0:
                    print(f"👁️ AWAKE - Dream in {time_until_dream/60:.1f} minutes")
                else:
                    print("👁️ AWAKE - Ready to dream")

            print(
                f"📊 Total: {stats['dream_sessions_completed']} sessions, {stats['insights_discovered']} insights"
            )

    except KeyboardInterrupt:
        print("\n🛑 Stopping Dream State Processor...")
        dream_state_processor.stop()
        await dream_task
        print("✅ Dream State Processor stopped")


if __name__ == "__main__":
    asyncio.run(main())
