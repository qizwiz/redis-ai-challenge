#!/usr/bin/env python3
"""
Multi-Agent Coordination Protocol
Coordinates workflow learning, context management, document monitoring, and execution engine agents
"""

import redis
import json
import time
import hashlib
import asyncio
from typing import Dict, List, Optional, Tuple, Set, Any, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import threading
import fastmcp


class AgentType(Enum):
    WORKFLOW_LEARNER = "workflow_learner"
    CONTEXT_MANAGER = "context_manager"
    DOCUMENT_MONITOR = "document_monitor"
    EXECUTION_ENGINE = "execution_engine"


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentCapability:
    agent_type: AgentType
    capabilities: List[str]
    max_concurrent_tasks: int
    average_response_time: float
    current_load: int
    last_heartbeat: float
    health_status: str  # 'healthy', 'degraded', 'offline'


@dataclass
class CoordinationTask:
    task_id: str
    task_type: str
    priority: TaskPriority
    data: Dict[str, Any]
    assigned_agents: List[AgentType]
    dependencies: List[str]  # other task IDs
    created_time: float
    deadline: Optional[float]
    status: str  # 'pending', 'assigned', 'in_progress', 'completed', 'failed'
    results: Dict[str, Any]


@dataclass
class CoordinationEvent:
    event_id: str
    event_type: str  # 'task_request', 'agent_response', 'status_update', 'emergency'
    source_agent: Optional[AgentType]
    target_agents: List[AgentType]
    data: Dict[str, Any]
    timestamp: float
    correlation_id: Optional[str]


class WorkflowOrchestrator:
    """Orchestrates complex workflows across multiple agents"""

    def __init__(self):
        self.active_workflows = {}
        self.workflow_templates = self._load_workflow_templates()

    def _load_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Define common workflow patterns"""
        return {
            "code_analysis_workflow": {
                "steps": [
                    {"agent": AgentType.DOCUMENT_MONITOR, "action": "scan_documents"},
                    {
                        "agent": AgentType.CONTEXT_MANAGER,
                        "action": "get_relevant_context",
                    },
                    {
                        "agent": AgentType.EXECUTION_ENGINE,
                        "action": "analyze_code_security",
                    },
                    {
                        "agent": AgentType.WORKFLOW_LEARNER,
                        "action": "record_workflow_event",
                    },
                ],
                "timeout": 30.0,
                "retry_policy": "linear_backoff",
            },
            "document_update_workflow": {
                "steps": [
                    {"agent": AgentType.DOCUMENT_MONITOR, "action": "scan_documents"},
                    {"agent": AgentType.CONTEXT_MANAGER, "action": "add_context"},
                    {
                        "agent": AgentType.EXECUTION_ENGINE,
                        "action": "generate_code_from_template",
                    },
                    {
                        "agent": AgentType.WORKFLOW_LEARNER,
                        "action": "get_workflow_predictions",
                    },
                ],
                "timeout": 45.0,
                "retry_policy": "exponential_backoff",
            },
            "learning_synthesis_workflow": {
                "steps": [
                    {
                        "agent": AgentType.WORKFLOW_LEARNER,
                        "action": "get_workflow_patterns",
                    },
                    {
                        "agent": AgentType.CONTEXT_MANAGER,
                        "action": "get_session_summary",
                    },
                    {
                        "agent": AgentType.DOCUMENT_MONITOR,
                        "action": "analyze_document_trends",
                    },
                    {
                        "agent": AgentType.EXECUTION_ENGINE,
                        "action": "execution_engine_status",
                    },
                ],
                "timeout": 60.0,
                "retry_policy": "none",
            },
        }

    def start_workflow(self, workflow_type: str, context: Dict[str, Any]) -> str:
        """Start a coordinated workflow"""
        workflow_id = hashlib.md5(f"{workflow_type}{time.time()}".encode()).hexdigest()[
            :12
        ]

        template = self.workflow_templates.get(workflow_type)
        if not template:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

        workflow = {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "context": context,
            "template": template,
            "current_step": 0,
            "step_results": [],
            "status": "running",
            "start_time": time.time(),
        }

        self.active_workflows[workflow_id] = workflow
        return workflow_id

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a running workflow"""
        return self.active_workflows.get(workflow_id)


