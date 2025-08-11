#!/usr/bin/env python3
"""
AI-Emacs Integration MCP Server
Revolutionary AI-Emacs integration with Redis coordination backbone
Based on architecture document: AI_EMACS_ARCHITECTURE.org
"""

import asyncio
import json
import redis
import subprocess
import re
import time
from typing import Any, Dict, List, Optional, Tuple
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
    ImageContent,
    EmbeddedResource,
)


@dataclass
class AIAgent:
    """Base class for AI agents in the system"""

    name: str
    agent_type: str
    redis_streams: List[str]
    primary_function: str

    def __post_init__(self):
        self.active = True
        self.last_activity = time.time()


class RedisCoordinator:
    """Redis coordination backbone for multi-AI system"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.streams = {
            "content": "emacs:content",
            "analysis": "ai:analysis",
            "patterns": "ai:patterns",
            "context": "ai:context",
            "execution": "ai:execute",
        }
        self.agents = {}

    async def initialize_streams(self):
        """Initialize Redis streams for coordination"""
        for stream_name, stream_key in self.streams.items():
            try:
                # Create stream if it doesn't exist
                self.redis.xadd(stream_key, {"initialized": "true"}, maxlen=1000)
            except Exception as e:
                print(f"Warning: Could not initialize stream {stream_key}: {e}")

    async def publish_content_change(
        self, buffer_name: str, content: str, position: int
    ):
        """Publish content changes to coordination layer"""
        try:
            self.redis.xadd(
                self.streams["content"],
                {
                    "buffer": buffer_name,
                    "content": content[:1000],  # Limit content size
                    "position": position,
                    "timestamp": str(time.time()),
                    "event_type": "content_change",
                },
            )
        except Exception as e:
            print(f"Warning: Could not publish content change: {e}")

    async def register_agent(self, agent: AIAgent):
        """Register an AI agent with the coordinator"""
        self.agents[agent.name] = agent
        try:
            self.redis.hset(
                "ai:agents",
                agent.name,
                json.dumps(
                    {
                        "type": agent.agent_type,
                        "streams": agent.redis_streams,
                        "function": agent.primary_function,
                        "active": agent.active,
                        "registered": str(time.time()),
                    }
                ),
            )
        except Exception as e:
            print(f"Warning: Could not register agent {agent.name}: {e}")

    async def coordinate_agents(
        self, analysis_request: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Coordinate multiple AI agents for analysis"""
        results = []

        # Simple coordination - in production this would be more sophisticated
        for agent_name, agent in self.agents.items():
            if agent.active:
                try:
                    # Publish analysis request
                    self.redis.xadd(
                        self.streams["analysis"],
                        {
                            "request_id": analysis_request.get("id", "unknown"),
                            "agent_target": agent_name,
                            "content": json.dumps(analysis_request),
                            "timestamp": str(time.time()),
                        },
                    )

                    # For this implementation, we'll simulate agent response
                    # In production, agents would read from streams and respond
                    results.append(
                        {
                            "agent": agent_name,
                            "status": "requested",
                            "timestamp": time.time(),
                        }
                    )
                except Exception as e:
                    print(f"Warning: Could not coordinate agent {agent_name}: {e}")

        return results


