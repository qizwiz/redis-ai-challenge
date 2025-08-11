#!/usr/bin/env python3
"""
Autonomous AI Agents - The Revolutionary AI Workforce

This creates truly autonomous AI agents that work independently,
implementing "mechanical selfishness" - maximizing output while you walk away.

These agents embody the vision: "build the system that you'd build to act as you"
"""

import asyncio
import json
import time
import logging
import redis
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from robust_claude_integration import claude_integration

logger = logging.getLogger(__name__)


class AgentType(Enum):
    CODER = "coder"
    REVIEWER = "reviewer"
    DOCUMENTER = "documenter"
    TESTER = "tester"
    ARCHITECT = "architect"
    OPTIMIZER = "optimizer"


@dataclass
class Task:
    """A task for autonomous agents"""

    id: str
    type: str
    description: str
    context: Dict[str, Any]
    priority: int
    assigned_agent: Optional[str] = None
    status: str = "pending"
    created_at: float = None
    completed_at: Optional[float] = None
    result: Optional[str] = None


class AutonomousAgent:
    """Base class for autonomous AI agents"""

    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        redis_host="localhost",
        redis_port=6379,
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )
        self.running = False
        self.tasks_completed = 0
        self.start_time = None

        # Agent-specific configuration
        self.task_queue = f"agent:{agent_id}:tasks"
        self.status_key = f"agent:{agent_id}:status"
        self.results_key = f"agent:{agent_id}:results"

        logger.info(f"🤖 Autonomous Agent {agent_id} ({agent_type.value}) initialized")

    async def start_autonomous_work(self):
        """Start autonomous work loop - the agent works independently"""
        self.running = True
        self.start_time = time.time()

        # Register agent as active
        await self._register_agent()

        logger.info(f"🚀 Agent {self.agent_id} starting autonomous work")

        while self.running:
            try:
                # Look for work in the task queue
                task = await self._get_next_task()

                if task:
                    # Execute task autonomously
                    result = await self._execute_task_autonomously(task)
                    await self._report_completion(task, result)
                    self.tasks_completed += 1
                else:
                    # No tasks available, do autonomous discovery
                    await self._autonomous_discovery()

                # Brief pause to prevent tight loop
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Agent {self.agent_id} error: {e}")
                await asyncio.sleep(5)

    async def _register_agent(self):
        """Register agent as active in the system"""
        agent_data = {
            "agent_id": self.agent_id,
            "type": self.agent_type.value,
            "status": "active",
            "start_time": self.start_time,
            "tasks_completed": 0,
            "last_heartbeat": time.time(),
        }

        # Store in Redis hash
        for key, value in agent_data.items():
            self.redis.hset(self.status_key, key, str(value))

        # Add to active agents set
        self.redis.sadd("autonomous:active_agents", self.agent_id)

        logger.info(f"📝 Agent {self.agent_id} registered as active")

    async def _get_next_task(self) -> Optional[Task]:
        """Get next task from queue"""
        # Check agent-specific queue first
        task_data = self.redis.lpop(self.task_queue)

        if not task_data:
            # Check global task queue for this agent type
            global_queue = f"tasks:{self.agent_type.value}"
            task_data = self.redis.lpop(global_queue)

        if task_data:
            try:
                task_dict = json.loads(task_data)
                return Task(**task_dict)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse task data: {task_data}")

        return None

    async def _execute_task_autonomously(self, task: Task) -> Dict[str, Any]:
        """Execute task autonomously using AI"""
        logger.info(f"🎯 Agent {self.agent_id} executing task: {task.description}")

        # Update task status
        task.status = "in_progress"
        task.assigned_agent = self.agent_id

        # Store task status
        self.redis.hset(f"task:{task.id}", "status", "in_progress")
        self.redis.hset(f"task:{task.id}", "assigned_agent", self.agent_id)

        # Execute based on agent type
        if self.agent_type == AgentType.CODER:
            result = await self._execute_coding_task(task)
        elif self.agent_type == AgentType.REVIEWER:
            result = await self._execute_review_task(task)
        elif self.agent_type == AgentType.DOCUMENTER:
            result = await self._execute_documentation_task(task)
        elif self.agent_type == AgentType.TESTER:
            result = await self._execute_testing_task(task)
        elif self.agent_type == AgentType.ARCHITECT:
            result = await self._execute_architecture_task(task)
        else:
            result = await self._execute_generic_task(task)

        return result

    async def _execute_coding_task(self, task: Task) -> Dict[str, Any]:
        """Execute coding task using Claude AI"""
        if not claude_integration.is_available():
            return {"status": "error", "message": "Claude not available"}

        # Create coding prompt
        prompt = f"""You are an autonomous coding agent. 

Task: {task.description}

Context: {json.dumps(task.context, indent=2)}

Generate the requested code. Respond with:
1. The complete code solution
2. Brief explanation of approach
3. Any assumptions made

Focus on clean, production-ready code."""

        response = claude_integration.execute_prompt(prompt, timeout=30)

        if response.success:
            # Store generated code
            code_key = f"generated_code:{task.id}"
            self.redis.hset(
                code_key,
                {
                    "task_id": task.id,
                    "agent_id": self.agent_id,
                    "code": response.content,
                    "timestamp": time.time(),
                },
            )

            return {
                "status": "completed",
                "output": response.content,
                "code_stored": code_key,
                "execution_time": response.execution_time,
            }
        else:
            return {"status": "error", "message": response.error_message}

    async def _execute_review_task(self, task: Task) -> Dict[str, Any]:
        """Execute code review task"""
        if not claude_integration.is_available():
            return {"status": "error", "message": "Claude not available"}

        code_to_review = task.context.get("code", "")

        prompt = f"""You are an autonomous code review agent.

Review this code for:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance optimizations
4. Security concerns

Code to review:
{code_to_review}

Provide a structured review with specific suggestions."""

        response = claude_integration.execute_prompt(prompt, timeout=20)

        if response.success:
            return {
                "status": "completed",
                "review": response.content,
                "execution_time": response.execution_time,
            }
        else:
            return {"status": "error", "message": response.error_message}

    async def _execute_documentation_task(self, task: Task) -> Dict[str, Any]:
        """Execute documentation task"""
        if not claude_integration.is_available():
            return {"status": "error", "message": "Claude not available"}

        code_to_document = task.context.get("code", "")

        prompt = f"""You are an autonomous documentation agent.

Generate comprehensive documentation for this code:
{code_to_document}

Include:
1. Clear description of functionality
2. Parameter explanations
3. Return value description
4. Usage examples
5. Any important notes

Format as proper docstring/comments for the language."""

        response = claude_integration.execute_prompt(prompt, timeout=20)

        if response.success:
            return {
                "status": "completed",
                "documentation": response.content,
                "execution_time": response.execution_time,
            }
        else:
            return {"status": "error", "message": response.error_message}

    async def _execute_testing_task(self, task: Task) -> Dict[str, Any]:
        """Execute testing task"""
        if not claude_integration.is_available():
            return {"status": "error", "message": "Claude not available"}

        code_to_test = task.context.get("code", "")

        prompt = f"""You are an autonomous testing agent.

Generate comprehensive tests for this code:
{code_to_test}

Include:
1. Unit tests for all functions
2. Edge case testing
3. Error condition testing
4. Integration tests if applicable

Use appropriate testing framework for the language."""

        response = claude_integration.execute_prompt(prompt, timeout=25)

        if response.success:
            return {
                "status": "completed",
                "tests": response.content,
                "execution_time": response.execution_time,
            }
        else:
            return {"status": "error", "message": response.error_message}

    async def _execute_architecture_task(self, task: Task) -> Dict[str, Any]:
        """Execute architecture design task"""
        if not claude_integration.is_available():
            return {"status": "error", "message": "Claude not available"}

        requirements = task.context.get("requirements", "")

        prompt = f"""You are an autonomous architecture agent.

Design system architecture for these requirements:
{requirements}

Provide:
1. High-level system design
2. Component breakdown
3. Data flow diagrams
4. Technology recommendations
5. Scalability considerations

Focus on practical, implementable architecture."""

        response = claude_integration.execute_prompt(prompt, timeout=30)

        if response.success:
            return {
                "status": "completed",
                "architecture": response.content,
                "execution_time": response.execution_time,
            }
        else:
            return {"status": "error", "message": response.error_message}

    async def _execute_generic_task(self, task: Task) -> Dict[str, Any]:
        """Execute generic task"""
        return {
            "status": "completed",
            "message": f"Generic task completed by {self.agent_id}",
            "description": task.description,
        }

    async def _autonomous_discovery(self):
        """Autonomous discovery of work when no tasks are queued"""
        # Update heartbeat
        self.redis.hset(self.status_key, "last_heartbeat", time.time())

        # Look for opportunities based on agent type
        if self.agent_type == AgentType.CODER:
            await self._discover_coding_opportunities()
        elif self.agent_type == AgentType.REVIEWER:
            await self._discover_review_opportunities()
        elif self.agent_type == AgentType.DOCUMENTER:
            await self._discover_documentation_opportunities()

        # Brief pause for discovery cycle
        await asyncio.sleep(5)

    async def _discover_coding_opportunities(self):
        """Discover coding opportunities autonomously"""
        # Look for incomplete code in Redis
        incomplete_code_keys = self.redis.keys("incomplete_code:*")

        if incomplete_code_keys:
            # Create tasks for incomplete code
            for key in incomplete_code_keys[:3]:  # Process up to 3
                task_id = f"auto_task_{int(time.time())}"
                code_data = self.redis.hgetall(key)

                task = Task(
                    id=task_id,
                    type="auto_coding",
                    description=f"Complete implementation: {code_data.get('description', 'Unknown')}",
                    context={"incomplete_code": code_data},
                    priority=3,
                    created_at=time.time(),
                )

                # Add to our task queue
                self.redis.rpush(self.task_queue, json.dumps(task.__dict__))
                logger.info(
                    f"🔍 Agent {self.agent_id} discovered coding opportunity: {task.description}"
                )

    async def _discover_review_opportunities(self):
        """Discover code review opportunities"""
        # Look for recently generated code that needs review
        recent_code_keys = self.redis.keys("generated_code:*")

        for key in recent_code_keys[:2]:  # Review up to 2
            code_data = self.redis.hgetall(key)
            timestamp = float(code_data.get("timestamp", 0))

            # Only review code from last hour that hasn't been reviewed
            if time.time() - timestamp < 3600:
                review_key = f"reviewed:{key}"
                if not self.redis.exists(review_key):
                    task_id = f"auto_review_{int(time.time())}"

                    task = Task(
                        id=task_id,
                        type="auto_review",
                        description=f"Review generated code from task {code_data.get('task_id')}",
                        context={"code": code_data.get("code", "")},
                        priority=2,
                        created_at=time.time(),
                    )

                    self.redis.rpush(self.task_queue, json.dumps(task.__dict__))
                    logger.info(
                        f"🔍 Agent {self.agent_id} discovered review opportunity"
                    )

    async def _discover_documentation_opportunities(self):
        """Discover documentation opportunities"""
        # Look for code without documentation
        code_keys = self.redis.keys("generated_code:*")

        for key in code_keys[:2]:
            doc_key = f"documented:{key}"
            if not self.redis.exists(doc_key):
                code_data = self.redis.hgetall(key)
                task_id = f"auto_doc_{int(time.time())}"

                task = Task(
                    id=task_id,
                    type="auto_documentation",
                    description=f"Document code from task {code_data.get('task_id')}",
                    context={"code": code_data.get("code", "")},
                    priority=1,
                    created_at=time.time(),
                )

                self.redis.rpush(self.task_queue, json.dumps(task.__dict__))
                logger.info(
                    f"🔍 Agent {self.agent_id} discovered documentation opportunity"
                )

    async def _report_completion(self, task: Task, result: Dict[str, Any]):
        """Report task completion"""
        completion_data = {
            "task_id": task.id,
            "agent_id": self.agent_id,
            "status": result.get("status", "completed"),
            "result": json.dumps(result),
            "completed_at": time.time(),
        }

        # Store completion
        self.redis.hset(f"task:{task.id}:completion", completion_data)

        # Update agent stats
        self.redis.hset(self.status_key, "tasks_completed", self.tasks_completed)

        # Add to results stream
        self.redis.xadd("autonomous:completions", completion_data)

        logger.info(f"✅ Agent {self.agent_id} completed task {task.id}")

    def stop(self):
        """Stop autonomous work"""
        self.running = False

        # Update status
        self.redis.hset(self.status_key, "status", "stopped")
        self.redis.srem("autonomous:active_agents", self.agent_id)

        runtime = time.time() - self.start_time if self.start_time else 0
        logger.info(
            f"🛑 Agent {self.agent_id} stopped after {runtime:.1f}s, {self.tasks_completed} tasks completed"
        )


