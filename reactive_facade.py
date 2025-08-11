#!/usr/bin/env python3
"""
Reactive Facade - Core Architecture
The fundamental loop: Intent → Redis Stream → AI Response → Reality

This is the beating heart of the composable AI development environment.
"""

import redis
import json
import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from robust_claude_integration import claude_integration


class IntentType(Enum):
    KEYSTROKE = "keystroke"
    COMMAND = "command"
    QUERY = "query"
    MODE_SWITCH = "mode_switch"
    WORKFLOW = "workflow"


@dataclass
class Intent:
    """Represents user intent captured from various sources"""

    id: str
    type: IntentType
    content: str
    context: Dict[str, Any]
    timestamp: float
    source: str  # emacs, cli, api, etc.


@dataclass
class Response:
    """AI-generated response to user intent"""

    intent_id: str
    content: str
    actions: List[Dict[str, Any]]
    confidence: float
    execution_time: float
    source_agent: str


class ReactiveFacade:
    """
    The core reactive system that bridges human intent with AI reality.

    This is what makes the system feel magical - you think it, it happens.
    """

    def __init__(self, redis_host="localhost", redis_port=6379):
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )
        self.logger = logging.getLogger(__name__)
        self.active_modes = set()
        self.context_memory = {}
        self.running = False

        # Stream names
        self.intent_stream = "reactive:intents"
        self.response_stream = "reactive:responses"
        self.action_stream = "reactive:actions"

        # Event handlers for different intent types
        self.intent_handlers = {
            IntentType.KEYSTROKE: self._handle_keystroke_intent,
            IntentType.COMMAND: self._handle_command_intent,
            IntentType.QUERY: self._handle_query_intent,
            IntentType.MODE_SWITCH: self._handle_mode_switch,
            IntentType.WORKFLOW: self._handle_workflow_intent,
        }

        # Initialize streams
        self._initialize_streams()

    def _initialize_streams(self):
        """Initialize Redis streams for reactive processing"""
        try:
            # Create consumer groups if they don't exist
            streams = [self.intent_stream, self.response_stream, self.action_stream]
            for stream in streams:
                try:
                    self.redis.xgroup_create(
                        stream, "reactive_processors", "0", mkstream=True
                    )
                except redis.ResponseError as e:
                    if "BUSYGROUP" not in str(e):
                        raise

            self.logger.info("✅ Reactive streams initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize streams: {e}")

    async def start_reactive_loop(self):
        """Start the main reactive processing loop"""
        self.running = True
        self.logger.info("🚀 Starting reactive facade loop")

        while self.running:
            try:
                await self._process_intent_stream()
                await asyncio.sleep(0.1)  # Small delay to prevent tight loop
            except Exception as e:
                self.logger.error(f"Error in reactive loop: {e}")
                await asyncio.sleep(1)

    async def _process_intent_stream(self):
        """Process incoming intents from the stream"""
        try:
            # Read from intent stream
            messages = self.redis.xreadgroup(
                "reactive_processors",
                "processor_main",
                {self.intent_stream: ">"},
                count=10,
                block=100,
            )

            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    intent = self._deserialize_intent(fields)
                    if intent:
                        response = await self._process_intent(intent)
                        if response:
                            await self._publish_response(response)

                        # Acknowledge message
                        self.redis.xack(
                            self.intent_stream, "reactive_processors", msg_id
                        )

        except Exception as e:
            self.logger.error(f"Error processing intent stream: {e}")

    def _deserialize_intent(self, fields: Dict[str, str]) -> Optional[Intent]:
        """Convert Redis stream fields back to Intent object"""
        try:
            return Intent(
                id=fields["id"],
                type=IntentType(fields["type"]),
                content=fields["content"],
                context=json.loads(fields.get("context", "{}")),
                timestamp=float(fields["timestamp"]),
                source=fields["source"],
            )
        except Exception as e:
            self.logger.error(f"Failed to deserialize intent: {e}")
            return None

    async def _process_intent(self, intent: Intent) -> Optional[Response]:
        """Process an intent and generate appropriate response"""
        start_time = time.time()

        try:
            # Route to appropriate handler
            handler = self.intent_handlers.get(intent.type)
            if not handler:
                self.logger.warning(f"No handler for intent type: {intent.type}")
                return None

            # Execute handler
            response_data = await handler(intent)
            if not response_data:
                return None

            # Create response object
            response = Response(
                intent_id=intent.id,
                content=response_data.get("content", ""),
                actions=response_data.get("actions", []),
                confidence=response_data.get("confidence", 0.5),
                execution_time=time.time() - start_time,
                source_agent=response_data.get("agent", "reactive_facade"),
            )

            return response

        except Exception as e:
            self.logger.error(f"Error processing intent {intent.id}: {e}")
            return None

    async def _handle_keystroke_intent(self, intent: Intent) -> Dict[str, Any]:
        """Handle keystroke-level intentions"""
        keystroke = intent.content
        context = intent.context

        # Analyze keystroke patterns for intelligent prediction
        if self._is_completion_trigger(keystroke, context):
            return await self._generate_completion(context)
        elif self._is_documentation_trigger(keystroke, context):
            return await self._generate_documentation(context)
        elif self._is_refactor_trigger(keystroke, context):
            return await self._suggest_refactoring(context)
        else:
            # Store keystroke for pattern learning
            await self._store_keystroke_pattern(keystroke, context)
            return None

    async def _handle_command_intent(self, intent: Intent) -> Dict[str, Any]:
        """Handle explicit command intentions"""
        command = intent.content
        context = intent.context

        if command.startswith("generate"):
            return await self._handle_generation_command(command, context)
        elif command.startswith("explain"):
            return await self._handle_explanation_command(command, context)
        elif command.startswith("refactor"):
            return await self._handle_refactor_command(command, context)
        elif command.startswith("test"):
            return await self._handle_test_command(command, context)
        else:
            return await self._handle_natural_language_command(command, context)

    async def _handle_query_intent(self, intent: Intent) -> Dict[str, Any]:
        """Handle query/question intentions"""
        query = intent.content
        context = intent.context

        # Use Claude for intelligent query response
        if claude_integration.is_available():
            prompt = f"""You are an intelligent development assistant integrated into a Redis-based reactive facade system.

User Query: {query}

Context: {json.dumps(context, indent=2)}

Provide a helpful response that considers:
1. The current development context
2. Best practices and patterns
3. Actionable next steps

Keep the response concise but comprehensive."""

            response = claude_integration.execute_prompt(prompt)
            if response.success:
                return {
                    "content": response.content,
                    "actions": [],
                    "confidence": 0.8,
                    "agent": "claude_query_handler",
                }

        # Fallback response
        return {
            "content": f"Query received: {query}. Claude integration not available for detailed response.",
            "actions": [],
            "confidence": 0.3,
            "agent": "fallback_query_handler",
        }

    async def _handle_mode_switch(self, intent: Intent) -> Dict[str, Any]:
        """Handle mode switching (composable minor modes)"""
        mode_data = intent.context
        from_mode = mode_data.get("from")
        to_mode = mode_data.get("to")

        # Deactivate old mode
        if from_mode and from_mode in self.active_modes:
            await self._deactivate_mode(from_mode)

        # Activate new mode
        if to_mode:
            await self._activate_mode(to_mode, mode_data.get("config", {}))

        return {
            "content": f"Switched from {from_mode} to {to_mode}",
            "actions": [{"type": "mode_change", "from": from_mode, "to": to_mode}],
            "confidence": 1.0,
            "agent": "mode_manager",
        }

    async def _handle_workflow_intent(self, intent: Intent) -> Dict[str, Any]:
        """Handle workflow-level intentions"""
        workflow = intent.context.get("workflow")

        # Execute workflow steps
        actions = []
        for step in workflow.get("steps", []):
            action = await self._execute_workflow_step(step)
            if action:
                actions.append(action)

        return {
            "content": f"Executed workflow: {workflow.get('name', 'unnamed')}",
            "actions": actions,
            "confidence": 0.9,
            "agent": "workflow_executor",
        }

    async def _publish_response(self, response: Response):
        """Publish response to the response stream"""
        try:
            # Convert to Redis-compatible format
            response_data = {
                "intent_id": response.intent_id,
                "content": response.content,
                "actions": json.dumps(response.actions),
                "confidence": str(response.confidence),
                "execution_time": str(response.execution_time),
                "source_agent": response.source_agent,
            }

            self.redis.xadd(self.response_stream, response_data)
            self.logger.debug(f"Published response for intent {response.intent_id}")
        except Exception as e:
            self.logger.error(f"Failed to publish response: {e}")

    def capture_intent(
        self,
        intent_type: IntentType,
        content: str,
        context: Dict[str, Any],
        source: str = "api",
    ) -> str:
        """Capture user intent and add to processing stream"""
        intent = Intent(
            id=f"intent_{int(time.time() * 1000)}",
            type=intent_type,
            content=content,
            context=context,
            timestamp=time.time(),
            source=source,
        )

        # Convert to Redis-compatible format
        intent_data = {
            "id": intent.id,
            "type": intent.type.value,  # Convert enum to string
            "content": intent.content,
            "context": json.dumps(intent.context),  # Serialize dict to JSON
            "timestamp": str(intent.timestamp),
            "source": intent.source,
        }

        # Add to Redis stream
        self.redis.xadd(self.intent_stream, intent_data)

        return intent.id

    def stop(self):
        """Stop the reactive loop"""
        self.running = False
        self.logger.info("🛑 Stopping reactive facade")

    # Placeholder methods for specific handlers (to be implemented)
    async def _generate_completion(self, context):
        return None

    async def _generate_documentation(self, context):
        return None

    async def _suggest_refactoring(self, context):
        return None

    async def _store_keystroke_pattern(self, keystroke, context):
        pass

    async def _handle_generation_command(self, command, context):
        return None

    async def _handle_explanation_command(self, command, context):
        return None

    async def _handle_refactor_command(self, command, context):
        return None

    async def _handle_test_command(self, command, context):
        return None

    async def _handle_natural_language_command(self, command, context):
        return None

    async def _deactivate_mode(self, mode):
        pass

    async def _activate_mode(self, mode, config):
        pass

    async def _execute_workflow_step(self, step):
        return None

    def _is_completion_trigger(self, keystroke, context):
        return False

    def _is_documentation_trigger(self, keystroke, context):
        return False

    def _is_refactor_trigger(self, keystroke, context):
        return False


# Global reactive facade instance
reactive_facade = ReactiveFacade()

if __name__ == "__main__":

    async def test_reactive_facade():
        """Test the reactive facade"""
        print("🧪 Testing Reactive Facade")

        # Start the reactive loop in background
        loop_task = asyncio.create_task(reactive_facade.start_reactive_loop())

        # Simulate some intents
        await asyncio.sleep(1)

        intent_id = reactive_facade.capture_intent(
            IntentType.QUERY,
            "How do I implement error handling?",
            {"file": "test.py", "line": 42},
            "test",
        )

        print(f"Captured intent: {intent_id}")

        # Let it process
        await asyncio.sleep(2)

        reactive_facade.stop()
        await loop_task

    asyncio.run(test_reactive_facade())