class MultiAgentCoordinator:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.Redis(decode_responses=True)
        self.agent_registry = {}  # AgentType -> AgentCapability
        self.task_queue = deque()
        self.active_tasks = {}  # task_id -> CoordinationTask
        self.orchestrator = WorkflowOrchestrator()
        self.coordinator_id = hashlib.md5(
            f"coordinator_{time.time()}".encode()
        ).hexdigest()[:12]

        # Coordination settings
        self.heartbeat_interval = 10  # seconds
        self.task_timeout = 60  # seconds
        self.max_retries = 3

        # Performance tracking
        self.coordination_metrics = {
            "tasks_processed": 0,
            "tasks_failed": 0,
            "average_task_time": 0.0,
            "agent_utilization": {},
            "start_time": time.time(),
        }

        # Initialize agent capabilities
        self._initialize_agent_capabilities()

    def _initialize_agent_capabilities(self):
        """Initialize known agent capabilities"""
        self.agent_registry[AgentType.WORKFLOW_LEARNER] = AgentCapability(
            agent_type=AgentType.WORKFLOW_LEARNER,
            capabilities=[
                "record_workflow_event",
                "get_workflow_predictions",
                "get_workflow_patterns",
            ],
            max_concurrent_tasks=5,
            average_response_time=0.5,
            current_load=0,
            last_heartbeat=time.time(),
            health_status="healthy",
        )

        self.agent_registry[AgentType.CONTEXT_MANAGER] = AgentCapability(
            agent_type=AgentType.CONTEXT_MANAGER,
            capabilities=["add_context", "get_relevant_context", "get_session_summary"],
            max_concurrent_tasks=10,
            average_response_time=0.3,
            current_load=0,
            last_heartbeat=time.time(),
            health_status="healthy",
        )

        self.agent_registry[AgentType.DOCUMENT_MONITOR] = AgentCapability(
            agent_type=AgentType.DOCUMENT_MONITOR,
            capabilities=[
                "scan_documents",
                "get_document_summary",
                "get_recent_changes",
            ],
            max_concurrent_tasks=3,
            average_response_time=1.0,
            current_load=0,
            last_heartbeat=time.time(),
            health_status="healthy",
        )

        self.agent_registry[AgentType.EXECUTION_ENGINE] = AgentCapability(
            agent_type=AgentType.EXECUTION_ENGINE,
            capabilities=[
                "execute_code",
                "analyze_code_security",
                "generate_code_from_template",
            ],
            max_concurrent_tasks=2,
            average_response_time=2.0,
            current_load=0,
            last_heartbeat=time.time(),
            health_status="healthy",
        )

    def register_agent(
        self, agent_type: AgentType, capabilities: List[str], max_concurrent: int = 5
    ) -> bool:
        """Register an agent with the coordinator"""
        self.agent_registry[agent_type] = AgentCapability(
            agent_type=agent_type,
            capabilities=capabilities,
            max_concurrent_tasks=max_concurrent,
            average_response_time=1.0,
            current_load=0,
            last_heartbeat=time.time(),
            health_status="healthy",
        )

        # Publish registration event
        self._publish_event(
            CoordinationEvent(
                event_id=self._generate_id(),
                event_type="agent_registration",
                source_agent=agent_type,
                target_agents=[],
                data={"capabilities": capabilities, "max_concurrent": max_concurrent},
                timestamp=time.time(),
                correlation_id=None,
            )
        )

        return True

    def submit_task(
        self,
        task_type: str,
        data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        required_capabilities: List[str] = None,
        deadline: Optional[float] = None,
    ) -> str:
        """Submit a coordination task"""

        task_id = self._generate_id()

        # Determine which agents can handle this task
        assigned_agents = self._select_agents(required_capabilities or [task_type])

        task = CoordinationTask(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            data=data,
            assigned_agents=assigned_agents,
            dependencies=[],
            created_time=time.time(),
            deadline=deadline,
            status="pending",
            results={},
        )

        self.active_tasks[task_id] = task
        self.task_queue.append(task)

        # Store in Redis for persistence
        self._store_task(task)

        return task_id

    def _select_agents(self, required_capabilities: List[str]) -> List[AgentType]:
        """Select best agents for required capabilities"""
        selected_agents = []

        for capability in required_capabilities:
            best_agent = None
            best_score = -1

            for agent_type, agent_info in self.agent_registry.items():
                if (
                    capability in agent_info.capabilities
                    and agent_info.health_status == "healthy"
                    and agent_info.current_load < agent_info.max_concurrent_tasks
                ):

                    # Score based on load and response time
                    load_factor = 1.0 - (
                        agent_info.current_load / agent_info.max_concurrent_tasks
                    )
                    time_factor = 1.0 / max(agent_info.average_response_time, 0.1)
                    score = load_factor * 0.7 + time_factor * 0.3

                    if score > best_score:
                        best_score = score
                        best_agent = agent_type

            if best_agent and best_agent not in selected_agents:
                selected_agents.append(best_agent)

        return selected_agents

    def process_task_queue(self) -> int:
        """Process pending tasks in the queue"""
        processed_count = 0

        while self.task_queue and processed_count < 10:  # Limit processing per call
            task = self.task_queue.popleft()

            if self._can_process_task(task):
                self._execute_task(task)
                processed_count += 1
            else:
                # Put back in queue if can't process yet
                self.task_queue.append(task)
                break

        return processed_count

    def _execute_task(self, task: CoordinationTask):
        """Execute a coordination task"""
        task.status = "in_progress"

        # Update agent loads
        for agent_type in task.assigned_agents:
            if agent_type in self.agent_registry:
                self.agent_registry[agent_type].current_load += 1

        # Publish task execution event
        event = CoordinationEvent(
            event_id=self._generate_id(),
            event_type="task_execution",
            source_agent=None,
            target_agents=task.assigned_agents,
            data={
                "task_id": task.task_id,
                "task_type": task.task_type,
                "task_data": task.data,
            },
            timestamp=time.time(),
            correlation_id=task.task_id,
        )

        self._publish_event(event)
        self._store_task(task)

    def complete_task(
        self, task_id: str, results: Dict[str, Any], agent_type: AgentType
    ) -> bool:
        """Mark task as completed by an agent"""

        task = self.active_tasks.get(task_id)
        if not task:
            return False

        # Update task results
        task.results[agent_type.value] = results

        # Check if all assigned agents have completed
        completed_agents = set(task.results.keys())
        required_agents = set(agent.value for agent in task.assigned_agents)

        if completed_agents >= required_agents:
            task.status = "completed"

            # Update metrics
            execution_time = time.time() - task.created_time
            self.coordination_metrics["tasks_processed"] += 1
            self.coordination_metrics["average_task_time"] = (
                self.coordination_metrics["average_task_time"]
                * (self.coordination_metrics["tasks_processed"] - 1)
                + execution_time
            ) / self.coordination_metrics["tasks_processed"]

        # Update agent load
        if agent_type in self.agent_registry:
            self.agent_registry[agent_type].current_load -= 1

        self._store_task(task)
        return True

    def start_workflow(self, workflow_type: str, context: Dict[str, Any]) -> str:
        """Start a coordinated multi-agent workflow"""
        return self.orchestrator.start_workflow(workflow_type, context)

    def get_coordination_status(self) -> Dict[str, Any]:
        """Get overall coordination status"""
        active_agents = sum(
            1
            for agent in self.agent_registry.values()
            if agent.health_status == "healthy"
        )

        total_load = sum(agent.current_load for agent in self.agent_registry.values())
        max_capacity = sum(
            agent.max_concurrent_tasks for agent in self.agent_registry.values()
        )

        return {
            "coordinator_id": self.coordinator_id,
            "active_agents": active_agents,
            "total_agents": len(self.agent_registry),
            "pending_tasks": len(self.task_queue),
            "active_tasks": len(
                [t for t in self.active_tasks.values() if t.status == "in_progress"]
            ),
            "completed_tasks": self.coordination_metrics["tasks_processed"],
            "failed_tasks": self.coordination_metrics["failed_tasks"],
            "system_load": total_load / max(max_capacity, 1),
            "average_task_time": self.coordination_metrics["average_task_time"],
            "uptime": time.time() - self.coordination_metrics["start_time"],
        }

    def _generate_id(self) -> str:
        """Generate unique ID"""
        return hashlib.md5(f"{time.time()}{self.coordinator_id}".encode()).hexdigest()[
            :12
        ]

    def health_check(self) -> Dict[str, Any]:
        """Perform system health check"""
        unhealthy_agents = []
        total_capacity = 0
        used_capacity = 0

        for agent_type, agent_info in self.agent_registry.items():
            total_capacity += agent_info.max_concurrent_tasks
            used_capacity += agent_info.current_load

            # Check if agent hasn't sent heartbeat recently
            if time.time() - agent_info.last_heartbeat > self.heartbeat_interval * 2:
                agent_info.health_status = "offline"
                unhealthy_agents.append(agent_type.value)

        return {
            "overall_health": "healthy" if not unhealthy_agents else "degraded",
            "unhealthy_agents": unhealthy_agents,
            "capacity_utilization": used_capacity / max(total_capacity, 1),
            "coordination_latency": self.coordination_metrics["average_task_time"],
            "error_rate": self.coordination_metrics["failed_tasks"]
            / max(
                self.coordination_metrics["tasks_processed"]
                + self.coordination_metrics["failed_tasks"],
                1,
            ),
        }


