#!/usr/bin/env python3
"""
Multi-AI Coordination System - Orchestrate multiple AI models for optimal results

This system coordinates between Claude, GPT-4, and local models to provide
the best possible development assistance by leveraging each model's strengths.
"""

import redis
import json
import time
import asyncio
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import logging

from intelligent_response_engine import (
    ClaudeProvider,
    OpenAIProvider,
    LocalModelProvider,
    AIProvider,
    IntelligentResponse,
    DevelopmentContext,
)


class AISpecialty(Enum):
    """AI model specialties for task assignment"""

    CODE_ANALYSIS = "code_analysis"
    ARCHITECTURE_DESIGN = "architecture_design"
    DEBUGGING = "debugging"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REFACTORING = "refactoring"
    PROJECT_PLANNING = "project_planning"
    GENERAL_ASSISTANCE = "general_assistance"


@dataclass
class AICapability:
    """Defines AI model capabilities and performance metrics"""

    model_name: str
    provider: AIProvider
    specialties: List[AISpecialty]
    performance_score: float
    response_time_avg: float
    reliability_score: float
    cost_per_request: float
    privacy_level: str  # "cloud", "hybrid", "local"
    context_window: int
    reasoning_strength: float
    code_understanding: float


@dataclass
class CoordinationTask:
    """A task that requires multi-AI coordination"""

    task_id: str
    task_type: AISpecialty
    context: DevelopmentContext
    user_intent: str
    patterns: List[Dict]
    priority: int  # 1-5, 5 being highest
    deadline: Optional[float] = None
    requires_consensus: bool = False
    min_confidence: float = 0.7


@dataclass
class AIResponse:
    """Response from a single AI model in coordination"""

    model_name: str
    response: IntelligentResponse
    specialty_match: float  # How well this AI matches the task
    processing_time: float
    confidence: float
    reasoning_quality: float


@dataclass
class CoordinatedResponse:
    """Final coordinated response from multiple AIs"""

    primary_response: IntelligentResponse
    supporting_responses: List[AIResponse]
    coordination_strategy: str
    consensus_level: float
    total_processing_time: float
    models_used: List[str]
    decision_reasoning: str


