#!/usr/bin/env python3
"""
Intelligent Response Processor - The Brain of the Revolutionary AI System

This processes keystrokes from Emacs and generates intelligent responses
that actually modify code, complete functions, and enhance development.
"""

import asyncio
import json
import time
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import redis
from robust_claude_integration import claude_integration

logger = logging.getLogger(__name__)


class ResponseType(Enum):
    INSERT_TEXT = "insert_text"
    REPLACE_TEXT = "replace_text"
    MOVE_CURSOR = "move_cursor"
    COMPLETE_FUNCTION = "complete_function"
    GENERATE_DOCS = "generate_docs"
    REFACTOR_CODE = "refactor_code"
    RUN_COMMAND = "run_command"
    SHOW_SUGGESTION = "show_suggestion"


@dataclass
class IntelligentAction:
    """An AI-generated action to execute in Emacs"""

    type: ResponseType
    content: str
    position: Optional[int] = None
    confidence: float = 0.0
    reasoning: str = ""
    metadata: Dict[str, Any] = None


class SemanticPatterns:
    """Semantic pattern recognition for development actions"""

    COMPLETION_TRIGGERS = {
        ".": "method_completion",
        "(": "function_signature",
        "[": "array_access",
        "{": "object_literal",
        "::": "namespace_access",
        "->": "pointer_dereference",
        "=>": "arrow_function",
    }

    DOCUMENTATION_TRIGGERS = {
        "def ",
        "function ",
        "class ",
        "fn ",
        "func ",
        "export function",
        "async def",
        "async function",
    }

    NAVIGATION_PATTERNS = {
        "ctrl+e": ("end-of-line", "move_cursor"),
        "ctrl+a": ("beginning-of-line", "move_cursor"),
        "ctrl+f": ("forward-char", "move_cursor"),
        "ctrl+b": ("backward-char", "move_cursor"),
        "meta+f": ("forward-word", "move_cursor"),
        "meta+b": ("backward-word", "move_cursor"),
    }