# FastMCP Server
mcp = fastmcp.FastMCP("multi-agent-coordinator")
coordinator = MultiAgentCoordinator()


@mcp.tool()
def submit_coordination_task(
    task_type: str, data: dict, priority: str = "medium"
) -> str:
    """Submit a task for multi-agent coordination"""
    priority_map = {
        "low": TaskPriority.LOW,
        "medium": TaskPriority.MEDIUM,
        "high": TaskPriority.HIGH,
        "critical": TaskPriority.CRITICAL,
    }

    task_priority = priority_map.get(priority.lower(), TaskPriority.MEDIUM)
    task_id = coordinator.submit_task(task_type, data, task_priority)

    return f"✅ **TASK SUBMITTED: {task_id}**\n\nTask: {task_type}\nPriority: {priority}\nData: {json.dumps(data, indent=2)}"


@mcp.tool()
def start_coordination_workflow(workflow_type: str, context: dict) -> str:
    """Start a coordinated multi-agent workflow"""
    try:
        workflow_id = coordinator.start_workflow(workflow_type, context)

        workflow_status = coordinator.orchestrator.get_workflow_status(workflow_id)

        result = f"🚀 **WORKFLOW STARTED: {workflow_id}**\n\n"
        result += f"**Type:** {workflow_type}\n"
        result += f"**Steps:** {len(workflow_status['template']['steps'])}\n"
        result += f"**Status:** {workflow_status['status']}\n"
        result += f"**Timeout:** {workflow_status['template']['timeout']}s\n\n"

        result += "**Workflow Steps:**\n"
        for i, step in enumerate(workflow_status["template"]["steps"], 1):
            result += f"  {i}. {step['agent'].value}: {step['action']}\n"

        return result

    except Exception as e:
        return f"❌ Failed to start workflow: {str(e)}"