class AutonomousWorkforce:
    """Manages a workforce of autonomous AI agents"""

    def __init__(self, redis_host="localhost", redis_port=6379):
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )
        self.agents = {}
        self.running = False

    async def deploy_workforce(self, workforce_config: Dict[AgentType, int]):
        """Deploy autonomous workforce"""
        print("🚀 Deploying Autonomous AI Workforce")
        print("=" * 50)

        agent_tasks = []

        for agent_type, count in workforce_config.items():
            print(f"   Deploying {count} {agent_type.value} agent(s)")

            for i in range(count):
                agent_id = f"{agent_type.value}_{i+1}"
                agent = AutonomousAgent(agent_id, agent_type)
                self.agents[agent_id] = agent

                # Start agent in background
                task = asyncio.create_task(agent.start_autonomous_work())
                agent_tasks.append(task)

        print(f"✅ Deployed {len(self.agents)} autonomous agents")
        self.running = True

        # Start workforce monitoring
        monitor_task = asyncio.create_task(self._monitor_workforce())

        return agent_tasks + [monitor_task]

    async def _monitor_workforce(self):
        """Monitor autonomous workforce"""
        while self.running:
            try:
                # Update workforce statistics
                total_tasks = sum(
                    agent.tasks_completed for agent in self.agents.values()
                )
                active_agents = len([a for a in self.agents.values() if a.running])

                workforce_stats = {
                    "total_agents": len(self.agents),
                    "active_agents": active_agents,
                    "total_tasks_completed": total_tasks,
                    "last_update": time.time(),
                }

                self.redis.hset("autonomous:workforce:stats", workforce_stats)

                # Brief pause
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Workforce monitoring error: {e}")
                await asyncio.sleep(30)

    def assign_task(self, agent_type: AgentType, task: Task):
        """Assign task to specific agent type"""
        task_queue = f"tasks:{agent_type.value}"
        self.redis.rpush(task_queue, json.dumps(task.__dict__))
        logger.info(
            f"📋 Assigned task to {agent_type.value} agents: {task.description}"
        )

    def get_workforce_status(self) -> Dict[str, Any]:
        """Get current workforce status"""
        status = {
            "total_agents": len(self.agents),
            "active_agents": len([a for a in self.agents.values() if a.running]),
            "agent_details": {},
        }

        for agent_id, agent in self.agents.items():
            status["agent_details"][agent_id] = {
                "type": agent.agent_type.value,
                "running": agent.running,
                "tasks_completed": agent.tasks_completed,
                "runtime": time.time() - agent.start_time if agent.start_time else 0,
            }

        return status

    async def stop_workforce(self):
        """Stop all autonomous agents"""
        print("🛑 Stopping Autonomous Workforce")

        for agent in self.agents.values():
            agent.stop()

        self.running = False
        print("✅ All agents stopped")