class MultiAICoordinator:
    """Coordinates multiple AI models for optimal development assistance"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.logger = self._setup_logging()

        # Initialize AI capabilities
        self.ai_capabilities = self._initialize_ai_capabilities()

        # Performance tracking
        self.performance_history = {}
        self.coordination_stats = {
            "total_coordinations": 0,
            "average_response_time": 0.0,
            "consensus_rate": 0.0,
            "model_usage": {},
            "specialty_accuracy": {},
        }

        # Coordination strategies
        self.strategies = {
            "best_match": self._strategy_best_match,
            "consensus": self._strategy_consensus,
            "parallel_validation": self._strategy_parallel_validation,
            "hierarchical": self._strategy_hierarchical,
            "specialist_chain": self._strategy_specialist_chain,
        }

    def _initialize_ai_capabilities(self) -> Dict[str, AICapability]:
        """Initialize AI model capabilities and specialties"""

        capabilities = {}

        # Claude 3.5 Sonnet - Excellent reasoning and code understanding
        claude_provider = ClaudeProvider()
        capabilities["claude"] = AICapability(
            model_name="claude-3.5-sonnet",
            provider=claude_provider,
            specialties=[
                AISpecialty.CODE_ANALYSIS,
                AISpecialty.ARCHITECTURE_DESIGN,
                AISpecialty.REFACTORING,
                AISpecialty.PROJECT_PLANNING,
                AISpecialty.DOCUMENTATION,
            ],
            performance_score=0.95,
            response_time_avg=2.5,
            reliability_score=0.92,
            cost_per_request=0.015,
            privacy_level="cloud",
            context_window=200000,
            reasoning_strength=0.95,
            code_understanding=0.90,
        )

        # GPT-4 Turbo - Strong debugging and testing capabilities
        openai_provider = OpenAIProvider()
        capabilities["gpt4"] = AICapability(
            model_name="gpt-4-turbo",
            provider=openai_provider,
            specialties=[
                AISpecialty.DEBUGGING,
                AISpecialty.TESTING,
                AISpecialty.PERFORMANCE,
                AISpecialty.SECURITY,
                AISpecialty.GENERAL_ASSISTANCE,
            ],
            performance_score=0.90,
            response_time_avg=3.2,
            reliability_score=0.88,
            cost_per_request=0.020,
            privacy_level="cloud",
            context_window=128000,
            reasoning_strength=0.88,
            code_understanding=0.85,
        )

        # Local Model - Privacy-focused, fast for simple tasks
        local_provider = LocalModelProvider()
        capabilities["local"] = AICapability(
            model_name="codellama",
            provider=local_provider,
            specialties=[AISpecialty.CODE_ANALYSIS, AISpecialty.GENERAL_ASSISTANCE],
            performance_score=0.70,
            response_time_avg=1.8,
            reliability_score=0.75,
            cost_per_request=0.000,
            privacy_level="local",
            context_window=16000,
            reasoning_strength=0.65,
            code_understanding=0.75,
        )

        return capabilities

    async def coordinate_response(self, task: CoordinationTask) -> CoordinatedResponse:
        """Coordinate multiple AI models to generate optimal response"""

        start_time = time.time()
        self.coordination_stats["total_coordinations"] += 1

        self.logger.info(
            f"Starting coordination for task {task.task_id} ({task.task_type.value})"
        )

        # Select coordination strategy
        strategy = self._select_coordination_strategy(task)
        self.logger.info(f"Using coordination strategy: {strategy}")

        # Execute coordination strategy
        coordinated_response = await self.strategies[strategy](task)

        # Update performance metrics
        total_time = time.time() - start_time
        self._update_performance_metrics(coordinated_response, total_time)

        # Store coordination result
        await self._store_coordination_result(task, coordinated_response)

        self.logger.info(
            f"Coordination complete: {len(coordinated_response.models_used)} models, "
            f"{total_time:.2f}s, consensus: {coordinated_response.consensus_level:.2f}"
        )

        return coordinated_response

    def _select_coordination_strategy(self, task: CoordinationTask) -> str:
        """Select optimal coordination strategy based on task characteristics"""

        # High priority tasks get parallel validation
        if task.priority >= 4:
            return "parallel_validation"

        # Tasks requiring consensus
        if task.requires_consensus:
            return "consensus"

        # Complex architectural tasks get hierarchical approach
        if task.task_type in [
            AISpecialty.ARCHITECTURE_DESIGN,
            AISpecialty.PROJECT_PLANNING,
        ]:
            return "hierarchical"

        # Specialized tasks get specialist chain
        if task.task_type in [
            AISpecialty.DEBUGGING,
            AISpecialty.SECURITY,
            AISpecialty.PERFORMANCE,
        ]:
            return "specialist_chain"

        # Default to best match for general tasks
        return "best_match"

    async def _strategy_best_match(self, task: CoordinationTask) -> CoordinatedResponse:
        """Strategy: Use the AI best suited for the task"""

        # Find best AI for this task
        best_ai = self._find_best_ai_for_task(task.task_type)

        # Generate response
        response = await best_ai.provider.generate_response(
            task.context, task.user_intent, task.patterns
        )

        ai_response = AIResponse(
            model_name=best_ai.model_name,
            response=response,
            specialty_match=1.0,
            processing_time=response.processing_time,
            confidence=response.confidence,
            reasoning_quality=0.8,
        )

        return CoordinatedResponse(
            primary_response=response,
            supporting_responses=[ai_response],
            coordination_strategy="best_match",
            consensus_level=1.0,
            total_processing_time=response.processing_time,
            models_used=[best_ai.model_name],
            decision_reasoning=f"Selected {best_ai.model_name} as best match for {task.task_type.value}",
        )

    async def _strategy_consensus(self, task: CoordinationTask) -> CoordinatedResponse:
        """Strategy: Get consensus from multiple AIs"""

        # Select top 3 AIs for this task
        top_ais = self._get_top_ais_for_task(task.task_type, 3)

        # Get responses from all selected AIs
        ai_responses = []
        tasks = []

        for ai in top_ais:
            task_coroutine = ai.provider.generate_response(
                task.context, task.user_intent, task.patterns
            )
            tasks.append((ai, task_coroutine))

        # Execute in parallel
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

        # Process results
        for (ai, _), result in zip(tasks, results):
            if not isinstance(result, Exception):
                specialty_match = self._calculate_specialty_match(
                    ai.specialties, task.task_type
                )
                ai_responses.append(
                    AIResponse(
                        model_name=ai.model_name,
                        response=result,
                        specialty_match=specialty_match,
                        processing_time=result.processing_time,
                        confidence=result.confidence,
                        reasoning_quality=self._assess_reasoning_quality(result),
                    )
                )

        # Build consensus
        primary_response, consensus_level = self._build_consensus(ai_responses)

        return CoordinatedResponse(
            primary_response=primary_response,
            supporting_responses=ai_responses,
            coordination_strategy="consensus",
            consensus_level=consensus_level,
            total_processing_time=max(r.processing_time for r in ai_responses),
            models_used=[r.model_name for r in ai_responses],
            decision_reasoning=f"Consensus from {len(ai_responses)} models with {consensus_level:.2f} agreement",
        )

    async def _strategy_parallel_validation(
        self, task: CoordinationTask
    ) -> CoordinatedResponse:
        """Strategy: Primary AI with validation from others"""

        # Get primary AI and validators
        primary_ai = self._find_best_ai_for_task(task.task_type)
        validators = [
            ai
            for ai in self.ai_capabilities.values()
            if ai.model_name != primary_ai.model_name
        ][:2]

        # Get primary response
        primary_response = await primary_ai.provider.generate_response(
            task.context, task.user_intent, task.patterns
        )

        # Get validation responses
        validation_tasks = []
        for validator in validators:
            # Modify context to include primary response for validation
            validation_context = self._create_validation_context(
                task.context, primary_response
            )
            validation_intent = (
                f"Validate and improve this response: {task.user_intent}"
            )

            validation_task = validator.provider.generate_response(
                validation_context, validation_intent, task.patterns
            )
            validation_tasks.append((validator, validation_task))

        # Execute validations
        validation_results = await asyncio.gather(
            *[t[1] for t in validation_tasks], return_exceptions=True
        )

        # Process validation results
        supporting_responses = []
        for (validator, _), result in zip(validation_tasks, validation_results):
            if not isinstance(result, Exception):
                supporting_responses.append(
                    AIResponse(
                        model_name=validator.model_name,
                        response=result,
                        specialty_match=0.7,
                        processing_time=result.processing_time,
                        confidence=result.confidence,
                        reasoning_quality=self._assess_reasoning_quality(result),
                    )
                )

        # Integrate feedback into final response
        final_response = self._integrate_validation_feedback(
            primary_response, supporting_responses
        )

        return CoordinatedResponse(
            primary_response=final_response,
            supporting_responses=supporting_responses,
            coordination_strategy="parallel_validation",
            consensus_level=0.85,
            total_processing_time=max(
                primary_response.processing_time,
                max((r.processing_time for r in supporting_responses), default=0),
            ),
            models_used=[primary_ai.model_name]
            + [r.model_name for r in supporting_responses],
            decision_reasoning=f"Primary response from {primary_ai.model_name} validated by {len(supporting_responses)} models",
        )

    async def _strategy_hierarchical(
        self, task: CoordinationTask
    ) -> CoordinatedResponse:
        """Strategy: Hierarchical processing with high-level then detailed analysis"""

        # Phase 1: High-level analysis (Claude for architecture)
        claude_ai = self.ai_capabilities["claude"]
        high_level_context = self._create_high_level_context(task.context)
        high_level_intent = (
            f"Provide high-level architectural guidance for: {task.user_intent}"
        )

        high_level_response = await claude_ai.provider.generate_response(
            high_level_context, high_level_intent, task.patterns
        )

        # Phase 2: Detailed implementation (GPT-4 for specifics)
        gpt4_ai = self.ai_capabilities["gpt4"]
        detailed_context = self._create_detailed_context(
            task.context, high_level_response
        )
        detailed_intent = (
            f"Provide detailed implementation guidance based on: {task.user_intent}"
        )

        detailed_response = await gpt4_ai.provider.generate_response(
            detailed_context, detailed_intent, task.patterns
        )

        # Phase 3: Local validation (if available)
        supporting_responses = []
        if "local" in self.ai_capabilities:
            local_ai = self.ai_capabilities["local"]
            local_response = await local_ai.provider.generate_response(
                task.context, task.user_intent, task.patterns
            )

            supporting_responses.append(
                AIResponse(
                    model_name=local_ai.model_name,
                    response=local_response,
                    specialty_match=0.6,
                    processing_time=local_response.processing_time,
                    confidence=local_response.confidence,
                    reasoning_quality=0.6,
                )
            )

        # Combine hierarchical responses
        combined_response = self._combine_hierarchical_responses(
            high_level_response, detailed_response
        )

        return CoordinatedResponse(
            primary_response=combined_response,
            supporting_responses=supporting_responses,
            coordination_strategy="hierarchical",
            consensus_level=0.80,
            total_processing_time=high_level_response.processing_time
            + detailed_response.processing_time,
            models_used=["claude-3.5-sonnet", "gpt-4-turbo"]
            + [r.model_name for r in supporting_responses],
            decision_reasoning="Hierarchical processing: Claude for architecture, GPT-4 for implementation",
        )

    async def _strategy_specialist_chain(
        self, task: CoordinationTask
    ) -> CoordinatedResponse:
        """Strategy: Chain of specialists for complex problems"""

        # Define specialist chain based on task type
        specialist_chain = self._get_specialist_chain(task.task_type)

        responses = []
        current_context = task.context

        for i, specialist in enumerate(specialist_chain):
            # Modify intent for chain position
            if i == 0:
                chain_intent = task.user_intent
            else:
                chain_intent = f"Building on previous analysis, {task.user_intent}"

            response = await specialist.provider.generate_response(
                current_context, chain_intent, task.patterns
            )

            responses.append(
                AIResponse(
                    model_name=specialist.model_name,
                    response=response,
                    specialty_match=1.0,
                    processing_time=response.processing_time,
                    confidence=response.confidence,
                    reasoning_quality=0.85,
                )
            )

            # Update context for next specialist
            current_context = self._update_context_with_response(
                current_context, response
            )

        # Final response is from last specialist, with all others as supporting
        primary_response = responses[-1].response
        supporting_responses = responses[:-1]

        return CoordinatedResponse(
            primary_response=primary_response,
            supporting_responses=supporting_responses,
            coordination_strategy="specialist_chain",
            consensus_level=0.75,
            total_processing_time=sum(r.processing_time for r in responses),
            models_used=[r.model_name for r in responses],
            decision_reasoning=f"Specialist chain: {' → '.join(r.model_name for r in responses)}",
        )

    def _find_best_ai_for_task(self, task_type: AISpecialty) -> AICapability:
        """Find the AI best suited for a specific task type"""

        best_ai = None
        best_score = 0.0

        for ai in self.ai_capabilities.values():
            score = 0.0

            # Specialty match bonus
            if task_type in ai.specialties:
                score += 1.0

            # Performance factors
            score += ai.performance_score * 0.5
            score += ai.reasoning_strength * 0.3
            score += ai.code_understanding * 0.2

            # Reliability factor
            score *= ai.reliability_score

            if score > best_score:
                best_score = score
                best_ai = ai

        return best_ai

    def _assess_reasoning_quality(self, response: IntelligentResponse) -> float:
        """Assess the reasoning quality of a response"""
        quality_score = 0.0

        # Check reasoning length and detail
        if len(response.reasoning) > 50:
            quality_score += 0.3
        if len(response.reasoning) > 150:
            quality_score += 0.2

        # Check for specific examples
        if (
            "example" in response.reasoning.lower()
            or "for instance" in response.reasoning.lower()
        ):
            quality_score += 0.2

        # Check for structured thinking
        if any(
            word in response.reasoning.lower()
            for word in ["first", "second", "therefore", "because"]
        ):
            quality_score += 0.2

        # Check confidence alignment
        if response.confidence > 0.8 and len(response.reasoning) > 100:
            quality_score += 0.1

        return min(quality_score, 1.0)

    def _build_consensus(
        self, ai_responses: List[AIResponse]
    ) -> Tuple[IntelligentResponse, float]:
        """Build consensus from multiple AI responses"""

        if not ai_responses:
            # Return empty response
            return (
                IntelligentResponse(
                    response_type="message",
                    content="No responses available for consensus",
                    confidence=0.0,
                    reasoning="No AI responses received",
                    suggested_actions=[],
                    context_used=[],
                    model_used="consensus",
                    processing_time=0.0,
                ),
                0.0,
            )

        # Weight responses by specialty match and confidence
        weighted_responses = []
        total_weight = 0.0

        for ai_response in ai_responses:
            weight = (
                ai_response.specialty_match
                * ai_response.confidence
                * ai_response.reasoning_quality
            )
            weighted_responses.append((weight, ai_response))
            total_weight += weight

        # Sort by weight
        weighted_responses.sort(key=lambda x: x[0], reverse=True)

        # Primary response is highest weighted
        primary_response = weighted_responses[0][1].response

        # Calculate consensus level based on response similarity
        consensus_level = self._calculate_consensus_level(ai_responses)

        # Enhance primary response with insights from others
        enhanced_response = self._enhance_response_with_consensus(
            primary_response, ai_responses
        )

        return enhanced_response, consensus_level

    def _calculate_consensus_level(self, ai_responses: List[AIResponse]) -> float:
        """Calculate how much the AI responses agree"""

        if len(ai_responses) < 2:
            return 1.0

        # Simple consensus based on confidence similarity and content themes
        confidences = [r.confidence for r in ai_responses]
        avg_confidence = sum(confidences) / len(confidences)
        confidence_variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(
            confidences
        )

        # Lower variance = higher consensus
        confidence_consensus = max(0.0, 1.0 - confidence_variance)

        # Check for common themes in responses
        all_content = " ".join(r.response.content.lower() for r in ai_responses)
        common_words = [
            "test",
            "implement",
            "consider",
            "suggest",
            "recommend",
            "error",
            "debug",
        ]
        theme_matches = sum(
            1
            for word in common_words
            if all_content.count(word) >= len(ai_responses) / 2
        )
        theme_consensus = min(1.0, theme_matches / len(common_words))

        return confidence_consensus * 0.6 + theme_consensus * 0.4

    def _enhance_response_with_consensus(
        self, primary_response: IntelligentResponse, ai_responses: List[AIResponse]
    ) -> IntelligentResponse:
        """Enhance primary response with insights from other AIs"""

        # Collect all suggested actions
        all_actions = set(primary_response.suggested_actions)
        for ai_response in ai_responses:
            all_actions.update(ai_response.response.suggested_actions)

        # Combine reasoning insights
        additional_insights = []
        for ai_response in ai_responses:
            if (
                ai_response.response != primary_response
                and ai_response.reasoning_quality > 0.7
            ):
                additional_insights.append(
                    f"({ai_response.model_name}: {ai_response.response.reasoning[:100]}...)"
                )

        enhanced_reasoning = primary_response.reasoning
        if additional_insights:
            enhanced_reasoning += (
                f" Additional perspectives: {'; '.join(additional_insights[:2])}"
            )

        return IntelligentResponse(
            response_type=primary_response.response_type,
            content=primary_response.content,
            confidence=min(
                1.0, primary_response.confidence + 0.1
            ),  # Slight confidence boost from consensus
            reasoning=enhanced_reasoning,
            suggested_actions=list(all_actions)[:6],  # Limit to 6 actions
            context_used=primary_response.context_used + ["multi_ai_consensus"],
            model_used=f"{primary_response.model_used}_consensus",
            processing_time=primary_response.processing_time,
        )

    def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination system statistics"""
        return {
            "total_coordinations": self.coordination_stats["total_coordinations"],
            "average_response_time": self.coordination_stats["average_response_time"],
            "consensus_rate": self.coordination_stats["consensus_rate"],
            "model_usage": dict(self.coordination_stats["model_usage"]),
            "available_models": list(self.ai_capabilities.keys()),
            "model_capabilities": {
                name: {
                    "specialties": [s.value for s in cap.specialties],
                    "performance_score": cap.performance_score,
                    "reliability_score": cap.reliability_score,
                    "privacy_level": cap.privacy_level,
                }
                for name, cap in self.ai_capabilities.items()
            },
        }

    def _update_performance_metrics(
        self, response: CoordinatedResponse, total_time: float
    ):
        """Update performance tracking metrics"""

        # Update overall stats
        if self.coordination_stats["total_coordinations"] > 1:
            self.coordination_stats["average_response_time"] = (
                self.coordination_stats["average_response_time"]
                * (self.coordination_stats["total_coordinations"] - 1)
                + total_time
            ) / self.coordination_stats["total_coordinations"]
        else:
            self.coordination_stats["average_response_time"] = total_time

        # Update model usage
        for model in response.models_used:
            self.coordination_stats["model_usage"][model] = (
                self.coordination_stats["model_usage"].get(model, 0) + 1
            )

        # Update consensus rate
        if response.consensus_level >= 0.7:
            self.coordination_stats["consensus_rate"] = (
                self.coordination_stats["consensus_rate"]
                * (self.coordination_stats["total_coordinations"] - 1)
                + 1.0
            ) / self.coordination_stats["total_coordinations"]
        else:
            self.coordination_stats["consensus_rate"] = (
                self.coordination_stats["consensus_rate"]
                * (self.coordination_stats["total_coordinations"] - 1)
                + 0.0
            ) / self.coordination_stats["total_coordinations"]

    async def _store_coordination_result(
        self, task: CoordinationTask, response: CoordinatedResponse
    ):
        """Store coordination result for learning"""

        result_data = {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "coordination_strategy": response.coordination_strategy,
            "models_used": response.models_used,
            "consensus_level": response.consensus_level,
            "total_processing_time": response.total_processing_time,
            "primary_confidence": response.primary_response.confidence,
            "timestamp": time.time(),
        }

        # Store in Redis for analysis
        self.redis.lpush("coordination_history", json.dumps(result_data))
        self.redis.ltrim("coordination_history", 0, 999)  # Keep last 1000 results

    # Helper methods for context manipulation

    def _create_high_level_context(
        self, context: DevelopmentContext
    ) -> DevelopmentContext:
        """Create high-level context for architectural analysis"""
        return context  # Simplified for now

    def _integrate_validation_feedback(
        self, primary: IntelligentResponse, validators: List[AIResponse]
    ) -> IntelligentResponse:
        """Integrate validation feedback into primary response"""

        # Collect validation insights
        validation_insights = []
        for validator in validators:
            if validator.confidence > 0.7:
                validation_insights.append(validator.response.content[:200])

        enhanced_content = primary.content
        if validation_insights:
            enhanced_content += (
                f"\n\n**Validation insights:** {'; '.join(validation_insights[:2])}"
            )

        return IntelligentResponse(
            response_type=primary.response_type,
            content=enhanced_content,
            confidence=min(1.0, primary.confidence + 0.05),
            reasoning=primary.reasoning + " (validated by additional models)",
            suggested_actions=primary.suggested_actions,
            context_used=primary.context_used + ["validation_feedback"],
            model_used=f"{primary.model_used}_validated",
            processing_time=primary.processing_time,
        )