@mcp.tool()
def get_coordination_status() -> str:
    """Get current coordination system status"""
    status = coordinator.get_coordination_status()

    result = f"🎛️ **MULTI-AGENT COORDINATION STATUS**\n\n"
    result += f"**Coordinator ID:** {status['coordinator_id']}\n"
    result += f"**Active Agents:** {status['active_agents']}/{status['total_agents']}\n"
    result += f"**Pending Tasks:** {status['pending_tasks']}\n"
    result += f"**Active Tasks:** {status['active_tasks']}\n"
    result += f"**Completed Tasks:** {status['completed_tasks']}\n"
    result += f"**Failed Tasks:** {status['failed_tasks']}\n"
    result += f"**System Load:** {status['system_load']:.1%}\n"
    result += f"**Average Task Time:** {status['average_task_time']:.2f}s\n"
    result += f"**Uptime:** {status['uptime']:.1f}s\n\n"

    # Agent details
    result += "**Agent Registry:**\n"
    for agent_type, agent_info in coordinator.agent_registry.items():
        load_pct = (agent_info.current_load / agent_info.max_concurrent_tasks) * 100
        result += f"  - {agent_type.value}: {agent_info.health_status} ({load_pct:.0f}% load)\n"

    return result


@mcp.tool()
def process_coordination_queue() -> str:
    """Process pending coordination tasks"""
    processed = coordinator.process_task_queue()

    if processed == 0:
        return "⏳ No tasks processed - queue empty or agents busy"

    return f"⚡ Processed {processed} coordination tasks"


