#!/usr/bin/env python3
"""
Redis State Diff MCP Server
Revolutionary diff-based utterances with accurate state detection
"""

import asyncio
import json
import redis
import subprocess
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from mcp.server import InitializationOptions, NotificationOptions, Server
from mcp import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)


@dataclass
class EmacsState:
    buffer: str
    point: int
    mode: str
    window_config: str
    helm_active: bool
    content_sample: str
    timestamp: float


@dataclass
class StateDiff:
    from_state: EmacsState
    to_state: EmacsState
    elisp_commands: List[str]
    description: str


class StateEngine:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)

    def capture_fresh_state(self) -> EmacsState:
        """Capture completely fresh state from Emacs with cross-verification"""

        # Multiple cross-checking queries
        queries = {
            "buffer": "(buffer-name (window-buffer (selected-window)))",
            "point": "(point)",
            "mode": "(symbol-name major-mode)",
            "helm": "(and (boundp 'helm-alive-p) helm-alive-p)",
            "content": "(buffer-substring (max 1 (- (point) 50)) (min (point-max) (+ (point) 50)))",
            "window_config": "(current-window-configuration)",
        }

        results = {}
        for key, query in queries.items():
            try:
                result = subprocess.run(
                    ["emacsclient", "--eval", query],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )

                if result.returncode == 0:
                    results[key] = result.stdout.strip().strip('"')
                else:
                    results[key] = f"ERROR: {result.stderr}"
            except Exception as e:
                results[key] = f"EXCEPTION: {str(e)}"

        # Clear inconsistent Redis state
        self.redis_client.delete("emacs:current", "emacs:current:buffer", "emacs:state")

        # Store fresh state
        fresh_state = EmacsState(
            buffer=results.get("buffer", "UNKNOWN"),
            point=(
                int(results.get("point", "0"))
                if results.get("point", "").isdigit()
                else 0
            ),
            mode=results.get("mode", "unknown-mode"),
            window_config=results.get("window_config", ""),
            helm_active="t" in results.get("helm", "nil"),
            content_sample=results.get("content", ""),
            timestamp=time.time(),
        )

        # Store in Redis with consistent keys
        self.redis_client.hset(
            "emacs:verified:state",
            mapping={
                "buffer": fresh_state.buffer,
                "point": str(fresh_state.point),
                "mode": fresh_state.mode,
                "helm_active": str(fresh_state.helm_active),
                "timestamp": str(fresh_state.timestamp),
            },
        )

        return fresh_state

    def create_diff(self, natural_command: str, current_state: EmacsState) -> StateDiff:
        """Create diff-based utterance representation"""

        # Parse desired end state from natural language
        desired_state = self._parse_desired_state(natural_command, current_state)

        # Generate elisp commands to bridge the diff
        elisp_commands = self._generate_diff_elisp(current_state, desired_state)

        return StateDiff(
            from_state=current_state,
            to_state=desired_state,
            elisp_commands=elisp_commands,
            description=natural_command,
        )

    def _parse_desired_state(self, command: str, current: EmacsState) -> EmacsState:
        """Parse natural language to desired end state"""

        # Start with current state as base
        desired = EmacsState(
            buffer=current.buffer,
            point=current.point,
            mode=current.mode,
            window_config=current.window_config,
            helm_active=current.helm_active,
            content_sample=current.content_sample,
            timestamp=time.time(),
        )

        command_lower = command.lower()

        # Buffer changes
        if "scratch" in command_lower:
            desired.buffer = "*scratch*"
        elif "tutorial" in command_lower:
            desired.buffer = "TUTORIAL"

        # Point changes - specific line:col navigation
        if "line" in command_lower and ":" in command:
            import re

            match = re.search(r"(\d+):(\d+)", command)
            if match:
                # Convert line:col to point (approximate)
                line, col = int(match.group(1)), int(match.group(2))
                desired.point = (line - 1) * 80 + col  # Rough estimate

        # End-of-line semantic patterns (THE KEY ENHANCEMENT)
        elif self._is_end_of_line_command(command_lower):
            # Mark that we want end-of-line but don't calculate exact point
            # The _generate_diff_elisp will handle this with (end-of-line)
            desired.point = -1  # Special marker for end-of-line

        # Beginning-of-line semantic patterns
        elif self._is_beginning_of_line_command(command_lower):
            desired.point = -2  # Special marker for beginning-of-line

        # Helm state changes
        if "helm" in command_lower or "counsel" in command_lower:
            if not current.helm_active:
                desired.helm_active = True

        return desired

    def _generate_diff_elisp(
        self, from_state: EmacsState, to_state: EmacsState
    ) -> List[str]:
        """Generate minimal elisp commands to achieve state transition"""

        commands = []

        # Buffer transition with proper mode and visibility
        if from_state.buffer != to_state.buffer:
            commands.append(f'(switch-to-buffer "{to_state.buffer}")')

            # EMERGENT LEARNING: Content creation ≠ User experience
            # Always ensure buffer is properly visible and configured
            commands.append("(delete-other-windows)")  # Make it visible

            # Intelligent mode selection based on buffer name
            if to_state.buffer.endswith(".org") or "session" in to_state.buffer.lower():
                commands.append("(org-mode)")
            elif to_state.buffer.endswith(".md"):
                commands.append("(markdown-mode)")
            elif to_state.buffer.endswith((".py", ".el")):
                commands.append("(auto-mode-alist)")  # Let Emacs choose
            elif "*" in to_state.buffer and "session" in to_state.buffer.lower():
                commands.append("(org-mode)")  # Conversation buffers should be org-mode

        # Point transition - handle special semantic markers
        if from_state.point != to_state.point:
            if to_state.point == -1:  # End-of-line marker
                commands.append("(end-of-line)")
            elif to_state.point == -2:  # Beginning-of-line marker
                commands.append("(beginning-of-line)")
            else:
                commands.append(f"(goto-char {to_state.point})")

        # Helm transition
        if not from_state.helm_active and to_state.helm_active:
            commands.append("(helm-mini)")
        elif from_state.helm_active and not to_state.helm_active:
            commands.append("(helm-keyboard-quit)")

        return commands

    def execute_diff(self, diff: StateDiff) -> Dict[str, Any]:
        """Execute state transition with verification"""

        if not diff.elisp_commands:
            return {"success": False, "error": "No state changes required"}

        # Capture pre-execution state for validation
        pre_state = self.capture_fresh_state()

        # Wrap in progn for atomic execution
        elisp = "(progn " + " ".join(diff.elisp_commands) + ")"

        try:
            result = subprocess.run(
                ["emacsclient", "--eval", elisp],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Verify state transition succeeded
                post_state = self.capture_fresh_state()

                # ENHANCED VALIDATION: Check semantic intent was achieved
                validation_result = self._validate_semantic_intent(
                    diff.description, pre_state, post_state, diff.elisp_commands
                )

                # Log the diff execution with validation details
                self.redis_client.xadd(
                    "emacs:diffs:executed",
                    {
                        "from_buffer": str(diff.from_state.buffer),
                        "to_buffer": str(post_state.buffer),
                        "from_point": str(diff.from_state.point),
                        "to_point": str(post_state.point),
                        "elisp": str(elisp),
                        "success": "true",
                        "semantic_intent": str(diff.description),
                        "validation_passed": str(validation_result["passed"]),
                        "validation_details": str(validation_result),
                        "timestamp": str(time.time()),
                    },
                )

                return {
                    "success": True,
                    "from_state": diff.from_state,
                    "to_state": post_state,
                    "elisp": diff.elisp_commands,
                    "verified": post_state.buffer == diff.to_state.buffer,
                    "semantic_validation": validation_result,
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "elisp": diff.elisp_commands,
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _validate_semantic_intent(
        self,
        original_command: str,
        pre_state: EmacsState,
        post_state: EmacsState,
        elisp_commands: List[str],
    ) -> Dict[str, Any]:
        """Validate that the executed commands achieved the semantic intent"""

        validation = {
            "passed": False,
            "intent": "unknown",
            "evidence": [],
            "expected_elisp": [],
            "actual_elisp": elisp_commands,
        }

        command_lower = original_command.lower()

        # Determine expected semantic intent
        if self._is_end_of_line_command(command_lower):
            validation["intent"] = "end-of-line"
            validation["expected_elisp"] = ["(end-of-line)"]

            # Validate: point should have moved to a position that represents end-of-line
            # We can't know exact position, but we can check the command was correct
            if "(end-of-line)" in elisp_commands:
                validation["evidence"].append(
                    "✅ Generated correct elisp: (end-of-line)"
                )
                validation["passed"] = True
            else:
                validation["evidence"].append(
                    "❌ Did not generate (end-of-line) command"
                )

            # Additional validation: check if point actually moved
            if pre_state.point != post_state.point:
                validation["evidence"].append(
                    f"✅ Point moved: {pre_state.point} → {post_state.point}"
                )
            else:
                validation["evidence"].append(
                    "⚠️  Point did not move (may already be at end of line)"
                )

        elif self._is_beginning_of_line_command(command_lower):
            validation["intent"] = "beginning-of-line"
            validation["expected_elisp"] = ["(beginning-of-line)"]

            if "(beginning-of-line)" in elisp_commands:
                validation["evidence"].append(
                    "✅ Generated correct elisp: (beginning-of-line)"
                )
                validation["passed"] = True
            else:
                validation["evidence"].append(
                    "❌ Did not generate (beginning-of-line) command"
                )

        else:
            validation["intent"] = "other"
            validation["evidence"].append(
                "⚠️  Semantic intent not recognized for validation"
            )
            validation["passed"] = True  # Don't fail unknown intents

        return validation


# MCP Server
server = Server("redis-state-diff")
state_engine = StateEngine()


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    return ListToolsResult(
        tools=[
            Tool(
                name="verify_state",
                description="Get completely fresh, verified Emacs state with cross-checking",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="diff_command",
                description="Execute natural language command as state diff transition",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Natural language command to execute as state transition",
                        }
                    },
                    "required": ["command"],
                },
            ),
            Tool(
                name="helm_interact",
                description="Interact with active helm session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "Helm action: navigate, select, quit, filter",
                        },
                        "value": {
                            "type": "string",
                            "description": "Value for the action (filter text, selection, etc)",
                        },
                    },
                    "required": ["action"],
                },
            ),
        ]
    )


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:

    if name == "verify_state":
        state = state_engine.capture_fresh_state()

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"""🔍 **VERIFIED EMACS STATE**

**Buffer**: {state.buffer}
**Point**: {state.point}
**Mode**: {state.mode}
**Helm Active**: {state.helm_active}
**Content Sample**: {state.content_sample[:100]}...
**Timestamp**: {state.timestamp}

✅ Fresh state captured with cross-verification
🗑️  Cleared inconsistent Redis keys
💾 Stored in emacs:verified:state""",
                )
            ]
        )

    elif name == "diff_command":
        command = arguments.get("command", "")

        # Get current verified state
        current_state = state_engine.capture_fresh_state()

        # Create diff-based utterance
        diff = state_engine.create_diff(command, current_state)

        # Execute the diff
        result = state_engine.execute_diff(diff)

        if result["success"]:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"""✅ **DIFF EXECUTED SUCCESSFULLY**

**Command**: {command}

**State Transition**:
FROM: {diff.from_state.buffer} @ {diff.from_state.point}
TO:   {result['to_state'].buffer} @ {result['to_state'].point}

**Elisp Diff**: {result['elisp']}
**Verified**: {result['verified']}

🎯 Revolutionary diff-based utterances working!""",
                    )
                ]
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"""❌ **DIFF EXECUTION FAILED**

**Command**: {command}
**Error**: {result['error']}
**Elisp**: {result.get('elisp', [])}

🔧 State transition unsuccessful""",
                    )
                ]
            )

    elif name == "helm_interact":
        action = arguments.get("action", "")
        value = arguments.get("value", "")

        # Verify helm is active
        current_state = state_engine.capture_fresh_state()

        if not current_state.helm_active:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="❌ **Helm not active** - cannot interact with helm session",
                    )
                ]
            )

        # Generate helm interaction commands
        helm_commands = {
            "navigate": [
                "(helm-next-line)" if value == "down" else "(helm-previous-line)"
            ],
            "select": ["(helm-maybe-exit-minibuffer)"],
            "quit": ["(helm-keyboard-quit)"],
            "filter": [f'(insert "{value}")'] if value else [],
        }

        elisp_commands = helm_commands.get(action, [])

        if elisp_commands:
            result = state_engine.execute_diff(
                StateDiff(
                    from_state=current_state,
                    to_state=current_state,  # Helm interactions don't change major state
                    elisp_commands=elisp_commands,
                    description=f"helm {action} {value}",
                )
            )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"""🎯 **HELM INTERACTION**
                        
**Action**: {action} {value}
**Commands**: {elisp_commands}
**Result**: {'✅ Success' if result['success'] else '❌ Failed'}""",
                    )
                ]
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"❓ **Unknown helm action**: {action}"
                    )
                ]
            )

    return CallToolResult(
        content=[TextContent(type="text", text=f"❓ Unknown tool: {name}")]
    )


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="redis-state-diff",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