class AIWorkspaceManager:
    """Manages AI workspace buffer and real-time sync"""

    def __init__(self, redis_coordinator: RedisCoordinator):
        self.coordinator = redis_coordinator
        self.workspace_buffer = "*AI-Workspace*"
        self.last_sync = time.time()

    async def create_workspace(self) -> Dict[str, Any]:
        """Create and configure AI workspace buffer"""
        elisp_commands = [
            f'(get-buffer-create "{self.workspace_buffer}")',
            f'(with-current-buffer "{self.workspace_buffer}"',
            "  (ai-workspace-mode)",
            '  (insert "AI-Emacs Integration Workspace\\n")',
            '  (insert "=================================\\n\\n")',
            '  (insert "This buffer provides real-time AI collaboration\\n")',
            '  (insert "Commands:\\n")',
            '  (insert "  C-c a - Accept AI suggestion\\n")',
            '  (insert "  C-c r - Reject AI suggestion\\n")',
            '  (insert "  C-c s - Sync with AI system\\n\\n"))',
            "(split-window-right)",
            f'(switch-to-buffer "{self.workspace_buffer}")',
        ]

        return await self._execute_elisp_sequence(elisp_commands)

    async def sync_content(self, buffer_name: str) -> Dict[str, Any]:
        """Sync buffer content with AI system"""
        try:
            # Get current buffer content and position
            elisp_query = f"""
(with-current-buffer "{buffer_name}"
  (list (buffer-substring-no-properties (point-min) (point-max))
        (point)
        (buffer-name)))
"""

            result = subprocess.run(
                ["emacsclient", "--eval", elisp_query],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                # Parse elisp list result
                content_data = result.stdout.strip()

                # Publish to coordination layer
                await self.coordinator.publish_content_change(
                    buffer_name, content_data, int(time.time())
                )

                self.last_sync = time.time()
                return {
                    "success": True,
                    "buffer": buffer_name,
                    "synced_at": self.last_sync,
                    "content_preview": (
                        content_data[:100] + "..."
                        if len(content_data) > 100
                        else content_data
                    ),
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_elisp_sequence(
        self, elisp_commands: List[str]
    ) -> Dict[str, Any]:
        """Execute elisp commands safely"""
        try:
            combined_elisp = "(progn " + " ".join(elisp_commands) + ")"

            result = subprocess.run(
                ["emacsclient", "--eval", combined_elisp],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "result": result.stdout.strip(),
                    "commands_executed": len(elisp_commands),
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}


class DocumentMonitor:
    """Monitor org documents for changes and trigger recursive development"""

    def __init__(self, redis_coordinator: RedisCoordinator):
        self.coordinator = redis_coordinator
        self.watched_docs = ["AI_EMACS_ARCHITECTURE.org"]
        self.last_modified = {}

    async def check_updates(self) -> Dict[str, Any]:
        """Check for document updates and trigger development"""
        updates = []

        for doc in self.watched_docs:
            try:
                # Check file modification time
                import os

                if os.path.exists(doc):
                    current_mtime = os.path.getmtime(doc)
                    last_mtime = self.last_modified.get(doc, 0)

                    if current_mtime > last_mtime:
                        self.last_modified[doc] = current_mtime
                        updates.append(
                            {
                                "document": doc,
                                "modified": current_mtime,
                                "needs_processing": True,
                            }
                        )

                        # Trigger recursive development
                        await self._trigger_recursive_development(doc)

            except Exception as e:
                print(f"Warning: Could not check {doc}: {e}")

        return {
            "documents_checked": len(self.watched_docs),
            "updates_found": len(updates),
            "updates": updates,
        }

    async def _trigger_recursive_development(self, document: str):
        """Trigger recursive development based on document changes"""
        try:
            self.coordinator.redis.xadd(
                "ai:recursive_dev",
                {
                    "document": document,
                    "trigger": "document_updated",
                    "timestamp": str(time.time()),
                    "action": "analyze_and_implement",
                },
            )
        except Exception as e:
            print(f"Warning: Could not trigger recursive development: {e}")


class AIEmacsIntegrationServer:
    """Main AI-Emacs integration server"""

    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.coordinator = RedisCoordinator(self.redis_client)
        self.workspace_manager = AIWorkspaceManager(self.coordinator)
        self.document_monitor = DocumentMonitor(self.coordinator)

        # Initialize AI agents
        self.agents = [
            AIAgent(
                "code_analyzer",
                "analysis",
                ["emacs:content", "ai:analysis"],
                "Real-time code analysis and syntax insights",
            ),
            AIAgent(
                "workflow_learner",
                "learning",
                ["ai:patterns"],
                "Pattern recognition and workflow prediction",
            ),
            AIAgent(
                "context_manager",
                "memory",
                ["ai:context"],
                "Cross-session memory and context injection",
            ),
            AIAgent(
                "documentation_engine",
                "docs",
                ["ai:execute", "docs:update"],
                "Self-updating documentation generation",
            ),
        ]

    async def initialize(self):
        """Initialize the AI-Emacs integration system"""
        try:
            # Initialize Redis streams
            await self.coordinator.initialize_streams()

            # Register AI agents
            for agent in self.agents:
                await self.coordinator.register_agent(agent)

            # Install AI workspace mode in Emacs
            await self._install_ai_workspace_mode()

            print("AI-Emacs Integration Server initialized successfully")
            return True

        except Exception as e:
            print(f"Initialization failed: {e}")
            return False

    async def _install_ai_workspace_mode(self):
        """Install AI workspace mode in Emacs"""
        elisp_mode_definition = """
(define-minor-mode ai-workspace-mode
  "Minor mode for AI collaboration workspace"
  :lighter " AI"
  :keymap (let ((map (make-sparse-keymap)))
            (define-key map (kbd "C-c a") 'ai-accept-suggestion)
            (define-key map (kbd "C-c r") 'ai-reject-suggestion)
            (define-key map (kbd "C-c s") 'ai-sync-content)
            map))

(defun ai-accept-suggestion ()
  "Accept current AI suggestion"
  (interactive)
  (message "AI suggestion accepted"))

(defun ai-reject-suggestion ()
  "Reject current AI suggestion"  
  (interactive)
  (message "AI suggestion rejected"))

(defun ai-sync-content ()
  "Sync current buffer with AI system"
  (interactive)
  (message "Syncing with AI system..."))
"""

        try:
            subprocess.run(
                ["emacsclient", "--eval", elisp_mode_definition],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception as e:
            print(f"Warning: Could not install AI workspace mode: {e}")


# MCP Server Setup
server = Server("ai-emacs-integration")
ai_emacs_server = AIEmacsIntegrationServer()


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available AI-Emacs integration tools"""
    return ListToolsResult(
        tools=[
            Tool(
                name="create_ai_workspace",
                description="Create AI collaboration workspace buffer in Emacs",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="sync_buffer_content",
                description="Sync Emacs buffer content with AI coordination system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "buffer_name": {
                            "type": "string",
                            "description": "Name of buffer to sync (default: current buffer)",
                        }
                    },
                },
            ),
            Tool(
                name="coordinate_ai_analysis",
                description="Coordinate multiple AI agents for code analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Content to analyze",
                        },
                        "analysis_type": {
                            "type": "string",
                            "description": "Type of analysis (syntax, patterns, context, documentation)",
                        },
                    },
                    "required": ["content"],
                },
            ),
            Tool(
                name="monitor_documents",
                description="Monitor org documents for changes and trigger recursive development",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="query_redis_streams",
                description="Query Redis coordination streams for AI activity",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "stream_name": {
                            "type": "string",
                            "description": "Stream to query (content, analysis, patterns, context, execution)",
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of recent entries to retrieve (default: 10)",
                        },
                    },
                },
            ),
        ]
    )


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
    """Handle AI-Emacs integration tool calls"""

    # Initialize server if not already done
    if not hasattr(ai_emacs_server, "_initialized"):
        await ai_emacs_server.initialize()
        ai_emacs_server._initialized = True

    if name == "create_ai_workspace":
        result = await ai_emacs_server.workspace_manager.create_workspace()

        if result["success"]:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"✅ AI Workspace created successfully!\n\nBuffer: {ai_emacs_server.workspace_manager.workspace_buffer}\nCommands executed: {result['commands_executed']}\n\nAI collaboration workspace is now active with real-time sync capabilities.",
                    )
                ]
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"❌ Failed to create AI workspace: {result['error']}",
                    )
                ]
            )

    elif name == "sync_buffer_content":
        buffer_name = arguments.get("buffer_name", "*scratch*")
        result = await ai_emacs_server.workspace_manager.sync_content(buffer_name)

        if result["success"]:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"✅ Buffer synced with AI system!\n\nBuffer: {result['buffer']}\nSynced at: {result['synced_at']}\nContent preview: {result['content_preview']}",
                    )
                ]
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"❌ Sync failed: {result['error']}")
                ]
            )

    elif name == "coordinate_ai_analysis":
        content = arguments.get("content", "")
        analysis_type = arguments.get("analysis_type", "general")

        analysis_request = {
            "id": str(int(time.time())),
            "content": content,
            "type": analysis_type,
            "timestamp": time.time(),
        }

        results = await ai_emacs_server.coordinator.coordinate_agents(analysis_request)

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"✅ AI analysis coordination initiated!\n\nRequest ID: {analysis_request['id']}\nAnalysis type: {analysis_type}\nAgents notified: {len(results)}\n\nActive agents:\n"
                    + "\n".join([f"- {r['agent']}: {r['status']}" for r in results]),
                )
            ]
        )

    elif name == "monitor_documents":
        result = await ai_emacs_server.document_monitor.check_updates()

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"✅ Document monitoring complete!\n\nDocuments checked: {result['documents_checked']}\nUpdates found: {result['updates_found']}\n\nUpdates:\n"
                    + "\n".join(
                        [
                            f"- {u['document']}: {'Needs processing' if u['needs_processing'] else 'Up to date'}"
                            for u in result["updates"]
                        ]
                    ),
                )
            ]
        )

    elif name == "query_redis_streams":
        stream_name = arguments.get("stream_name", "content")
        count = arguments.get("count", 10)

        try:
            stream_key = ai_emacs_server.coordinator.streams.get(
                stream_name, f"ai:{stream_name}"
            )
            entries = ai_emacs_server.redis_client.xrevrange(stream_key, count=count)

            if entries:
                formatted_entries = []
                for entry_id, fields in entries:
                    formatted_entries.append(
                        f"ID: {entry_id}\n  "
                        + "\n  ".join([f"{k}: {v}" for k, v in fields.items()])
                    )

                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"✅ Redis stream query results for '{stream_name}':\n\n"
                            + "\n\n".join(formatted_entries),
                        )
                    ]
                )
            else:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"No entries found in stream '{stream_name}'",
                        )
                    ]
                )
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"❌ Stream query failed: {str(e)}")
                ]
            )

    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")]
        )


async def main():
    """Run the AI-Emacs integration MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ai-emacs-integration",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