@mcp.tool()
def get_agent_capabilities() -> str:
    """Get capabilities of all registered agents"""
    result = f"🤖 **AGENT CAPABILITIES**\n\n"

    for agent_type, agent_info in coordinator.agent_registry.items():
        result += f"**{agent_type.value.upper()}**\n"
        result += f"  Health: {agent_info.health_status}\n"
        result += (
            f"  Load: {agent_info.current_load}/{agent_info.max_concurrent_tasks}\n"
        )
        result += f"  Avg Response: {agent_info.average_response_time:.2f}s\n"
        result += f"  Capabilities:\n"
        for capability in agent_info.capabilities:
            result += f"    - {capability}\n"
        result += "\n"

    return result


@mcp.tool()
def system_health_check() -> str:
    """Perform comprehensive system health check"""
    health = coordinator.health_check()

    status_emoji = "✅" if health["overall_health"] == "healthy" else "⚠️"

    result = f"{status_emoji} **SYSTEM HEALTH CHECK**\n\n"
    result += f"**Overall Health:** {health['overall_health']}\n"
    result += f"**Capacity Utilization:** {health['capacity_utilization']:.1%}\n"
    result += f"**Coordination Latency:** {health['coordination_latency']:.2f}s\n"
    result += f"**Error Rate:** {health['error_rate']:.1%}\n\n"

    if health["unhealthy_agents"]:
        result += f"**Unhealthy Agents:** {', '.join(health['unhealthy_agents'])}\n"
    else:
        result += "**All agents healthy** ✅\n"

    # Performance recommendations
    if health["capacity_utilization"] > 0.8:
        result += "\n⚠️ **High system load detected - consider scaling agents**"

    if health["error_rate"] > 0.1:
        result += "\n⚠️ **High error rate detected - check agent health**"

    return result


@mcp.tool()
def simulate_coordination_scenario() -> str:
    """Simulate a complex coordination scenario"""
    scenario_tasks = [
        {
            "task_type": "document_analysis",
            "data": {"file_path": "AI_EMACS_ARCHITECTURE.org"},
            "priority": "high",
        },
        {
            "task_type": "context_synthesis",
            "data": {"query": "multi-agent coordination"},
            "priority": "medium",
        },
        {
            "task_type": "workflow_prediction",
            "data": {"recent_events": ["buffer_switch", "command_execute"]},
            "priority": "low",
        },
        {
            "task_type": "code_generation",
            "data": {"template": "mcp_server", "name": "test_agent"},
            "priority": "medium",
        },
    ]

    submitted_tasks = []
    for task in scenario_tasks:
        task_id = coordinator.submit_task(
            task["task_type"], task["data"], TaskPriority[task["priority"].upper()]
        )
        submitted_tasks.append(task_id)

    # Start a workflow
    workflow_id = coordinator.start_workflow(
        "code_analysis_workflow", {"context": "coordination_simulation"}
    )

    result = f"🎭 **COORDINATION SCENARIO SIMULATED**\n\n"
    result += f"**Tasks Submitted:** {len(submitted_tasks)}\n"
    result += f"**Workflow Started:** {workflow_id}\n\n"

    result += "**Task IDs:**\n"
    for i, task_id in enumerate(submitted_tasks, 1):
        result += f"  {i}. {task_id}\n"

    return result


if __name__ == "__main__":
    print("🎛️ Starting Multi-Agent Coordination Protocol FastMCP Server")
    mcp.run()
