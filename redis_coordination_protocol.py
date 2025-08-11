#!/usr/bin/env python3
"""
Redis Coordination Protocol for AI-Emacs Integration
Implements the Redis backbone for multi-AI coordination as specified in AI_EMACS_ARCHITECTURE.org
"""

import asyncio
import json
import redis
import time
import threading
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for coordination protocol"""

    CONTENT_CHANGE = "content_change"
    AI_ANALYSIS = "ai_analysis"
    WORKFLOW_PATTERN = "workflow_pattern"
    CONTEXT_UPDATE = "context_update"
    EXECUTION_COMMAND = "execution_command"
    AGENT_HEARTBEAT = "agent_heartbeat"
    SYSTEM_STATUS = "system:status"


@dataclass
class CoordinationEvent:
    """Base coordination event structure"""

    event_type: EventType
    source: str
    timestamp: float
    data: Dict[str, Any]
    correlation_id: Optional[str] = None

    def to_redis_dict(self) -> Dict[str, str]:
        """Convert to Redis stream format"""
        return {
            "event_type": self.event_type.value,
            "source": self.source,
            "timestamp": str(self.timestamp),
            "data": json.dumps(self.data),
            "correlation_id": self.correlation_id or "",
        }

    @classmethod
    def from_redis_dict(cls, redis_data: Dict[str, str]) -> "CoordinationEvent":
        """Create from Redis stream data"""
        return cls(
            event_type=EventType(redis_data["event_type"]),
            source=redis_data["source"],
            timestamp=float(redis_data["timestamp"]),
            data=json.loads(redis_data["data"]),
            correlation_id=redis_data.get("correlation_id") or None,
        )


class StreamManager:
    """Manages Redis streams for coordination"""

    STREAMS = {
        EventType.CONTENT_CHANGE: "emacs:content",
        EventType.AI_ANALYSIS: "ai:analysis",
        EventType.WORKFLOW_PATTERN: "ai:patterns",
        EventType.CONTEXT_UPDATE: "ai:context",
        EventType.EXECUTION_COMMAND: "ai:execute",
        EventType.AGENT_HEARTBEAT: "system:heartbeat",
        EventType.SYSTEM_STATUS: "system:status",
    }

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.max_len = 1000  # Maximum stream length

    async def initialize_streams(self):
        """Initialize all coordination streams"""
        for event_type, stream_name in self.STREAMS.items():
            try:
                # Create stream with initial message
                self.redis.xadd(
                    stream_name, {"initialized": "true"}, maxlen=self.max_len
                )
                logger.info(f"Initialized stream: {stream_name}")
            except Exception as e:
                logger.warning(f"Could not initialize stream {stream_name}: {e}")

    def create_consumer_group(self, stream_name: str, group_name: str):
        """Create consumer group for stream processing"""
        try:
            self.redis.xgroup_create(stream_name, group_name, id="0", mkstream=True)
            logger.info(f"Created consumer group {group_name} for {stream_name}")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(
                    f"Consumer group {group_name} already exists for {stream_name}"
                )
            else:
                logger.error(f"Error creating consumer group: {e}")

    def publish_event(self, event: CoordinationEvent) -> str:
        """Publish coordination event to appropriate stream"""
        stream_name = self.STREAMS[event.event_type]

        try:
            event_id = self.redis.xadd(
                stream_name, event.to_redis_dict(), maxlen=self.max_len
            )
            logger.debug(f"Published event {event_id} to {stream_name}")
            return event_id.decode() if isinstance(event_id, bytes) else event_id
        except Exception as e:
            logger.error(f"Failed to publish event to {stream_name}: {e}")
            raise

    def read_events(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        count: int = 10,
        block: int = 500,
    ) -> List[CoordinationEvent]:
        """Read events from stream using a consumer group"""
        logger.debug(
            f"StreamManager.read_events called with: stream_name={stream_name}, group_name={group_name}, consumer_name={consumer_name}, count={count}, block={block}"
        )
        try:
            streams = self.redis.xreadgroup(
                group_name,
                consumer_name,
                {stream_name: ">"},  # Use '>' to read new messages
                count=count,
                block=block,
            )
            logger.debug(f"StreamManager.read_events raw xreadgroup output: {streams}")

            events = []
            for stream, messages in streams:
                for message_id, fields in messages:
                    try:
                        event = CoordinationEvent.from_redis_dict(fields)
                        events.append(event)
                    except Exception as e:
                        logger.warning(f"Could not parse event {message_id}: {e}")

            return events
        except Exception as e:
            logger.error(
                f"Failed to read from {stream_name} for consumer {consumer_name}: {e}"
            )
            return []


class AgentCoordinator:
    """Coordinates multiple AI agents through Redis"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.stream_manager = StreamManager(redis_client)
        self.active_agents = {}
        self.event_handlers = {}
        self.running = False

    async def initialize(self):
        """Initialize the coordination system"""
        await self.stream_manager.initialize_streams()

        # Create consumer groups for different event types
        for event_type, stream_name in StreamManager.STREAMS.items():
            self.stream_manager.create_consumer_group(stream_name, "ai_agents")

        logger.info("Agent coordinator initialized")

    def register_agent(self, agent_id: str, agent_type: str, capabilities: List[str]):
        """Register an AI agent with the coordinator"""
        agent_info = {
            "id": agent_id,
            "type": agent_type,
            "capabilities": capabilities,
            "status": "active",
            "last_heartbeat": time.time(),
            "registered_at": time.time(),
        }

        self.active_agents[agent_id] = agent_info

        # Store in Redis
        self.redis.hset("agents:registry", agent_id, json.dumps(agent_info))

        # Publish registration event
        event = CoordinationEvent(
            event_type=EventType.SYSTEM_STATUS,
            source="coordinator",
            timestamp=time.time(),
            data={
                "action": "agent_registered",
                "agent_id": agent_id,
                "agent_type": agent_type,
                "capabilities": capabilities,
            },
        )
        self.stream_manager.publish_event(event)

        logger.info(f"Registered agent: {agent_id} ({agent_type})")

    def unregister_agent(self, agent_id: str):
        """Unregister an AI agent"""
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]
            self.redis.hdel("agents:registry", agent_id)

            # Publish unregistration event
            event = CoordinationEvent(
                event_type=EventType.SYSTEM_STATUS,
                source="coordinator",
                timestamp=time.time(),
                data={"action": "agent_unregistered", "agent_id": agent_id},
            )
            self.stream_manager.publish_event(event)

            logger.info(f"Unregistered agent: {agent_id}")

    def register_event_handler(
        self, event_type: EventType, handler: Callable[[CoordinationEvent], None]
    ):
        """Register event handler for specific event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type.value}")

    async def start_coordination(self):
        """Start the coordination event loop"""
        self.running = True
        logger.info("Starting coordination event loop")

        # Start heartbeat monitoring
        asyncio.create_task(self._heartbeat_monitor())

        # Start event processing
        # The coordinator no longer processes events for agents directly
        # asyncio.create_task(self._process_events())

    async def stop_coordination(self):
        """Stop the coordination event loop"""
        self.running = False
        logger.info("Stopping coordination event loop")

    async def _heartbeat_monitor(self):
        """Monitor agent heartbeats"""
        while self.running:
            try:
                current_time = time.time()
                timeout_threshold = 30  # 30 seconds timeout

                for agent_id, agent_info in list(self.active_agents.items()):
                    if current_time - agent_info["last_heartbeat"] > timeout_threshold:
                        logger.warning(f"Agent {agent_id} heartbeat timeout")
                        agent_info["status"] = "timeout"

                        # Publish timeout event
                        event = CoordinationEvent(
                            event_type=EventType.SYSTEM_STATUS,
                            source="coordinator",
                            timestamp=current_time,
                            data={"action": "agent_timeout", "agent_id": agent_id},
                        )
                        self.stream_manager.publish_event(event)

                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                await asyncio.sleep(5)

    # Removed _process_events from AgentCoordinator
    # async def _process_events(self):
    #     """Process coordination events"""
    #     logger.debug("Entering _process_events loop.")
    #     while self.running:
    #         try:
    #             # Iterate through active agents and their registered event types
    #             for agent_id, agent_info in self.active_agents.items():
    #                 # For each event type the agent handles, read from its consumer group
    #                 # We need to get the actual agent instance to access its registered handlers
    #                 agent_instance = next((agent for agent in self.agents.values() if agent.agent_id == agent_id), None)
    #                 if not agent_instance:
    #                     logger.warning(f"Agent instance not found for {agent_id}")
    #                     continue

    #                 for event_type, handlers in agent_instance.event_handlers.items(): # Access handlers from agent instance
    #                     stream_name = StreamManager.STREAMS[event_type]
    #                     consumer_name = agent_instance.consumer_name

    #                     logger.debug(f"Agent {agent_id} reading events from stream: {stream_name} with consumer: {consumer_name}")
    #                     events = self.stream_manager.read_events(stream_name, "ai_agents", consumer_name, count=5, block=500)

    #                     if not events:
    #                         logger.debug(f"No new events for agent {agent_id} from stream: {stream_name}")

    #                     for event in events:
    #                         await self._handle_event(event)

    #             await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
    #         except Exception as e:
    #             logger.error(f"Event processing error: {e}")
    #             await asyncio.sleep(1)

    async def _handle_event(self, event: CoordinationEvent):
        """Handle a coordination event"""
        logger.debug(
            f"Received event in _handle_event: Type={event.event_type.value}, Source={event.source}"
        )
        try:
            # Update agent heartbeats
            if event.event_type == EventType.AGENT_HEARTBEAT:
                agent_id = event.data.get("agent_id")
                if agent_id in self.active_agents:
                    self.active_agents[agent_id]["last_heartbeat"] = event.timestamp
                    self.active_agents[agent_id]["status"] = "active"

            # Call registered handlers
            if event.event_type in self.event_handlers:
                logger.debug(f"Found handlers for event type: {event.event_type.value}")
                for handler in self.event_handlers[event.event_type]:
                    try:
                        handler(event)
                        logger.debug(f"Handler executed for {event.event_type.value}")
                    except Exception as e:
                        logger.error(f"Event handler error: {e}")

            logger.info(f"Handled event: {event.event_type.value} from {event.source}")
        except Exception as e:
            logger.error(f"Error handling event: {e}")

    def publish_content_change(
        self, buffer_name: str, content: str, position: int, correlation_id: str = None
    ):
        """Publish content change event"""
        event = CoordinationEvent(
            event_type=EventType.CONTENT_CHANGE,
            source="emacs",
            timestamp=time.time(),
            data={
                "buffer_name": buffer_name,
                "content": content[:1000],  # Limit content size
                "position": position,
                "content_length": len(content),
            },
            correlation_id=correlation_id,
        )
        return self.stream_manager.publish_event(event)

    def publish_ai_analysis(
        self,
        agent_id: str,
        analysis_type: str,
        results: Dict[str, Any],
        correlation_id: str = None,
    ):
        """Publish AI analysis results"""
        event = CoordinationEvent(
            event_type=EventType.AI_ANALYSIS,
            source=agent_id,
            timestamp=time.time(),
            data={
                "analysis_type": analysis_type,
                "results": results,
                "agent_id": agent_id,
            },
            correlation_id=correlation_id,
        )
        return self.stream_manager.publish_event(event)

    def publish_workflow_pattern(self, pattern_type: str, pattern_data: Dict[str, Any]):
        """Publish discovered workflow pattern"""
        event = CoordinationEvent(
            event_type=EventType.WORKFLOW_PATTERN,
            source="workflow_learner",
            timestamp=time.time(),
            data={
                "pattern_type": pattern_type,
                "pattern_data": pattern_data,
                "confidence": pattern_data.get("confidence", 0.5),
            },
        )
        return self.stream_manager.publish_event(event)

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents"""
        return {
            "total_agents": len(self.active_agents),
            "active_agents": [
                a for a in self.active_agents.values() if a["status"] == "active"
            ],
            "coordinator_running": self.running,
            "streams_active": list(StreamManager.STREAMS.values()),
        }


