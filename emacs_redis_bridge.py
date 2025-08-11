#!/usr/bin/env python3
"""
Emacs-Redis Bridge - Real-time bridge between Emacs and Redis AI system
Enables bidirectional communication and real-time event streaming
"""

import redis
import json
import asyncio
import websockets
import threading
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import subprocess
import os
from pathlib import Path


@dataclass
class EmacsEvent:
    """Event from Emacs to Redis AI system"""

    event_type: str
    data: Dict[str, Any]
    buffer_name: str
    file_path: Optional[str]
    timestamp: float


@dataclass
class RedisEvent:
    """Event from Redis AI system to Emacs"""

    event_type: str
    data: Dict[str, Any]
    target_buffer: Optional[str]
    timestamp: float


class EmacsRedisEventBridge:
    """Bridge between Emacs and Redis AI workforce system"""

    def __init__(self, redis_host="localhost", redis_port=6379, emacs_port=8882):
        self.redis_client = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )
        self.emacs_port = emacs_port
        self.running = False
        self.emacs_connections = set()

        # Event queues
        self.emacs_to_redis_queue = asyncio.Queue()
        self.redis_to_emacs_queue = asyncio.Queue()

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def start_bridge(self):
        """Start the bridge server"""
        self.running = True
        self.logger.info(f"Starting Emacs-Redis bridge on port {self.emacs_port}")

        # Start WebSocket server for Emacs connections
        start_server = websockets.serve(
            self.handle_emacs_connection, "localhost", self.emacs_port
        )

        # Start Redis monitoring
        redis_task = asyncio.create_task(self.monitor_redis_events())

        # Start event processing
        processing_task = asyncio.create_task(self.process_events())

        # Run the server
        await asyncio.gather(start_server, redis_task, processing_task)

    async def handle_emacs_connection(self, websocket, path):
        """Handle WebSocket connection from Emacs"""
        self.emacs_connections.add(websocket)
        self.logger.info(f"Emacs connected: {websocket.remote_address}")

        try:
            async for message in websocket:
                try:
                    event_data = json.loads(message)
                    emacs_event = EmacsEvent(
                        event_type=event_data["event_type"],
                        data=event_data["data"],
                        buffer_name=event_data.get("buffer_name", ""),
                        file_path=event_data.get("file_path"),
                        timestamp=time.time(),
                    )
                    await self.emacs_to_redis_queue.put(emacs_event)
                    self.logger.info(f"Received Emacs event: {emacs_event.event_type}")

                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON from Emacs: {e}")

        except websockets.exceptions.ConnectionClosed:
            self.logger.info("Emacs connection closed")
        finally:
            self.emacs_connections.remove(websocket)

    async def monitor_redis_events(self):
        """Monitor Redis for events to send to Emacs"""
        while self.running:
            try:
                # Check for work completion notifications
                work_result = self.redis_client.blpop(["work_completed"], timeout=1)
                if work_result:
                    _, result_data = work_result
                    try:
                        result = json.loads(result_data)
                        redis_event = RedisEvent(
                            event_type="work_completed",
                            data=result,
                            target_buffer=result.get("buffer_name"),
                            timestamp=time.time(),
                        )
                        await self.redis_to_emacs_queue.put(redis_event)
                    except json.JSONDecodeError:
                        self.logger.error(
                            f"Invalid work completion data: {result_data}"
                        )

                # Check for agent status updates
                status_result = self.redis_client.blpop(
                    ["agent_status_updates"], timeout=1
                )
                if status_result:
                    _, status_data = status_result
                    try:
                        status = json.loads(status_data)
                        redis_event = RedisEvent(
                            event_type="agent_status",
                            data=status,
                            target_buffer=None,
                            timestamp=time.time(),
                        )
                        await self.redis_to_emacs_queue.put(redis_event)
                    except json.JSONDecodeError:
                        self.logger.error(f"Invalid status data: {status_data}")

                # Check for Lisp execution results
                lisp_result = self.redis_client.blpop(["lisp_results"], timeout=1)
                if lisp_result:
                    _, lisp_data = lisp_result
                    try:
                        result = json.loads(lisp_data)
                        redis_event = RedisEvent(
                            event_type="lisp_result",
                            data=result,
                            target_buffer=result.get("buffer_name"),
                            timestamp=time.time(),
                        )
                        await self.redis_to_emacs_queue.put(redis_event)
                    except json.JSONDecodeError:
                        self.logger.error(f"Invalid Lisp result: {lisp_data}")

            except Exception as e:
                self.logger.error(f"Error monitoring Redis: {e}")
                await asyncio.sleep(1)

    async def process_events(self):
        """Process events in both directions"""
        while self.running:
            # Process Emacs to Redis events
            try:
                emacs_event = await asyncio.wait_for(
                    self.emacs_to_redis_queue.get(), timeout=0.1
                )
                await self.handle_emacs_event(emacs_event)
            except asyncio.TimeoutError:
                pass

            # Process Redis to Emacs events
            try:
                redis_event = await asyncio.wait_for(
                    self.redis_to_emacs_queue.get(), timeout=0.1
                )
                await self.send_to_emacs(redis_event)
            except asyncio.TimeoutError:
                pass

    async def handle_emacs_event(self, event: EmacsEvent):
        """Handle event from Emacs"""
        try:
            if event.event_type == "assign_work":
                # Assign work to AI agent
                work_data = {
                    "task_type": event.data.get("task_type", "custom"),
                    "description": event.data["description"],
                    "target_files": event.data.get("target_files", []),
                    "buffer_name": event.buffer_name,
                    "priority": event.data.get("priority", 5),
                    "estimated_duration": event.data.get("duration", 30),
                }

                agent_id = event.data.get("agent_id", "test_agent_01")
                self.redis_client.lpush(f"agent_work:{agent_id}", json.dumps(work_data))
                self.logger.info(
                    f"Assigned work to {agent_id}: {work_data['description']}"
                )

            elif event.event_type == "execute_lisp":
                # Execute Lisp code via MCP server
                lisp_code = event.data["code"]
                request_id = f"emacs_{int(time.time())}"

                mcp_request = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "execute_lisp",
                        "arguments": {"code": lisp_code},
                    },
                    "id": request_id,
                }

                self.redis_client.lpush("mcp_requests", json.dumps(mcp_request))
                self.logger.info(f"Executing Lisp: {lisp_code}")

            elif event.event_type == "natural_command":
                # Process natural language command
                command = event.data["command"]
                context = {
                    "buffer_name": event.buffer_name,
                    "file_path": event.file_path,
                    "command": command,
                    "timestamp": event.timestamp,
                }

                self.redis_client.lpush("natural_commands", json.dumps(context))
                self.logger.info(f"Natural command: {command}")

            elif event.event_type == "file_changed":
                # Notify about file changes
                change_data = {
                    "file_path": event.file_path,
                    "buffer_name": event.buffer_name,
                    "change_type": event.data.get("change_type", "saved"),
                    "timestamp": event.timestamp,
                }

                self.redis_client.lpush("file_changes", json.dumps(change_data))
                self.logger.info(f"File changed: {event.file_path}")

            elif event.event_type == "request_completion":
                # Request AI completion
                completion_request = {
                    "symbol": event.data["symbol"],
                    "context": event.data["context"],
                    "buffer_name": event.buffer_name,
                    "file_path": event.file_path,
                    "timestamp": event.timestamp,
                }

                self.redis_client.lpush(
                    "completion_requests", json.dumps(completion_request)
                )
                self.logger.info(f"Completion request: {event.data['symbol']}")

        except Exception as e:
            self.logger.error(f"Error handling Emacs event: {e}")

    async def send_to_emacs(self, event: RedisEvent):
        """Send event to all connected Emacs instances"""
        if not self.emacs_connections:
            return

        message = json.dumps(asdict(event))
        disconnected = set()

        for websocket in self.emacs_connections:
            try:
                await websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(websocket)
            except Exception as e:
                self.logger.error(f"Error sending to Emacs: {e}")
                disconnected.add(websocket)

        # Clean up disconnected connections
        self.emacs_connections -= disconnected

    def start_emacs_integration(self):
        """Start the Emacs integration in a separate thread"""

        def run_emacs_server():
            # Create simple HTTP server for Emacs to connect to
            import http.server
            import socketserver

            class EmacsHandler(http.server.SimpleHTTPRequestHandler):
                def do_POST(self):
                    content_length = int(self.headers["Content-Length"])
                    post_data = self.rfile.read(content_length)

                    try:
                        event_data = json.loads(post_data.decode("utf-8"))
                        # Process the event
                        self.send_response(200)
                        self.send_header("Content-type", "application/json")
                        self.end_headers()
                        self.wfile.write(b'{"status": "received"}')
                    except Exception as e:
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(f'{{"error": "{str(e)}"}}'.encode())

            with socketserver.TCPServer(("", self.emacs_port), EmacsHandler) as httpd:
                self.logger.info(
                    f"Emacs HTTP server listening on port {self.emacs_port}"
                )
                httpd.serve_forever()

        thread = threading.Thread(target=run_emacs_server, daemon=True)
        thread.start()
        return thread