class IntelligentResponseProcessor:
    """Process keystrokes and generate intelligent AI responses"""

    def __init__(self, redis_host="localhost", redis_port=6379):
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )
        self.patterns = SemanticPatterns()
        self.context_memory = {}
        self.running = False

        # Performance tracking
        self.stats = {
            "keystrokes_processed": 0,
            "actions_generated": 0,
            "completions_successful": 0,
            "start_time": time.time(),
        }

    async def start_processing(self):
        """Start processing keystroke events from Redis streams"""
        self.running = True
        logger.info("🧠 Starting Intelligent Response Processor")

        while self.running:
            try:
                await self._process_keystroke_stream()
                await asyncio.sleep(0.05)  # High-frequency processing
            except Exception as e:
                logger.error(f"Processing error: {e}")
                await asyncio.sleep(1)

    async def _process_keystroke_stream(self):
        """Process keystrokes from revolutionary:keystrokes stream"""
        try:
            # Read from keystroke stream
            messages = self.redis.xread(
                {"revolutionary:keystrokes": "$"}, count=5, block=50
            )

            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    keystroke_data = json.loads(fields["data"])
                    await self._analyze_keystroke(keystroke_data)
                    self.stats["keystrokes_processed"] += 1

        except Exception as e:
            logger.error(f"Keystroke stream error: {e}")

    async def _analyze_keystroke(self, keystroke_data: Dict[str, Any]):
        """Analyze a keystroke event and generate intelligent response"""
        intent = keystroke_data.get("intent", "general")
        context = keystroke_data.get("context", {})

        # Store context for pattern learning
        session_id = context.get("session_id")
        if session_id:
            self.context_memory[session_id] = context

        # Route to appropriate handler
        actions = []

        if intent == "completion_trigger":
            actions = await self._handle_completion_trigger(context)
        elif intent == "documentation_request":
            actions = await self._handle_documentation_request(context)
        elif intent == "function_signature":
            actions = await self._handle_function_signature(context)
        elif intent == "navigation":
            actions = await self._handle_smart_navigation(context)
        elif intent == "editing":
            actions = await self._handle_intelligent_editing(context)
        elif keystroke_data.get("type") == "natural_command":
            actions = await self._handle_natural_command(keystroke_data)

        # Send actions back to Emacs
        for action in actions:
            await self._send_action_to_emacs(action)
            self.stats["actions_generated"] += 1

    async def _handle_completion_trigger(
        self, context: Dict[str, Any]
    ) -> List[IntelligentAction]:
        """Handle code completion triggers like '.' or '('"""
        actions = []

        last_key = context.get("last_key", "")
        line_content = context.get("line_content", "")
        cursor_context = context.get("cursor_context", {})
        major_mode = context.get("major_mode", "")

        if last_key == "." and not cursor_context.get("in_string"):
            # Method/property completion
            completion = await self._generate_method_completion(
                line_content, major_mode
            )
            if completion:
                actions.append(
                    IntelligentAction(
                        type=ResponseType.INSERT_TEXT,
                        content=completion,
                        confidence=0.8,
                        reasoning="Method completion based on context",
                    )
                )

        elif last_key == "(" and not cursor_context.get("in_string"):
            # Function signature help
            signature = await self._generate_function_signature(
                line_content, major_mode
            )
            if signature:
                actions.append(
                    IntelligentAction(
                        type=ResponseType.SHOW_SUGGESTION,
                        content=signature,
                        confidence=0.9,
                        reasoning="Function signature assistance",
                    )
                )

        return actions

    async def _handle_documentation_request(
        self, context: Dict[str, Any]
    ) -> List[IntelligentAction]:
        """Handle documentation generation requests"""
        actions = []

        function_name = context.get("function_name")
        line_content = context.get("line_content", "")
        major_mode = context.get("major_mode", "")

        # Check if we're at a function definition
        if any(
            trigger in line_content for trigger in self.patterns.DOCUMENTATION_TRIGGERS
        ):
            doc = await self._generate_function_documentation(
                line_content, major_mode, function_name
            )
            if doc:
                actions.append(
                    IntelligentAction(
                        type=ResponseType.GENERATE_DOCS,
                        content=doc,
                        confidence=0.85,
                        reasoning="Generated documentation for function definition",
                    )
                )

        return actions

    async def _handle_function_signature(
        self, context: Dict[str, Any]
    ) -> List[IntelligentAction]:
        """Handle function signature completion"""
        actions = []

        line_content = context.get("line_content", "")
        major_mode = context.get("major_mode", "")

        # Extract function being called
        match = re.search(r"(\w+)\s*\($", line_content)
        if match:
            function_name = match.group(1)
            signature = await self._get_function_signature(function_name, major_mode)

            if signature:
                actions.append(
                    IntelligentAction(
                        type=ResponseType.SHOW_SUGGESTION,
                        content=f"Signature: {signature}",
                        confidence=0.7,
                        reasoning=f"Function signature for {function_name}",
                    )
                )

        return actions

    async def _handle_smart_navigation(
        self, context: Dict[str, Any]
    ) -> List[IntelligentAction]:
        """Handle intelligent navigation assistance"""
        actions = []

        last_command = context.get("last_command", "")

        # Semantic equivalence mapping
        semantic_mapping = {
            "forward-char": "ctrl+f",
            "backward-char": "ctrl+b",
            "next-line": "ctrl+n",
            "previous-line": "ctrl+p",
            "beginning-of-line": "ctrl+a",
            "end-of-line": "ctrl+e",
        }

        if last_command in semantic_mapping:
            # Learn navigation patterns - this is where semantic equivalence happens
            await self._learn_navigation_pattern(
                context, semantic_mapping[last_command]
            )

        return actions

    async def _handle_intelligent_editing(
        self, context: Dict[str, Any]
    ) -> List[IntelligentAction]:
        """Handle intelligent editing assistance"""
        actions = []

        last_command = context.get("last_command", "")
        cursor_context = context.get("cursor_context", {})

        # Intelligent auto-completion for common patterns
        if last_command == "self-insert-command":
            completion = await self._predict_next_text(context)
            if completion:
                actions.append(
                    IntelligentAction(
                        type=ResponseType.SHOW_SUGGESTION,
                        content=completion,
                        confidence=0.6,
                        reasoning="Predictive text completion",
                    )
                )

        return actions

    async def _handle_natural_command(
        self, command_data: Dict[str, Any]
    ) -> List[IntelligentAction]:
        """Handle natural language commands"""
        actions = []

        command = command_data.get("command", "")
        context = command_data.get("context", {})

        if claude_integration.is_available():
            response = await self._process_with_claude(command, context)
            if response:
                actions.extend(response)
        else:
            # Use fallback processing
            actions = await self._process_command_fallback(command, context)

        return actions

    async def _process_with_claude(
        self, command: str, context: Dict[str, Any]
    ) -> List[IntelligentAction]:
        """Process command using Claude AI"""
        prompt = f"""You are an AI development assistant integrated into Emacs. 
        
User Command: {command}

Development Context:
- File: {context.get('file_name', 'unknown')}
- Function: {context.get('function_name', 'none')}
- Line: {context.get('line_number', 0)}
- Mode: {context.get('major_mode', 'unknown')}
- Line Content: {context.get('line_content', '')}

Generate specific actions to help the user. Respond in JSON format:
{{
  "actions": [
    {{
      "type": "insert_text|replace_text|generate_docs|complete_function|refactor_code",
      "content": "actual code or text to insert",
      "confidence": 0.0-1.0,
      "reasoning": "why this action helps"
    }}
  ]
}}

Focus on practical, executable actions that improve their code."""

        claude_response = claude_integration.execute_prompt(prompt)
        if claude_response.success:
            try:
                response_data = json.loads(claude_response.content)
                actions = []

                for action_data in response_data.get("actions", []):
                    action = IntelligentAction(
                        type=ResponseType(action_data["type"]),
                        content=action_data["content"],
                        confidence=action_data.get("confidence", 0.5),
                        reasoning=action_data.get("reasoning", ""),
                    )
                    actions.append(action)

                return actions
            except json.JSONDecodeError:
                logger.warning("Failed to parse Claude response as JSON")

        return []

    async def _generate_method_completion(
        self, line_content: str, major_mode: str
    ) -> Optional[str]:
        """Generate method completion suggestions"""
        # Extract object before the dot
        match = re.search(r"(\w+)\.$", line_content)
        if not match:
            return None

        obj_name = match.group(1)

        # Language-specific completions
        completions = {
            "python-mode": {
                "str": ["strip()", "split()", "replace()", "format()", "join()"],
                "list": ["append()", "extend()", "remove()", "pop()", "sort()"],
                "dict": ["keys()", "values()", "items()", "get()", "pop()"],
                "file": ["read()", "write()", "close()", "readline()", "readlines()"],
            },
            "js-mode": {
                "array": ["push()", "pop()", "map()", "filter()", "reduce()"],
                "string": [
                    "split()",
                    "slice()",
                    "replace()",
                    "trim()",
                    "toLowerCase()",
                ],
                "object": ["hasOwnProperty()", "toString()", "valueOf()"],
            },
        }

        if major_mode in completions:
            # Simple heuristic - return first method for the object type
            for obj_type, methods in completions[major_mode].items():
                if obj_type in obj_name.lower():
                    return methods[0]

        return None

    async def _generate_function_documentation(
        self, line_content: str, major_mode: str, function_name: str
    ) -> Optional[str]:
        """Generate function documentation"""
        if major_mode == "python-mode":
            return f'"""\n    {function_name.replace("_", " ").title()} function.\n    \n    Returns:\n        Description of return value\n    """'
        elif major_mode == "js-mode":
            return f'/**\n * {function_name.replace("_", " ")} function\n * @returns {{}} Description\n */'

        return None

    async def _get_function_signature(
        self, function_name: str, major_mode: str
    ) -> Optional[str]:
        """Get function signature help"""
        # This would connect to language servers or documentation
        common_signatures = {
            "print": 'print(*values, sep=" ", end="\\n", file=sys.stdout)',
            "len": "len(obj) -> int",
            "open": 'open(file, mode="r", encoding=None)',
            "range": "range(start, stop, step=1)",
            "map": "map(function, iterable)",
            "filter": "filter(function, iterable)",
        }

        return common_signatures.get(function_name)

    async def _predict_next_text(self, context: Dict[str, Any]) -> Optional[str]:
        """Predict next text based on context"""
        line_content = context.get("line_content", "").strip()

        # Simple pattern-based predictions
        if line_content.endswith("if "):
            return '__name__ == "__main__":'
        elif line_content.endswith("for "):
            return "i in range():"
        elif line_content.endswith("def "):
            return "function_name():"
        elif line_content.endswith("import "):
            return "os"

        return None

    async def _learn_navigation_pattern(
        self, context: Dict[str, Any], semantic_equivalent: str
    ):
        """Learn navigation patterns for semantic equivalence"""
        # Store the mapping between commands and semantic meaning
        pattern_key = f"nav_pattern_{context.get('session_id')}"
        pattern_data = {
            "command": context.get("last_command"),
            "semantic": semantic_equivalent,
            "context": context.get("cursor_context", {}),
            "timestamp": time.time(),
        }

        # Store in Redis for pattern learning
        self.redis.lpush(pattern_key, json.dumps(pattern_data))
        self.redis.ltrim(pattern_key, 0, 99)  # Keep last 100 patterns

    async def _send_action_to_emacs(self, action: IntelligentAction):
        """Send action back to Emacs via Redis stream"""
        action_data = {
            "type": action.type.value,
            "content": action.content,
            "position": action.position,
            "confidence": action.confidence,
            "reasoning": action.reasoning,
            "timestamp": time.time(),
        }

        self.redis.xadd("revolutionary:responses", action_data)
        logger.debug(f"Sent action to Emacs: {action.type.value}")

    def stop(self):
        """Stop the processor"""
        self.running = False
        logger.info("🛑 Intelligent Response Processor stopped")

        # Print stats
        runtime = time.time() - self.stats["start_time"]
        logger.info(f"📊 Processing Stats:")
        logger.info(f"   Keystrokes: {self.stats['keystrokes_processed']}")
        logger.info(f"   Actions: {self.stats['actions_generated']}")
        logger.info(f"   Runtime: {runtime:.1f}s")
        logger.info(
            f"   Rate: {self.stats['keystrokes_processed']/runtime:.1f} keystrokes/sec"
        )


# Global processor instance
intelligent_processor = IntelligentResponseProcessor()


async def main():
    """Test the intelligent processor"""
    print("🧠 Testing Intelligent Response Processor")

    # Start processor
    processor_task = asyncio.create_task(intelligent_processor.start_processing())

    # Let it run for a bit
    await asyncio.sleep(5)

    # Stop
    intelligent_processor.stop()
    await processor_task


if __name__ == "__main__":
    asyncio.run(main())