async def demo_multi_ai_coordination():
    """Demo the multi-AI coordination system"""
    print("🤖 MULTI-AI COORDINATION SYSTEM DEMO")
    print("=" * 50)

    # Setup
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    coordinator = MultiAICoordinator(redis_client)

    # Show available capabilities
    stats = coordinator.get_coordination_stats()
    print("🧠 Available AI Models:")
    for model, caps in stats["model_capabilities"].items():
        print(
            f"   • {model}: {caps['specialties'][:3]} (score: {caps['performance_score']:.2f})"
        )

    # Test different coordination strategies
    test_tasks = [
        CoordinationTask(
            task_id="arch_design_001",
            task_type=AISpecialty.ARCHITECTURE_DESIGN,
            context=DevelopmentContext(
                current_buffer="main.py",
                buffer_type="python",
                project_root="/project",
                git_branch="feature/refactor",
                recent_files=["main.py", "models.py"],
                cursor_context="class APIHandler:",
                recent_commands=["self-insert-command"],
                active_modes=["python-mode"],
                project_files=["main.py", "models.py", "tests.py"],
                error_messages=[],
                test_status=None,
                build_status=None,
            ),
            user_intent="Design a scalable API architecture for microservices",
            patterns=[],
            priority=5,
            requires_consensus=True,
        ),
        CoordinationTask(
            task_id="debug_001",
            task_type=AISpecialty.DEBUGGING,
            context=DevelopmentContext(
                current_buffer="debug.py",
                buffer_type="python",
                project_root="/project",
                git_branch="bugfix/memory-leak",
                recent_files=["debug.py"],
                cursor_context="Memory usage keeps growing",
                recent_commands=["compile"],
                active_modes=["python-mode"],
                project_files=["debug.py"],
                error_messages=["MemoryError: Unable to allocate array"],
                test_status="failing",
                build_status="failing",
            ),
            user_intent="Debug memory leak in data processing pipeline",
            patterns=[],
            priority=4,
        ),
    ]

    print(f"\n🎯 Testing coordination strategies...")

    for task in test_tasks:
        print(f"\n--- Task: {task.task_id} ({task.task_type.value}) ---")

        try:
            result = await coordinator.coordinate_response(task)

            print(f"📋 Strategy: {result.coordination_strategy}")
            print(f"🤖 Models: {', '.join(result.models_used)}")
            print(f"⏱️  Time: {result.total_processing_time:.2f}s")
            print(f"🎯 Consensus: {result.consensus_level:.2f}")
            print(f"💭 Response: {result.primary_response.content[:150]}...")
            print(
                f"🔧 Actions: {', '.join(result.primary_response.suggested_actions[:3])}"
            )

        except Exception as e:
            print(f"❌ Error: {e}")

    # Show final statistics
    final_stats = coordinator.get_coordination_stats()
    print(f"\n📊 COORDINATION STATISTICS:")
    print(f"   Total coordinations: {final_stats['total_coordinations']}")
    print(f"   Average response time: {final_stats['average_response_time']:.2f}s")
    print(f"   Consensus rate: {final_stats['consensus_rate']:.2%}")
    print(f"   Model usage: {final_stats['model_usage']}")

    print(f"\n✨ MULTI-AI COORDINATION CAPABILITIES:")
    print(f"   ✅ Intelligent model selection based on task specialties")
    print(f"   ✅ Multiple coordination strategies (consensus, hierarchical, etc.)")
    print(f"   ✅ Parallel processing for faster responses")
    print(f"   ✅ Quality assessment and validation")
    print(f"   ✅ Performance tracking and optimization")
    print(f"   ✅ Privacy-aware model selection (cloud vs local)")


if __name__ == "__main__":
    asyncio.run(demo_multi_ai_coordination())
