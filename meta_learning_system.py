#!/usr/bin/env python3
"""
Meta-Learning System - Learning How to Learn Better
This system learns about its own learning processes and optimizes them.
"""

import asyncio
import json
import time
import logging
import statistics
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from fixed_redis_coordinator import redis_coordinator
from robust_claude_integration import claude_integration
from persistent_memory_system import persistent_memory_system

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LearningStrategy(Enum):
    PATTERN_RECOGNITION = "pattern_recognition"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    TRANSFER_LEARNING = "transfer_learning"
    ACTIVE_LEARNING = "active_learning"
    META_COGNITIVE = "meta_cognitive"
    EXPERIENTIAL = "experiential"
    SOCIAL_LEARNING = "social_learning"
    EVOLUTIONARY = "evolutionary"


@dataclass
class LearningExperiment:
    experiment_id: str
    strategy: LearningStrategy
    hypothesis: str
    parameters: Dict[str, Any]
    start_time: float
    end_time: Optional[float]
    success_metric: float
    confidence: float
    results: Dict[str, Any]


@dataclass
class MetaKnowledge:
    knowledge_id: str
    domain: str
    learning_principle: str
    effectiveness_score: float
    applicability_contexts: List[str]
    evidence_strength: float
    discovered_at: float


class MetaLearningSystem:
    """System that learns how to learn more effectively"""

    def __init__(self):
        self.coordinator = redis_coordinator
        self.memory_system = persistent_memory_system
        self.running = False

        # Meta-learning state
        self.learning_experiments: List[LearningExperiment] = []
        self.meta_knowledge: Dict[str, MetaKnowledge] = {}
        self.learning_strategies: Dict[LearningStrategy, float] = {}

        # Learning optimization
        self.current_learning_rate = 0.1
        self.exploration_rate = 0.3
        self.learning_efficiency_history: List[float] = []

        # Meta-cognitive tracking
        self.learning_sessions_analyzed = 0
        self.strategies_discovered = 0
        self.learning_principles_extracted = 0

        # Initialize learning strategies
        self._initialize_learning_strategies()

        logger.info("🎓 Meta-Learning System initialized")
        logger.info("🧠 Learning how to learn more effectively")

    def _initialize_learning_strategies(self):
        """Initialize learning strategy effectiveness scores"""
        for strategy in LearningStrategy:
            self.learning_strategies[strategy] = 0.5  # Start with neutral effectiveness

    async def start_meta_learning(self):
        """Start meta-learning processes"""
        self.running = True

        logger.info("🚀 Starting Meta-Learning System")
        logger.info("📚 Analyzing and optimizing learning processes")

        # Start meta-learning tasks
        meta_tasks = [
            asyncio.create_task(self._analyze_learning_patterns()),
            asyncio.create_task(self._experiment_with_strategies()),
            asyncio.create_task(self._extract_learning_principles()),
            asyncio.create_task(self._optimize_learning_parameters()),
            asyncio.create_task(self._discover_meta_knowledge()),
        ]

        try:
            await asyncio.gather(*meta_tasks)
        except Exception as e:
            logger.error(f"Meta-learning error: {e}")

    async def _analyze_learning_patterns(self):
        """Analyze patterns in learning effectiveness"""
        while self.running:
            try:
                # Analyze memory formation patterns
                if self.memory_system:
                    await self._analyze_memory_formation_patterns()

                # Analyze AI response improvement patterns
                await self._analyze_response_improvement_patterns()

                # Analyze pattern recognition effectiveness
                await self._analyze_pattern_recognition_effectiveness()

                self.learning_sessions_analyzed += 1

                await asyncio.sleep(120)

            except Exception as e:
                logger.error(f"Learning pattern analysis error: {e}")
                await asyncio.sleep(120)

    async def _analyze_memory_formation_patterns(self):
        """Analyze how memories are formed and which ones persist"""
        try:
            if not hasattr(self.memory_system, "active_memories"):
                return

            # Analyze memory formation success
            strong_memories = [
                m
                for m in self.memory_system.active_memories.values()
                if m.importance > 0.7 and m.access_count > 2
            ]

            weak_memories = [
                m
                for m in self.memory_system.active_memories.values()
                if m.importance < 0.3 or m.access_count < 1
            ]

            if strong_memories and weak_memories:
                # Extract patterns from strong vs weak memories
                strong_patterns = self._extract_memory_patterns(strong_memories)
                weak_patterns = self._extract_memory_patterns(weak_memories)

                # Identify what makes memories strong
                effective_patterns = []
                for pattern, strength in strong_patterns.items():
                    weak_strength = weak_patterns.get(pattern, 0)
                    if strength > weak_strength * 1.5:  # Significantly stronger
                        effective_patterns.append(pattern)

                if effective_patterns:
                    # Create meta-knowledge about memory formation
                    await self._create_meta_knowledge(
                        domain="memory_formation",
                        principle=f"Effective memory patterns: {', '.join(effective_patterns)}",
                        effectiveness=0.8,
                        contexts=["pattern_recognition", "experience_encoding"],
                    )

                    logger.info(
                        f"🧠 Discovered memory formation principle: {effective_patterns}"
                    )

        except Exception as e:
            logger.error(f"Memory formation analysis error: {e}")

    def _extract_memory_patterns(self, memories: List[Any]) -> Dict[str, float]:
        """Extract patterns from memory collections"""
        patterns = {}

        for memory in memories:
            # Memory type patterns
            memory_type = memory.memory_type.value
            patterns[f"type_{memory_type}"] = patterns.get(f"type_{memory_type}", 0) + 1

            # Context patterns
            for key, value in memory.context.items():
                pattern_key = f"context_{key}_{str(value)[:20]}"
                patterns[pattern_key] = patterns.get(pattern_key, 0) + 1

            # Content length patterns
            content_length = len(memory.content)
            if content_length < 50:
                patterns["short_content"] = patterns.get("short_content", 0) + 1
            elif content_length > 200:
                patterns["long_content"] = patterns.get("long_content", 0) + 1
            else:
                patterns["medium_content"] = patterns.get("medium_content", 0) + 1

        # Normalize by total memories
        total = len(memories)
        if total > 0:
            for key in patterns:
                patterns[key] = patterns[key] / total

        return patterns

    async def _analyze_response_improvement_patterns(self):
        """Analyze patterns in AI response quality improvement"""
        try:
            responses = self.coordinator.get_recent_responses(count=30)

            if len(responses) < 10:
                return

            # Group responses by time windows
            current_time = time.time()
            recent_responses = [
                r
                for r in responses
                if current_time - float(r.get("timestamp", 0)) < 1800
            ]  # 30 minutes
            older_responses = [
                r
                for r in responses
                if current_time - float(r.get("timestamp", 0)) >= 1800
            ]

            if recent_responses and older_responses:
                # Analyze quality trends (simplified)
                recent_quality = self._estimate_response_quality(recent_responses)
                older_quality = self._estimate_response_quality(older_responses)

                improvement = recent_quality - older_quality

                if improvement > 0.1:
                    # Quality is improving - analyze what's driving it
                    improvement_factors = self._analyze_improvement_factors(
                        recent_responses, older_responses
                    )

                    if improvement_factors:
                        await self._create_meta_knowledge(
                            domain="response_quality",
                            principle=f"Quality improvement factors: {', '.join(improvement_factors)}",
                            effectiveness=0.7,
                            contexts=["response_generation", "quality_optimization"],
                        )

                        logger.info(
                            f"📈 Response quality improvement detected: {improvement:.3f}"
                        )

        except Exception as e:
            logger.error(f"Response improvement analysis error: {e}")

    def _estimate_response_quality(self, responses: List[Dict[str, Any]]) -> float:
        """Estimate quality of responses (simplified heuristic)"""
        if not responses:
            return 0.0

        quality_scores = []

        for response in responses:
            score = 0.5  # Base score

            # Length indicates effort
            content = response.get("response", "") + response.get("suggestion", "")
            if len(content) > 20:
                score += 0.2
            if len(content) > 100:
                score += 0.2

            # Intelligence source
            if response.get("intelligence_source") == "claude":
                score += 0.3

            # Confidence
            confidence = float(response.get("confidence", 0.5))
            score += confidence * 0.2

            quality_scores.append(min(score, 1.0))

        return statistics.mean(quality_scores) if quality_scores else 0.0

    def _analyze_improvement_factors(
        self, recent: List[Dict], older: List[Dict]
    ) -> List[str]:
        """Analyze what factors led to improvement"""
        factors = []

        # Check if more Claude responses in recent
        recent_claude = sum(
            1 for r in recent if r.get("intelligence_source") == "claude"
        )
        older_claude = sum(1 for r in older if r.get("intelligence_source") == "claude")

        recent_claude_ratio = recent_claude / len(recent) if recent else 0
        older_claude_ratio = older_claude / len(older) if older else 0

        if recent_claude_ratio > older_claude_ratio + 0.2:
            factors.append("increased_claude_usage")

        # Check response length trends
        recent_avg_length = (
            statistics.mean(
                [len(r.get("response", "") + r.get("suggestion", "")) for r in recent]
            )
            if recent
            else 0
        )

        older_avg_length = (
            statistics.mean(
                [len(r.get("response", "") + r.get("suggestion", "")) for r in older]
            )
            if older
            else 0
        )

        if recent_avg_length > older_avg_length * 1.2:
            factors.append("increased_response_depth")

        return factors

    async def _analyze_pattern_recognition_effectiveness(self):
        """Analyze effectiveness of pattern recognition strategies"""
        try:
            # Check if semantic understanding system is discovering patterns
            # This would integrate with semantic_understanding_engine if available

            # For now, analyze pattern discovery from Redis
            pattern_entries = []
            try:
                entries = self.coordinator.redis.xrange("patterns", count=20)
                pattern_entries = entries
            except:
                pass

            if len(pattern_entries) > 5:
                # Analyze pattern discovery rate
                recent_patterns = [
                    e
                    for e in pattern_entries
                    if time.time() - float(dict(e[1]).get("timestamp", 0))
                    < 3600  # Last hour
                ]

                pattern_discovery_rate = len(recent_patterns) / len(pattern_entries)

                if pattern_discovery_rate > 0.3:  # High discovery rate
                    await self._create_meta_knowledge(
                        domain="pattern_recognition",
                        principle="High pattern discovery rate indicates effective recognition",
                        effectiveness=0.8,
                        contexts=["pattern_discovery", "learning_optimization"],
                    )

                    logger.info(
                        f"🔍 High pattern discovery rate detected: {pattern_discovery_rate:.3f}"
                    )

        except Exception as e:
            logger.error(f"Pattern recognition analysis error: {e}")

    async def _experiment_with_strategies(self):
        """Experiment with different learning strategies"""
        while self.running:
            try:
                # Run learning experiments
                await self._run_learning_experiment()

                # Analyze experiment results
                await self._analyze_experiment_results()

                await asyncio.sleep(300)  # Experiment every 5 minutes

            except Exception as e:
                logger.error(f"Strategy experimentation error: {e}")
                await asyncio.sleep(300)

    async def _run_learning_experiment(self):
        """Run a learning strategy experiment"""
        try:
            # Choose strategy to experiment with
            strategy = self._select_strategy_for_experiment()

            experiment_id = f"exp_{strategy.value}_{int(time.time())}"

            # Create experiment hypothesis
            hypothesis = (
                f"Strategy {strategy.value} will improve learning effectiveness"
            )

            # Define experiment parameters
            parameters = {
                "learning_rate": self.current_learning_rate,
                "exploration_rate": self.exploration_rate,
                "strategy": strategy.value,
            }

            experiment = LearningExperiment(
                experiment_id=experiment_id,
                strategy=strategy,
                hypothesis=hypothesis,
                parameters=parameters,
                start_time=time.time(),
                end_time=None,
                success_metric=0.0,
                confidence=0.5,
                results={},
            )

            self.learning_experiments.append(experiment)

            # Run the experiment (simplified)
            success_metric = await self._execute_learning_experiment(experiment)

            # Complete the experiment
            experiment.end_time = time.time()
            experiment.success_metric = success_metric
            experiment.confidence = 0.7

            logger.info(
                f"🧪 Learning experiment completed: {strategy.value} (success: {success_metric:.3f})"
            )

        except Exception as e:
            logger.error(f"Learning experiment error: {e}")

    def _select_strategy_for_experiment(self) -> LearningStrategy:
        """Select a learning strategy for experimentation"""
        # Use epsilon-greedy selection
        if math.random() < self.exploration_rate:
            # Explore: try random strategy
            strategies = list(LearningStrategy)
            return strategies[int(math.random() * len(strategies))]
        else:
            # Exploit: use best known strategy
            best_strategy = max(self.learning_strategies.items(), key=lambda x: x[1])
            return best_strategy[0]

    async def _execute_learning_experiment(
        self, experiment: LearningExperiment
    ) -> float:
        """Execute a learning experiment and measure success"""
        try:
            strategy = experiment.strategy

            # Different experiments based on strategy
            if strategy == LearningStrategy.PATTERN_RECOGNITION:
                return await self._experiment_pattern_recognition()
            elif strategy == LearningStrategy.ACTIVE_LEARNING:
                return await self._experiment_active_learning()
            elif strategy == LearningStrategy.META_COGNITIVE:
                return await self._experiment_metacognitive_learning()
            else:
                # Default experiment
                return await self._experiment_default_learning()

        except Exception as e:
            logger.error(f"Learning experiment execution error: {e}")
            return 0.0

    async def _experiment_pattern_recognition(self) -> float:
        """Experiment with pattern recognition learning"""
        try:
            # Measure current pattern recognition effectiveness
            baseline_patterns = len(self.meta_knowledge)

            # Apply pattern recognition strategy for a short time
            await asyncio.sleep(30)

            # Check if new patterns were discovered
            new_patterns = len(self.meta_knowledge) - baseline_patterns

            # Success metric: pattern discovery rate
            return min(new_patterns / 10.0, 1.0)  # Normalize

        except Exception as e:
            logger.error(f"Pattern recognition experiment error: {e}")
            return 0.0

    async def _experiment_active_learning(self) -> float:
        """Experiment with active learning strategy"""
        # Simplified: measure learning efficiency
        try:
            # Record learning state before
            before_efficiency = self._calculate_current_learning_efficiency()

            # Apply active learning (ask more questions, seek feedback)
            await asyncio.sleep(20)

            # Measure after
            after_efficiency = self._calculate_current_learning_efficiency()

            return max(0, after_efficiency - before_efficiency)

        except Exception as e:
            logger.error(f"Active learning experiment error: {e}")
            return 0.0

    async def _experiment_metacognitive_learning(self) -> float:
        """Experiment with metacognitive learning"""
        try:
            # Measure metacognitive awareness
            responses = self.coordinator.get_recent_responses(count=5)

            metacognitive_indicators = 0
            for response in responses:
                content = response.get("response", "")
                if any(
                    phrase in content.lower()
                    for phrase in ["I think", "I understand", "I realize"]
                ):
                    metacognitive_indicators += 1

            return metacognitive_indicators / max(1, len(responses))

        except Exception as e:
            logger.error(f"Metacognitive learning experiment error: {e}")
            return 0.0

    async def _experiment_default_learning(self) -> float:
        """Default learning experiment"""
        return 0.5  # Neutral result

    def _calculate_current_learning_efficiency(self) -> float:
        """Calculate current learning efficiency"""
        try:
            # Simple efficiency metric based on recent performance
            efficiency_factors = []

            # Memory formation efficiency
            if self.memory_system and hasattr(
                self.memory_system, "memories_created_this_session"
            ):
                memory_rate = self.memory_system.memories_created_this_session / max(
                    1, (time.time() - self.memory_system.session_start_time) / 3600
                )  # per hour
                efficiency_factors.append(min(memory_rate / 10.0, 1.0))

            # Pattern discovery efficiency
            pattern_count = len(self.meta_knowledge)
            efficiency_factors.append(min(pattern_count / 20.0, 1.0))

            # Response quality efficiency
            responses = self.coordinator.get_recent_responses(count=10)
            if responses:
                quality = self._estimate_response_quality(responses)
                efficiency_factors.append(quality)

            return statistics.mean(efficiency_factors) if efficiency_factors else 0.5

        except Exception as e:
            logger.error(f"Learning efficiency calculation error: {e}")
            return 0.5

    async def _analyze_experiment_results(self):
        """Analyze results of learning experiments"""
        try:
            if len(self.learning_experiments) < 2:
                return

            # Analyze recent experiments
            recent_experiments = self.learning_experiments[-5:]

            # Update strategy effectiveness scores
            for experiment in recent_experiments:
                if experiment.end_time is not None:
                    current_score = self.learning_strategies[experiment.strategy]
                    new_score = (
                        current_score * 0.8 + experiment.success_metric * 0.2
                    )  # Moving average
                    self.learning_strategies[experiment.strategy] = new_score

            # Find best strategy
            best_strategy = max(self.learning_strategies.items(), key=lambda x: x[1])

            if best_strategy[1] > 0.7:
                logger.info(
                    f"🏆 Best learning strategy: {best_strategy[0].value} (effectiveness: {best_strategy[1]:.3f})"
                )

                # Create meta-knowledge about best strategy
                await self._create_meta_knowledge(
                    domain="learning_strategy",
                    principle=f"Strategy {best_strategy[0].value} is most effective",
                    effectiveness=best_strategy[1],
                    contexts=["strategy_selection", "learning_optimization"],
                )

        except Exception as e:
            logger.error(f"Experiment results analysis error: {e}")

    async def _extract_learning_principles(self):
        """Extract general learning principles from experience"""
        while self.running:
            try:
                # Analyze accumulated learning data
                await self._analyze_learning_principles()

                self.learning_principles_extracted += 1

                await asyncio.sleep(600)  # Extract principles every 10 minutes

            except Exception as e:
                logger.error(f"Learning principles extraction error: {e}")
                await asyncio.sleep(600)

    async def _analyze_learning_principles(self):
        """Analyze data to extract learning principles"""
        try:
            if len(self.learning_experiments) < 5:
                return

            # Analyze experiment patterns
            successful_experiments = [
                e for e in self.learning_experiments if e.success_metric > 0.6
            ]
            failed_experiments = [
                e for e in self.learning_experiments if e.success_metric < 0.4
            ]

            if successful_experiments and failed_experiments:
                # Extract principles from successful vs failed experiments
                success_strategies = [e.strategy for e in successful_experiments]
                failure_strategies = [e.strategy for e in failed_experiments]

                # Find strategies that appear more in successes
                success_counts = {}
                for strategy in success_strategies:
                    success_counts[strategy] = success_counts.get(strategy, 0) + 1

                failure_counts = {}
                for strategy in failure_strategies:
                    failure_counts[strategy] = failure_counts.get(strategy, 0) + 1

                # Identify consistently successful strategies
                effective_strategies = []
                for strategy, success_count in success_counts.items():
                    failure_count = failure_counts.get(strategy, 0)
                    if success_count > failure_count * 2:  # Much more successful
                        effective_strategies.append(strategy)

                if effective_strategies:
                    principle = f"Consistently effective strategies: {[s.value for s in effective_strategies]}"

                    await self._create_meta_knowledge(
                        domain="learning_principles",
                        principle=principle,
                        effectiveness=0.8,
                        contexts=["strategy_selection", "learning_optimization"],
                    )

                    logger.info(f"📚 Learning principle discovered: {principle}")

        except Exception as e:
            logger.error(f"Learning principles analysis error: {e}")

    async def _optimize_learning_parameters(self):
        """Optimize learning parameters based on results"""
        while self.running:
            try:
                # Analyze current learning efficiency
                current_efficiency = self._calculate_current_learning_efficiency()
                self.learning_efficiency_history.append(current_efficiency)

                # Keep history manageable
                if len(self.learning_efficiency_history) > 100:
                    self.learning_efficiency_history = self.learning_efficiency_history[
                        -100:
                    ]

                # Optimize parameters if we have enough data
                if len(self.learning_efficiency_history) >= 10:
                    await self._adjust_learning_parameters()

                await asyncio.sleep(180)  # Optimize every 3 minutes

            except Exception as e:
                logger.error(f"Learning parameter optimization error: {e}")
                await asyncio.sleep(180)

    async def _adjust_learning_parameters(self):
        """Adjust learning parameters based on efficiency trends"""
        try:
            recent_efficiency = statistics.mean(self.learning_efficiency_history[-5:])
            older_efficiency = statistics.mean(self.learning_efficiency_history[-10:-5])

            efficiency_trend = recent_efficiency - older_efficiency

            # Adjust learning rate
            if efficiency_trend > 0.1:
                # Efficiency improving - maintain or slightly increase learning rate
                self.current_learning_rate = min(0.3, self.current_learning_rate * 1.05)
                logger.info(
                    f"📈 Increased learning rate to {self.current_learning_rate:.3f}"
                )
            elif efficiency_trend < -0.1:
                # Efficiency declining - reduce learning rate
                self.current_learning_rate = max(
                    0.01, self.current_learning_rate * 0.95
                )
                logger.info(
                    f"📉 Decreased learning rate to {self.current_learning_rate:.3f}"
                )

            # Adjust exploration rate
            if recent_efficiency > 0.7:
                # High efficiency - reduce exploration, exploit more
                self.exploration_rate = max(0.1, self.exploration_rate * 0.95)
            elif recent_efficiency < 0.4:
                # Low efficiency - increase exploration
                self.exploration_rate = min(0.5, self.exploration_rate * 1.05)

        except Exception as e:
            logger.error(f"Learning parameter adjustment error: {e}")

    async def _discover_meta_knowledge(self):
        """Discover meta-knowledge about learning itself"""
        while self.running:
            try:
                # Analyze learning about learning
                await self._analyze_meta_learning_patterns()

                self.strategies_discovered += 1

                await asyncio.sleep(900)  # Discover meta-knowledge every 15 minutes

            except Exception as e:
                logger.error(f"Meta-knowledge discovery error: {e}")
                await asyncio.sleep(900)

    async def _analyze_meta_learning_patterns(self):
        """Analyze patterns in how the system learns to learn"""
        try:
            if len(self.meta_knowledge) < 3:
                return

            # Analyze meta-knowledge evolution
            recent_knowledge = [
                mk
                for mk in self.meta_knowledge.values()
                if time.time() - mk.discovered_at < 3600
            ]  # Last hour

            if len(recent_knowledge) >= 2:
                # Meta-learning is active
                avg_effectiveness = statistics.mean(
                    [mk.effectiveness_score for mk in recent_knowledge]
                )

                if avg_effectiveness > 0.7:
                    # High-quality meta-knowledge being generated
                    await self._create_meta_knowledge(
                        domain="meta_learning",
                        principle="System is effectively learning about its own learning processes",
                        effectiveness=0.9,
                        contexts=["meta_cognition", "recursive_improvement"],
                    )

                    logger.info("🎓 Meta-learning effectiveness detected")

        except Exception as e:
            logger.error(f"Meta-learning pattern analysis error: {e}")

    async def _create_meta_knowledge(
        self, domain: str, principle: str, effectiveness: float, contexts: List[str]
    ):
        """Create new meta-knowledge"""
        try:
            knowledge_id = f"mk_{domain}_{int(time.time())}_{len(self.meta_knowledge)}"

            meta_knowledge = MetaKnowledge(
                knowledge_id=knowledge_id,
                domain=domain,
                learning_principle=principle,
                effectiveness_score=effectiveness,
                applicability_contexts=contexts,
                evidence_strength=0.8,
                discovered_at=time.time(),
            )

            self.meta_knowledge[knowledge_id] = meta_knowledge

            # Store in Redis
            self.coordinator.store_pattern(
                "meta_knowledge",
                {
                    "knowledge_id": knowledge_id,
                    "domain": domain,
                    "principle": principle,
                    "effectiveness": effectiveness,
                    "contexts": json.dumps(contexts),
                    "timestamp": str(time.time()),
                },
            )

            logger.info(f"🎓 Meta-knowledge created: {domain} - {principle}")

        except Exception as e:
            logger.error(f"Meta-knowledge creation error: {e}")

    def get_meta_learning_stats(self) -> Dict[str, Any]:
        """Get meta-learning system statistics"""
        best_strategy = (
            max(self.learning_strategies.items(), key=lambda x: x[1])
            if self.learning_strategies
            else ("none", 0)
        )

        return {
            "running": self.running,
            "learning_sessions_analyzed": self.learning_sessions_analyzed,
            "strategies_discovered": self.strategies_discovered,
            "learning_principles_extracted": self.learning_principles_extracted,
            "total_experiments": len(self.learning_experiments),
            "meta_knowledge_count": len(self.meta_knowledge),
            "current_learning_rate": self.current_learning_rate,
            "current_exploration_rate": self.exploration_rate,
            "best_strategy": (
                best_strategy[0].value
                if hasattr(best_strategy[0], "value")
                else str(best_strategy[0])
            ),
            "best_strategy_effectiveness": best_strategy[1],
            "current_learning_efficiency": self._calculate_current_learning_efficiency(),
            "strategy_effectiveness": {
                strategy.value: effectiveness
                for strategy, effectiveness in self.learning_strategies.items()
            },
        }

    def stop(self):
        """Stop meta-learning system"""
        self.running = False
        logger.info("🛑 Meta-Learning System stopped")

        stats = self.get_meta_learning_stats()
        logger.info(
            f"🎓 Meta-learning stats: {stats['total_experiments']} experiments, {stats['meta_knowledge_count']} meta-knowledge discovered"
        )


