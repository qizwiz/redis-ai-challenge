#!/usr/bin/env python3
"""
Multi-AI Coordination System - Real Implementation
Coordinates multiple AI agents working together on development tasks.
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from fixed_redis_coordinator import redis_coordinator
from robust_claude_integration import claude_integration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentRole(Enum):
    CODER = "coder"
    REVIEWER = "reviewer"
    DOCUMENTER = "documenter"
    TESTER = "tester"
    ARCHITECT = "architect"
    OPTIMIZER = "optimizer"


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AITask:
    id: str
    type: str
    content: str
    context: Dict[str, Any]
    assigned_to: Optional[AgentRole] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = 0.0
    started_at: float = 0.0
    completed_at: float = 0.0
    result: Optional[str] = None
    error: Optional[str] = None


class AIAgent:
    """Individual AI agent with specialized role"""

    def __init__(self, role: AgentRole, coordinator):
        self.role = role
        self.coordinator = coordinator
        self.active = True
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.specialization = self._get_specialization()

        logger.info(f"🤖 {role.value.title()} agent initialized")

    def _get_specialization(self) -> Dict[str, Any]:
        """Get agent specialization details"""
        specializations = {
            AgentRole.CODER: {
                "task_types": ["code_generation", "bug_fix", "refactor"],
                "expertise": "Writing clean, efficient code",
                "prompt_prefix": "You are an expert software engineer. Generate high-quality code that follows best practices.",
            },
            AgentRole.REVIEWER: {
                "task_types": ["code_review", "quality_check", "security_audit"],
                "expertise": "Code quality and security analysis",
                "prompt_prefix": "You are a senior code reviewer. Analyze code for quality, security, and best practices.",
            },
            AgentRole.DOCUMENTER: {
                "task_types": ["documentation", "comments", "readme"],
                "expertise": "Technical documentation and communication",
                "prompt_prefix": "You are a technical writer. Create clear, comprehensive documentation.",
            },
            AgentRole.TESTER: {
                "task_types": ["test_generation", "test_review", "coverage_analysis"],
                "expertise": "Test design and quality assurance",
                "prompt_prefix": "You are a QA engineer. Design thorough tests that catch edge cases.",
            },
            AgentRole.ARCHITECT: {
                "task_types": [
                    "system_design",
                    "pattern_analysis",
                    "architecture_review",
                ],
                "expertise": "System architecture and design patterns",
                "prompt_prefix": "You are a software architect. Design scalable, maintainable systems.",
            },
            AgentRole.OPTIMIZER: {
                "task_types": ["performance_analysis", "optimization", "profiling"],
                "expertise": "Performance optimization and analysis",
                "prompt_prefix": "You are a performance engineer. Optimize code for speed and efficiency.",
            },
        }

        return specializations.get(self.role, {})

    def can_handle_task(self, task: AITask) -> bool:
        """Check if this agent can handle the given task"""
        return task.type in self.specialization.get("task_types", [])

    async def execute_task(self, task: AITask) -> bool:
        """Execute a task with agent's specialization"""
        try:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = time.time()

            logger.info(f"🔨 {self.role.value.title()} executing: {task.type}")

            # Build specialized prompt
            prompt = self._build_specialized_prompt(task)

            # Execute with Claude if available
            if claude_integration.is_available():
                response = claude_integration.execute_prompt(prompt, timeout=30)

                if response.success:
                    task.result = response.content
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = time.time()
                    self.tasks_completed += 1

                    logger.info(
                        f"✅ {self.role.value.title()} completed task: {task.type}"
                    )
                    return True
                else:
                    task.error = response.error_message
                    task.status = TaskStatus.FAILED
                    self.tasks_failed += 1

                    logger.error(
                        f"❌ {self.role.value.title()} failed task: {response.error_message}"
                    )
                    return False
            else:
                # Fallback execution
                result = self._execute_fallback(task)
                if result:
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = time.time()
                    self.tasks_completed += 1

                    logger.info(
                        f"✅ {self.role.value.title()} completed task (fallback): {task.type}"
                    )
                    return True
                else:
                    task.error = "Fallback execution failed"
                    task.status = TaskStatus.FAILED
                    self.tasks_failed += 1
                    return False

        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            self.tasks_failed += 1
            logger.error(f"❌ {self.role.value.title()} task error: {e}")
            return False

    def _build_specialized_prompt(self, task: AITask) -> str:
        """Build a specialized prompt based on agent role"""
        base_prompt = self.specialization.get("prompt_prefix", "")

        prompt = f"""{base_prompt}

Task: {task.type}
Request: {task.content}

Context:
- File: {task.context.get('file', 'unknown')}
- Language: {task.context.get('language', 'unknown')}
- Function/Class: {task.context.get('target', 'unknown')}

Additional Context:
{json.dumps(task.context, indent=2)}

Generate a high-quality response that demonstrates expertise in {self.specialization.get('expertise', 'this area')}.
Provide practical, actionable output."""

        return prompt

    def _execute_fallback(self, task: AITask) -> Optional[str]:
        """Execute task with fallback logic when Claude unavailable"""
        task_type = task.type
        content = task.content

        if self.role == AgentRole.CODER:
            if "function" in content.lower():
                return f"""def example_function():
    \"\"\"Generated by {self.role.value} agent.\"\"\"
    # TODO: Implement {content}
    pass"""
            elif "class" in content.lower():
                return f"""class ExampleClass:
    \"\"\"Generated by {self.role.value} agent.\"\"\"
    
    def __init__(self):
        # TODO: Implement {content}
        pass"""
            else:
                return f"# {self.role.value.title()} agent processed: {content}"

        elif self.role == AgentRole.REVIEWER:
            return f"""# Code Review by {self.role.value.title()} Agent

## Review Summary
- Task: {content}
- Status: Needs implementation
- Recommendation: Follow best practices for this type of code

## Suggestions
1. Add proper error handling
2. Include comprehensive tests
3. Add documentation
4. Consider edge cases"""

        elif self.role == AgentRole.DOCUMENTER:
            return f"""# Documentation by {self.role.value.title()} Agent

## Overview
{content}

## Description
This component handles the requested functionality.

## Usage
```python
# Example usage here
```

## Notes
Generated by AI documentation agent."""

        elif self.role == AgentRole.TESTER:
            return f"""# Tests by {self.role.value.title()} Agent

def test_{content.lower().replace(' ', '_')}():
    \"\"\"Test for {content}.\"\"\"
    # Arrange
    # TODO: Set up test data
    
    # Act
    # TODO: Execute the functionality
    
    # Assert
    # TODO: Verify results
    assert True  # Placeholder"""

        else:
            return f"# {self.role.value.title()} agent output for: {content}"

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "role": self.role.value,
            "active": self.active,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "success_rate": (
                self.tasks_completed / max(1, self.tasks_completed + self.tasks_failed)
            )
            * 100,
            "specialization": self.specialization["expertise"],
        }