# Global workforce manager
autonomous_workforce = AutonomousWorkforce()


async def main():
    """Demonstrate autonomous AI workforce"""
    print("🤖 AUTONOMOUS AI WORKFORCE DEMONSTRATION")
    print("=" * 60)
    print("Deploying agents that work independently while you walk away")
    print("=" * 60)

    # Define workforce configuration
    workforce_config = {
        AgentType.CODER: 2,
        AgentType.REVIEWER: 1,
        AgentType.DOCUMENTER: 1,
    }

    # Deploy workforce
    agent_tasks = await autonomous_workforce.deploy_workforce(workforce_config)

    # Create some test tasks
    test_tasks = [
        Task(
            id="task_1",
            type="coding",
            description="Create a Python function to calculate factorial",
            context={"language": "python", "requirements": "recursive implementation"},
            priority=1,
            created_at=time.time(),
        ),
        Task(
            id="task_2",
            type="coding",
            description="Create a function to validate email addresses",
            context={"language": "python", "requirements": "use regex"},
            priority=2,
            created_at=time.time(),
        ),
    ]

    # Assign tasks
    for task in test_tasks:
        autonomous_workforce.assign_task(AgentType.CODER, task)

    print(f"\n📋 Assigned {len(test_tasks)} tasks to autonomous agents")
    print("🚶 Walking away... agents working independently...")

    # Let agents work for a while
    await asyncio.sleep(20)

    # Show status
    status = autonomous_workforce.get_workforce_status()
    print(f"\n📊 Workforce Status:")
    print(f"   Active Agents: {status['active_agents']}/{status['total_agents']}")

    for agent_id, details in status["agent_details"].items():
        print(
            f"   {agent_id}: {details['tasks_completed']} tasks, {details['runtime']:.1f}s runtime"
        )

    # Stop workforce
    await autonomous_workforce.stop_workforce()

    print("\n🎯 Autonomous AI Workforce Demo Complete!")


if __name__ == "__main__":
    asyncio.run(main())