class AIAgent:
    """Base class for AI agents that participate in coordination"""

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[str],
        redis_client: redis.Redis,
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.redis = redis_client
        self.coordinator = AgentCoordinator(redis_client)
        self.running = False
        self.consumer_name = (
            f"{agent_id}_consumer"  # Unique consumer name for each agent
        )
        self.event_handlers = {}  # Each agent manages its own handlers

    async def start(self):
        """Start the AI agent"""
        await self.coordinator.initialize()
        self.coordinator.register_agent(
            self.agent_id, self.agent_type, self.capabilities
        )

        # Register event handlers and create consumer for each relevant stream
        await self._register_handlers()

        # Start heartbeat
        asyncio.create_task(self._send_heartbeat())

        # Start event processing for this agent
        asyncio.create_task(self._process_agent_events())

        self.running = True
        logger.info(f"AI Agent {self.agent_id} started")

    async def stop(self):
        """Stop the AI agent"""
        self.running = False
        self.coordinator.unregister_agent(self.agent_id)
        logger.info(f"AI Agent {self.agent_id} stopped")

    def register_event_handler(
        self, event_type: EventType, handler: Callable[[CoordinationEvent], None]
    ):
        """Register event handler for specific event type for this agent"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Agent {self.agent_id} registered handler for {event_type.value}")

    async def _process_agent_events(self):
        """Process events for this agent from its consumer groups"""
        logger.debug(f"Agent {self.agent_id} entering _process_agent_events loop.")
        while self.running:
            try:
                for event_type, handlers in self.event_handlers.items():
                    stream_name = StreamManager.STREAMS[event_type]

                    logger.debug(
                        f"Agent {self.agent_id} attempting to read from stream: {stream_name} with consumer: {self.consumer_name}"
                    )
                    events = self.redis.xreadgroup(
                        "ai_agents",
                        self.consumer_name,
                        {stream_name: ">"},  # Use '>' to read new messages
                        count=5,
                        block=500,
                    )
                    logger.debug(
                        f"Agent {self.agent_id} raw xreadgroup output for {stream_name}: {events}"
                    )

                    if events:
                        logger.debug(
                            f"Agent {self.agent_id} read {len(events)} events from {stream_name}"
                        )
                        for event_data in events:
                            # The structure of events from xreadgroup is a list of tuples: [(stream_name, [message1, message2, ...])]
                            # We need to iterate through the messages within each stream
                            for message_id, fields in event_data[1]:
                                try:
                                    event = CoordinationEvent.from_redis_dict(fields)
                                    for handler in handlers:
                                        try:
                                            handler(event)
                                            logger.debug(
                                                f"Agent {self.agent_id} handler executed for {event.event_type.value}"
                                            )
                                        except Exception as e:
                                            logger.error(
                                                f"Agent {self.agent_id} event handler error: {e}"
                                            )
                                except Exception as e:
                                    logger.warning(
                                        f"Agent {self.agent_id} could not parse event {message_id}: {e}"
                                    )
                    else:
                        logger.debug(
                            f"Agent {self.agent_id} no new events from {stream_name}"
                        )

                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
            except Exception as e:
                logger.error(f"Agent {self.agent_id} event processing error: {e}")
                await asyncio.sleep(1)

    async def _register_handlers(self):
        """Register event handlers - to be implemented by subclasses"""
        pass

    async def _send_heartbeat(self):
        """Send periodic heartbeat"""
        while self.running:
            try:
                event = CoordinationEvent(
                    event_type=EventType.AGENT_HEARTBEAT,
                    source=self.agent_id,
                    timestamp=time.time(),
                    data={
                        "agent_id": self.agent_id,
                        "agent_type": self.agent_type,
                        "status": "active",
                    },
                )
                self.coordinator.stream_manager.publish_event(event)
                await asyncio.sleep(15)  # Send heartbeat every 15 seconds
            except Exception as e:
                logger.error(f"Heartbeat error for {self.agent_id}: {e}")
                await asyncio.sleep(5)


# Example AI Agent Implementations


class CodeAnalyzerAgent(AIAgent):
    """AI agent for real-time code analysis"""

    def __init__(self, redis_client: redis.Redis):
        super().__init__(
            agent_id="advanced_code_analyzer",  # Changed agent_id to match demo
            agent_type="analysis",
            capabilities=["syntax_analysis", "code_quality", "suggestions"],
            redis_client=redis_client,
        )

    async def _register_handlers(self):
        """Register handlers for content changes"""
        self.register_event_handler(
            EventType.CONTENT_CHANGE, self._handle_content_change
        )
        # Create consumer for this agent for content changes
        stream_name = StreamManager.STREAMS[EventType.CONTENT_CHANGE]
        try:
            # Use xgroup_create to ensure the group exists, then create the consumer
            self.redis.xgroup_create(stream_name, "ai_agents", id="0", mkstream=True)
            self.redis.xgroup_createconsumer(
                stream_name, "ai_agents", self.consumer_name
            )
            logger.info(
                f"Agent {self.agent_id} created consumer {self.consumer_name} for {stream_name}"
            )
        except redis.ResponseError as e:
            if "BUSYGROUP: Consumer Group name already exists" in str(e):
                logger.info(
                    f"Consumer group 'ai_agents' already exists for stream {stream_name}. Creating consumer."
                )
                try:
                    self.redis.xgroup_createconsumer(
                        stream_name, "ai_agents", self.consumer_name
                    )
                    logger.info(
                        f"Agent {self.agent_id} created consumer {self.consumer_name} for {stream_name}"
                    )
                except redis.ResponseError as ce:
                    if "BUSYGROUP: Consumer name already exists" in str(ce):
                        logger.info(
                            f"Consumer {self.consumer_name} already exists for group ai_agents on stream {stream_name}"
                        )
                    else:
                        logger.error(
                            f"Error creating consumer {self.consumer_name} for {self.agent_id} on {stream_name}: {ce}"
                        )
            else:
                logger.error(
                    f"Error creating consumer group for {self.agent_id} on {stream_name}: {e}"
                )


class WorkflowLearnerAgent(AIAgent):
    """AI agent for workflow pattern learning"""

    def __init__(self, redis_client: redis.Redis):
        super().__init__(
            agent_id="workflow_learner",
            agent_type="learning",
            capabilities=["pattern_recognition", "workflow_prediction"],
            redis_client=redis_client,
        )
        self.pattern_cache = {}

    async def _register_handlers(self):
        """Register handlers for execution commands"""
        self.register_event_handler(
            EventType.EXECUTION_COMMAND, self._handle_execution_command
        )
        # Create consumer for this agent for execution commands
        stream_name = StreamManager.STREAMS[EventType.EXECUTION_COMMAND]
        try:
            # Use xgroup_create to ensure the group exists, then create the consumer
            self.redis.xgroup_create(stream_name, "ai_agents", id="0", mkstream=True)
            self.redis.xgroup_createconsumer(
                stream_name, "ai_agents", self.consumer_name
            )
            logger.info(
                f"Agent {self.agent_id} created consumer {self.consumer_name} for {stream_name}"
            )
        except redis.ResponseError as e:
            if "BUSYGROUP: Consumer Group name already exists" in str(e):
                logger.info(
                    f"Consumer group 'ai_agents' already exists for stream {stream_name}. Creating consumer."
                )
                try:
                    self.redis.xgroup_createconsumer(
                        stream_name, "ai_agents", self.consumer_name
                    )
                    logger.info(
                        f"Consumer {self.consumer_name} already exists for group ai_agents on stream {stream_name}"
                    )
                except redis.ResponseError as ce:
                    if "BUSYGROUP: Consumer name already exists" in str(ce):
                        logger.info(
                            f"Consumer {self.consumer_name} already exists for group ai_agents on stream {stream_name}"
                        )
                    else:
                        logger.error(
                            f"Error creating consumer {self.consumer_name} for {self.agent_id} on {stream_name}: {ce}"
                        )
            else:
                logger.error(
                    f"Error creating consumer group for {self.agent_id} on {stream_name}: {e}"
                )


# Testing and Demo Functions


async def demo_coordination_system():
    """Demonstrate the Redis coordination system"""
    logger.info("Starting Redis Coordination System Demo")

    # Initialize Redis client
    redis_client = redis.Redis(decode_responses=True)

    try:
        # Test Redis connection
        redis_client.ping()
    except redis.ConnectionError:
        logger.error("Could not connect to Redis. Make sure Redis is running.")
        return

    # Create coordinator
    coordinator = AgentCoordinator(redis_client)
    await coordinator.initialize()

    # Start coordination
    await coordinator.start_coordination()

    # Create and start AI agents
    code_analyzer = CodeAnalyzerAgent(redis_client)
    workflow_learner = WorkflowLearnerAgent(redis_client)

    await code_analyzer.start()
    await workflow_learner.start()

    # Simulate content changes
    logger.info("Simulating content changes...")
    coordinator.publish_content_change(
        "*scratch*", '(defun hello-world () (message "Hello, World!"))', 42
    )

    # Simulate execution commands
    coordinator.stream_manager.publish_event(
        CoordinationEvent(
            event_type=EventType.EXECUTION_COMMAND,
            source="emacs",
            timestamp=time.time(),
            data={"command": "switch-to-buffer *scratch*"},
        )
    )

    # Wait for processing
    await asyncio.sleep(2)

    # Show agent status
    status = coordinator.get_agent_status()
    logger.info(f"Coordination system status: {status}")

    # Stop agents
    await code_analyzer.stop()
    await workflow_learner.stop()
    await coordinator.stop_coordination()

    logger.info("Demo completed")


if __name__ == "__main__":
    asyncio.run(demo_coordination_system())