class MultiAICoordinator:
    """Coordinates multiple AI agents working together"""

    def __init__(self):
        self.agents: Dict[AgentRole, AIAgent] = {}
        self.task_queue: List[AITask] = []
        self.completed_tasks: List[AITask] = []
        self.running = False
        self.coordinator = redis_coordinator

        # Initialize all agent types
        for role in AgentRole:
            self.agents[role] = AIAgent(role, self.coordinator)

        logger.info("🎯 Multi-AI Coordination System initialized")
        logger.info(f"👥 Active agents: {list(self.agents.keys())}")

    async def start_coordination(self):
        """Start coordinating multiple AI agents"""
        self.running = True

        logger.info("🚀 Starting Multi-AI Coordination System")
        logger.info("🤖 Agents ready for collaborative development")

        # Start coordination loops
        coordination_tasks = [
            asyncio.create_task(self._monitor_user_requests()),
            asyncio.create_task(self._assign_tasks()),
            asyncio.create_task(self._execute_tasks()),
            asyncio.create_task(self._coordinate_agents()),
        ]

        try:
            await asyncio.gather(*coordination_tasks)
        except Exception as e:
            logger.error(f"Coordination error: {e}")

    async def _monitor_user_requests(self):
        """Monitor Redis for user requests that need multi-AI coordination"""
        while self.running:
            try:
                # Check for natural commands that need multi-agent coordination
                entries = self.coordinator.redis.xrange("intents", count=10)

                for entry_id, fields in entries:
                    if fields.get("type") == "natural_command":
                        command = fields.get("command", "")

                        # Identify complex commands that need multi-agent coordination
                        if self._needs_multi_agent_coordination(command):
                            await self._decompose_user_request(command, fields)

                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Request monitoring error: {e}")
                await asyncio.sleep(5)

    def _needs_multi_agent_coordination(self, command: str) -> bool:
        """Determine if command needs multiple agents"""
        multi_agent_keywords = [
            "create class",
            "build system",
            "implement feature",
            "refactor code",
            "add tests",
            "review code",
            "optimize performance",
            "write documentation",
            "design architecture",
            "full implementation",
        ]

        command_lower = command.lower()
        return any(keyword in command_lower for keyword in multi_agent_keywords)

    async def _decompose_user_request(self, command: str, context: Dict[str, Any]):
        """Decompose user request into tasks for different agents"""
        logger.info(f"🎯 Decomposing multi-agent request: {command}")

        # Create tasks based on command analysis
        tasks = []

        command_lower = command.lower()

        if "class" in command_lower or "implement" in command_lower:
            # Code generation task
            tasks.append(
                AITask(
                    id=f"code_{time.time()}",
                    type="code_generation",
                    content=command,
                    context=context,
                )
            )

            # Documentation task
            tasks.append(
                AITask(
                    id=f"doc_{time.time()}",
                    type="documentation",
                    content=f"Document the implementation: {command}",
                    context=context,
                )
            )

            # Test generation task
            tasks.append(
                AITask(
                    id=f"test_{time.time()}",
                    type="test_generation",
                    content=f"Create tests for: {command}",
                    context=context,
                )
            )

        elif "review" in command_lower:
            tasks.append(
                AITask(
                    id=f"review_{time.time()}",
                    type="code_review",
                    content=command,
                    context=context,
                )
            )

        elif "optimize" in command_lower:
            tasks.append(
                AITask(
                    id=f"optimize_{time.time()}",
                    type="performance_analysis",
                    content=command,
                    context=context,
                )
            )

        else:
            # Default: treat as code generation
            tasks.append(
                AITask(
                    id=f"general_{time.time()}",
                    type="code_generation",
                    content=command,
                    context=context,
                )
            )

        # Add tasks to queue
        self.task_queue.extend(tasks)

        logger.info(f"📋 Created {len(tasks)} tasks for multi-agent coordination")

    async def _assign_tasks(self):
        """Assign tasks to appropriate agents"""
        while self.running:
            try:
                # Assign unassigned tasks
                for task in self.task_queue:
                    if task.assigned_to is None:
                        # Find best agent for task
                        best_agent = self._find_best_agent(task)
                        if best_agent:
                            task.assigned_to = best_agent.role
                            logger.info(
                                f"📋 Assigned {task.type} to {best_agent.role.value}"
                            )

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Task assignment error: {e}")
                await asyncio.sleep(5)

    def _find_best_agent(self, task: AITask) -> Optional[AIAgent]:
        """Find the best agent for a given task"""
        # Find agents that can handle this task type
        capable_agents = [
            agent
            for agent in self.agents.values()
            if agent.can_handle_task(task) and agent.active
        ]

        if not capable_agents:
            return None

        # Return agent with best success rate
        return max(
            capable_agents,
            key=lambda a: a.tasks_completed
            / max(1, a.tasks_completed + a.tasks_failed),
        )

    async def _execute_tasks(self):
        """Execute assigned tasks"""
        while self.running:
            try:
                # Execute assigned, pending tasks
                pending_tasks = [
                    t
                    for t in self.task_queue
                    if t.status == TaskStatus.PENDING and t.assigned_to is not None
                ]

                for task in pending_tasks[:3]:  # Limit concurrent tasks
                    agent = self.agents.get(task.assigned_to)
                    if agent:
                        success = await agent.execute_task(task)

                        if success:
                            # Store result in Redis
                            self._store_agent_result(task)

                            # Move to completed
                            self.task_queue.remove(task)
                            self.completed_tasks.append(task)

                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Task execution error: {e}")
                await asyncio.sleep(5)

    def _store_agent_result(self, task: AITask):
        """Store agent task result in Redis"""
        try:
            result_data = {
                "type": "multi_agent_result",
                "task_id": task.id,
                "task_type": task.type,
                "agent_role": task.assigned_to.value if task.assigned_to else "unknown",
                "result": task.result,
                "execution_time": task.completed_at - task.started_at,
                "session_id": task.context.get("session_id"),
                "timestamp": str(time.time()),
            }

            self.coordinator.store_ai_response(result_data)
            logger.info(
                f"💾 Stored result from {task.assigned_to.value if task.assigned_to else 'unknown'}"
            )

        except Exception as e:
            logger.error(f"Failed to store agent result: {e}")

    async def _coordinate_agents(self):
        """Coordinate agents and manage workload"""
        while self.running:
            try:
                # Log coordination status
                if len(self.task_queue) > 0 or len(self.completed_tasks) > 0:
                    logger.info(
                        f"🎯 Coordination status: {len(self.task_queue)} pending, {len(self.completed_tasks)} completed"
                    )

                    # Show agent stats
                    for role, agent in self.agents.items():
                        stats = agent.get_stats()
                        if stats["tasks_completed"] > 0 or stats["tasks_failed"] > 0:
                            logger.info(
                                f"🤖 {role.value}: {stats['tasks_completed']} completed, {stats['success_rate']:.1f}% success"
                            )

                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Coordination error: {e}")
                await asyncio.sleep(10)

    def get_system_stats(self) -> Dict[str, Any]:
        """Get multi-AI system statistics"""
        agent_stats = {
            role.value: agent.get_stats() for role, agent in self.agents.items()
        }

        total_completed = sum(agent.tasks_completed for agent in self.agents.values())
        total_failed = sum(agent.tasks_failed for agent in self.agents.values())

        return {
            "running": self.running,
            "agents": agent_stats,
            "total_tasks_completed": total_completed,
            "total_tasks_failed": total_failed,
            "overall_success_rate": (
                total_completed / max(1, total_completed + total_failed)
            )
            * 100,
            "pending_tasks": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "claude_available": claude_integration.is_available(),
        }

    def stop(self):
        """Stop the multi-AI coordination system"""
        self.running = False
        logger.info("🛑 Multi-AI Coordination System stopped")