class RedisLispExecutor:
    """Execute Lisp commands from Emacs via Redis"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def execute_lisp_command(
        self, command: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a Lisp command and return results"""
        try:
            # Store command in Redis for MCP server to process
            request = {
                "command": command,
                "context": context,
                "timestamp": time.time(),
                "request_id": f"lisp_{int(time.time())}",
            }

            self.redis.lpush("lisp_commands", json.dumps(request))

            # Wait for result (in a real implementation, this would be async)
            result_key = f"lisp_result:{request['request_id']}"

            # Poll for result with timeout
            for _ in range(50):  # 5 second timeout
                result = self.redis.get(result_key)
                if result:
                    self.redis.delete(result_key)
                    return json.loads(result)
                time.sleep(0.1)

            return {"error": "Timeout waiting for Lisp execution"}

        except Exception as e:
            return {"error": f"Lisp execution failed: {str(e)}"}


def create_emacs_lisp_installer():
    """Create installation script for the Emacs mode"""
    install_script = """#!/bin/bash
# Install Redis AI Emacs Mode

EMACS_CONFIG_DIR="$HOME/.emacs.d"
REDIS_AI_DIR="$EMACS_CONFIG_DIR/redis-ai"

echo "🚀 Installing Redis AI Emacs Mode..."

# Create directory
mkdir -p "$REDIS_AI_DIR"

# Copy the mode file
cp redis-ai-emacs-mode.el "$REDIS_AI_DIR/"

# Add to Emacs configuration
INIT_FILE="$EMACS_CONFIG_DIR/init.el"
CONFIG_ENTRY="
;; Redis AI Workforce Integration
(add-to-list 'load-path \"$REDIS_AI_DIR\")
(require 'redis-ai-emacs-mode)
(redis-ai-global-mode-enable)
"

if ! grep -q "redis-ai-emacs-mode" "$INIT_FILE" 2>/dev/null; then
    echo "$CONFIG_ENTRY" >> "$INIT_FILE"
    echo "✅ Added Redis AI mode to Emacs configuration"
else
    echo "✅ Redis AI mode already configured"
fi

echo "🎉 Installation complete!"
echo ""
echo "Usage in Emacs:"
echo "  M-x redis-ai-mode    - Enable in current buffer"
echo "  C-c r c              - Connect to Redis"
echo "  C-c r t              - Generate tests"
echo "  C-c r o              - Generate documentation"
echo "  C-c r l              - Execute Lisp"
echo "  C-c r n              - Natural language command"
echo "  C-c r D              - Show dashboard"
echo ""
echo "Restart Emacs to complete installation."
"""

    with open("install_redis_ai_emacs.sh", "w") as f:
        f.write(install_script)

    os.chmod("install_redis_ai_emacs.sh", 0o755)
    print("✅ Created install_redis_ai_emacs.sh")


async def main():
    """Main entry point"""
    bridge = EmacsRedisEventBridge()

    # Create installer script
    create_emacs_lisp_installer()

    try:
        print("🌉 Starting Emacs-Redis Bridge...")
        print("Connect from Emacs with: M-x redis-ai-mode, then C-c r c")
        await bridge.start_bridge()
    except KeyboardInterrupt:
        print("\n🛑 Stopping bridge...")
        bridge.running = False


if __name__ == "__main__":
    asyncio.run(main())