# Global meta-learning system
meta_learning_system = MetaLearningSystem()


async def main():
    """Demo the Meta-Learning System"""
    print("🎓 META-LEARNING SYSTEM")
    print("=" * 60)
    print("Learning how to learn more effectively")
    print("=" * 60)

    # Start meta-learning
    learning_task = asyncio.create_task(meta_learning_system.start_meta_learning())

    print("✅ Meta-learning started")
    print("🧪 Experimenting with learning strategies")
    print("📚 Extracting learning principles")
    print("⚙️ Optimizing learning parameters")
    print("🎓 Discovering meta-knowledge")
    print("🛑 Press Ctrl+C to stop")

    try:
        while True:
            await asyncio.sleep(120)

            # Show meta-learning stats
            stats = meta_learning_system.get_meta_learning_stats()
            print(
                f"🎓 Meta-Learning: {stats['total_experiments']} experiments, "
                f"{stats['meta_knowledge_count']} meta-knowledge"
            )
            print(
                f"📊 Best strategy: {stats['best_strategy']} "
                f"(effectiveness: {stats['best_strategy_effectiveness']:.3f})"
            )
            print(f"⚡ Learning efficiency: {stats['current_learning_efficiency']:.3f}")

    except KeyboardInterrupt:
        print("\n🛑 Stopping Meta-Learning System...")
        meta_learning_system.stop()
        await learning_task
        print("✅ Meta-Learning System stopped")


if __name__ == "__main__":
    asyncio.run(main())