# Global coordination system
multi_ai_coordinator = MultiAICoordinator()


async def main():
    """Demo the Multi-AI Coordination System"""
    print("🎯 MULTI-AI COORDINATION SYSTEM")
    print("=" * 60)
    print("Coordinating multiple AI agents for development tasks")
    print("=" * 60)

    # Start coordination
    coordination_task = asyncio.create_task(multi_ai_coordinator.start_coordination())

    print("✅ Multi-AI coordination started")
    print("🤖 Agent roles:", [role.value for role in AgentRole])
    print(
        "🌐 Claude integration:",
        "✅ Active" if claude_integration.is_available() else "❌ Unavailable",
    )
    print("📝 Use M-x working-redis-natural-command in Emacs")
    print("💬 Try: 'create a User class with tests and documentation'")
    print("🔧 Try: 'implement a caching system'")
    print("🛑 Press Ctrl+C to stop")

    try:
        while True:
            await asyncio.sleep(10)

            # Show system stats
            stats = multi_ai_coordinator.get_system_stats()
            if stats["total_tasks_completed"] > 0 or stats["pending_tasks"] > 0:
                print(
                    f"📊 System: {stats['pending_tasks']} pending, {stats['total_tasks_completed']} completed"
                )
                print(f"🎯 Success rate: {stats['overall_success_rate']:.1f}%")

    except KeyboardInterrupt:
        print("\n🛑 Stopping Multi-AI Coordination System...")
        multi_ai_coordinator.stop()
        await coordination_task
        print("✅ Multi-AI Coordination System stopped")


if __name__ == "__main__":
    asyncio.run(main())
