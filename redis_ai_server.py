#!/usr/bin/env python3
"""
Redis AI Server - Production persistent server for the Redis AI development platform
Runs forever as a proper server with web dashboard, API endpoints, and service management
"""

import asyncio
import logging
import signal
import sys
import time
import json
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Web server imports
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import redis

# Internal components
from always_on_ai_workforce import PersistentBackgroundAgent, BackgroundTaskType
from ai_execution_engine import RealAIWorkforceEngine
from claude_api_integration import ClaudeCodeIntegration
from mcp_tool_composition import MCPToolExecutor


@dataclass
class ServerStatus:
    """Server status information"""

    uptime: float
    active_agents: int
    completed_work: int
    failed_work: int
    redis_connected: bool
    claude_available: bool
    memory_usage: float
    cpu_usage: float


class RedisAIServer:
    """Production Redis AI Server"""

    def __init__(
        self, host="0.0.0.0", port=8883, redis_host="localhost", redis_port=6379
    ):
        self.host = host
        self.port = port
        self.start_time = time.time()
        self.running = False

        # Setup logging
        self.logger = self._setup_logging()

        # Redis connection
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )

        # Core components
        self.ai_engine = RealAIWorkforceEngine(self.redis)
        self.claude_integration = ClaudeCodeIntegration(self.redis)
        self.mcp_executor = MCPToolExecutor(self.redis)

        # Active agents
        self.agents: Dict[str, PersistentBackgroundAgent] = {}
        self.agent_threads: Dict[str, threading.Thread] = {}

        # Web interface
        self.app = Flask(__name__, template_folder="templates", static_folder="static")
        self.app.config["SECRET_KEY"] = "redis-ai-server-secret-key"
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Setup routes
        self._setup_routes()
        self._setup_websocket_handlers()

        # Signal handling (only in main thread)
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except ValueError:
            # Not in main thread, ignore signal handling
            pass

        self.logger.info("Redis AI Server initialized")

    def _setup_logging(self):
        """Setup server logging"""

        log_dir = Path.home() / ".redis-ai-logs"
        log_dir.mkdir(exist_ok=True)

        logger = logging.getLogger("redis_ai_server")
        logger.setLevel(logging.INFO)

        # File handler
        handler = logging.FileHandler(log_dir / "server.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route("/")
        def dashboard():
            """Main dashboard"""
            return render_template("dashboard.html")

        @self.app.route("/api/status")
        def api_status():
            """Get server status"""
            status = self._get_server_status()
            return jsonify(asdict(status))

        @self.app.route("/api/agents")
        def api_agents():
            """Get agent information"""
            agents_info = []
            for agent_id, agent in self.agents.items():
                agents_info.append(
                    {
                        "id": agent_id,
                        "specialty": agent.specialty.value,
                        "status": (
                            "running" if agent_id in self.agent_threads else "stopped"
                        ),
                        "work_completed": getattr(
                            agent.work_session, "work_units_completed", 0
                        ),
                        "current_work": getattr(agent, "current_work", None),
                    }
                )
            return jsonify(agents_info)

        @self.app.route("/api/work/assign", methods=["POST"])
        def api_assign_work():
            """Assign work to an agent"""
            data = request.json

            try:
                agent_id = data.get("agent_id", "test_agent_01")
                task_type = data.get("task_type", "test_generation")
                description = data.get("description", "API assigned work")
                target_files = data.get("target_files", [])
                priority = data.get("priority", 5)

                work_data = {
                    "task_type": task_type,
                    "description": description,
                    "target_files": target_files,
                    "priority": priority,
                    "estimated_duration": 30,
                }

                self.redis.lpush(f"agent_work:{agent_id}", json.dumps(work_data))

                # Broadcast to websocket clients
                self.socketio.emit(
                    "work_assigned", {"agent_id": agent_id, "description": description}
                )

                return jsonify(
                    {"success": True, "message": f"Work assigned to {agent_id}"}
                )

            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 400

        @self.app.route("/api/lisp/execute", methods=["POST"])
        def api_execute_lisp():
            """Execute Lisp code via MCP server"""
            data = request.json

            try:
                lisp_code = data.get("code", '["print", "Hello from API"]')

                # Store in Redis for MCP server
                mcp_request = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "execute_lisp",
                        "arguments": {"code": lisp_code},
                    },
                    "id": f"api_{int(time.time())}",
                }

                self.redis.lpush("mcp_requests", json.dumps(mcp_request))

                return jsonify(
                    {"success": True, "message": "Lisp code queued for execution"}
                )

            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 400

        @self.app.route("/api/compositions")
        def api_compositions():
            """Get available MCP tool compositions"""
            compositions = self.mcp_executor.list_compositions()
            return jsonify(compositions)

        @self.app.route("/api/compositions/<name>/execute", methods=["POST"])
        def api_execute_composition(name):
            """Execute an MCP tool composition"""
            data = request.json or {}

            # Queue for async execution
            asyncio.create_task(self._execute_composition_async(name, data))

            return jsonify(
                {"success": True, "message": f"Composition {name} queued for execution"}
            )

        @self.app.route("/api/logs/<agent_id>")
        def api_agent_logs(agent_id):
            """Get agent logs"""
            log_file = Path.home() / ".redis-ai-logs" / f"{agent_id}.log"

            if log_file.exists():
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    return jsonify({"logs": lines[-100:]})  # Last 100 lines
            else:
                return jsonify({"logs": []})

    def _setup_websocket_handlers(self):
        """Setup WebSocket event handlers"""

        @self.socketio.on("connect")
        def handle_connect():
            self.logger.info(f"Client connected: {request.sid}")
            emit("status", asdict(self._get_server_status()))

        @self.socketio.on("disconnect")
        def handle_disconnect():
            self.logger.info(f"Client disconnected: {request.sid}")

        @self.socketio.on("start_agent")
        def handle_start_agent(data):
            """
            Handles the start agent event by initializing a new agent thread.

            This function processes a start agent request by extracting the agent ID and specialty
            from the provided data, then starts a new agent thread if the agent doesn't already exist.
            Upon successful agent creation, it emits an 'agent_started' event.

            Args:
                data (dict): A dictionary containing agent configuration data with the following keys:
                    - agent_id (str): Unique identifier for the agent to start
                    - specialty (str, optional): The agent's specialty area. Defaults to 'test_generation'

            Returns:
                None: This function doesn't return a value but has the side effect of starting
                an agent thread and emitting an event.

            Raises:
                No explicit exceptions are raised by this function, though underlying methods
                like _start_agent() may raise exceptions.

            Example:
                >>> data = {'agent_id': 'agent_001', 'specialty': 'code_review'}
                >>> handle_start_agent(data)
                # Agent thread started and 'agent_started' event emitted

            Note:
                The function only starts an agent if the agent_id is provided and the agent
                is not already running (not in self.agent_threads).
            """
            agent_id = data.get("agent_id")
            specialty = data.get("specialty", "test_generation")

            if agent_id and agent_id not in self.agent_threads:
                self._start_agent(agent_id, specialty)
                emit("agent_started", {"agent_id": agent_id})

        @self.socketio.on("stop_agent")
        def handle_stop_agent(data):
            """Handle stop agent socket event

            Stops a running AI agent by agent ID.

            Args:
                data: Dictionary containing agent_id to stop
            """
            agent_id = data.get("agent_id")

            if agent_id in self.agent_threads:
                self._stop_agent(agent_id)
                emit("agent_stopped", {"agent_id": agent_id})

    async def _execute_composition_async(self, name: str, context: Dict[str, Any]):
        """Execute MCP composition asynchronously"""
        try:
            result = await self.mcp_executor.execute_composition(name, context)

            # Broadcast result to websocket clients
            self.socketio.emit(
                "composition_completed",
                {
                    "name": name,
                    "success": result["success"],
                    "artifacts": result.get("artifacts", []),
                    "errors": result.get("errors", []),
                },
            )

        except Exception as e:
            self.logger.error(f"Error executing composition {name}: {e}")
            self.socketio.emit("composition_error", {"name": name, "error": str(e)})

    def _get_server_status(self) -> ServerStatus:
        """Get current server status"""

        try:
            # Test Redis connection
            self.redis.ping()
            redis_connected = True
        except:
            redis_connected = False

        return ServerStatus(
            uptime=time.time() - self.start_time,
            active_agents=len([t for t in self.agent_threads.values() if t.is_alive()]),
            completed_work=len(self.redis.keys("work_unit:*")),
            failed_work=0,  # TODO: Track failed work
            redis_connected=redis_connected,
            claude_available=self.claude_integration.claude_code_available,
            memory_usage=0.0,  # TODO: Get actual memory usage
            cpu_usage=0.0,  # TODO: Get actual CPU usage
        )

    def _start_agent(self, agent_id: str, specialty: str):
        """Start a background agent"""

        try:
            # Convert specialty string to enum
            if specialty == "test_generation":
                task_type = BackgroundTaskType.TEST_GENERATION
            elif specialty == "documentation":
                task_type = BackgroundTaskType.DOCUMENTATION
            elif specialty == "code_quality":
                task_type = BackgroundTaskType.CODE_QUALITY
            else:
                task_type = BackgroundTaskType.TEST_GENERATION

            # Create agent
            agent = PersistentBackgroundAgent(agent_id, task_type, self.redis)
            self.agents[agent_id] = agent

            # Start agent thread
            thread = threading.Thread(target=agent.start_background_work, daemon=True)
            thread.start()
            self.agent_threads[agent_id] = thread

            self.logger.info(f"Started agent {agent_id} with specialty {specialty}")

        except Exception as e:
            self.logger.error(f"Error starting agent {agent_id}: {e}")

    def _stop_agent(self, agent_id: str):
        """Stop a background agent"""

        try:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.shutdown_requested = True

                # Wait for thread to finish
                if agent_id in self.agent_threads:
                    thread = self.agent_threads[agent_id]
                    thread.join(timeout=5)
                    del self.agent_threads[agent_id]

                del self.agents[agent_id]

                self.logger.info(f"Stopped agent {agent_id}")

        except Exception as e:
            self.logger.error(f"Error stopping agent {agent_id}: {e}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()

    def start_default_agents(self):
        """Start default set of agents"""

        default_agents = [
            ("test_agent_01", "test_generation"),
            ("doc_agent_01", "documentation"),
            ("quality_agent_01", "code_quality"),
        ]

        for agent_id, specialty in default_agents:
            self._start_agent(agent_id, specialty)

        self.logger.info(f"Started {len(default_agents)} default agents")

    async def start_background_monitoring(self):
        """Start background monitoring tasks"""

        while self.running:
            try:
                # Broadcast status updates to connected clients
                status = self._get_server_status()
                self.socketio.emit("status_update", asdict(status))

                # Monitor agent health
                for agent_id, thread in list(self.agent_threads.items()):
                    if not thread.is_alive():
                        self.logger.warning(
                            f"Agent {agent_id} thread died, restarting..."
                        )
                        del self.agent_threads[agent_id]
                        if agent_id in self.agents:
                            specialty = self.agents[agent_id].specialty.value
                            self._start_agent(agent_id, specialty)

                await asyncio.sleep(10)  # Update every 10 seconds

            except Exception as e:
                self.logger.error(f"Error in background monitoring: {e}")
                await asyncio.sleep(10)

    def run(self):
        """Run the server"""

        self.logger.info(f"Starting Redis AI Server on {self.host}:{self.port}")
        self.running = True

        # Test Redis connection
        try:
            self.redis.ping()
            self.logger.info("✅ Redis connection established")
        except Exception as e:
            self.logger.error(f"❌ Redis connection failed: {e}")
            return

        # Test Claude integration
        if self.claude_integration.claude_code_available:
            self.logger.info("✅ Claude Code integration available")
        else:
            self.logger.warning("⚠️ Claude Code not available, using template fallbacks")

        # Start default agents
        self.start_default_agents()

        # Start background monitoring in a separate thread
        monitoring_thread = threading.Thread(
            target=self._run_monitoring_loop, daemon=True
        )
        monitoring_thread.start()

        try:
            # Run the web server
            self.logger.info(
                f"🌐 Web dashboard available at http://{self.host}:{self.port}"
            )
            self.logger.info("🤖 AI workforce is now running persistently")
            self.logger.info("🔄 Server will run forever until stopped")

            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=False,
                allow_unsafe_werkzeug=True,
            )

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            self.shutdown()

    def _run_monitoring_loop(self):
        """Run monitoring in a background thread with its own event loop"""
        asyncio.run(self.start_background_monitoring())

    def shutdown(self):
        """Shutdown the server gracefully"""

        self.logger.info("Shutting down Redis AI Server...")
        self.running = False

        # Stop all agents
        for agent_id in list(self.agents.keys()):
            self._stop_agent(agent_id)

        # Close Redis connection
        try:
            self.redis.close()
        except:
            pass

        self.logger.info("Redis AI Server shutdown complete")
        sys.exit(0)


def create_web_dashboard_template():
    """Create the web dashboard HTML template"""

    template_dir = Path("templates")
    template_dir.mkdir(exist_ok=True)

    dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Redis AI Server Dashboard</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            color: #333;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .agents-section, .work-section, .lisp-section {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .agent-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border: 1px solid #eee;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .agent-running {
            border-left: 4px solid #4CAF50;
        }
        .agent-stopped {
            border-left: 4px solid #f44336;
        }
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
        }
        .btn:hover {
            background: #5a6fd8;
        }
        .btn-danger {
            background: #f44336;
        }
        .btn-danger:hover {
            background: #d32f2f;
        }
        .work-form {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }
        .work-form input, .work-form select, .work-form textarea {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .logs-section {
            background: #1a1a1a;
            color: #00ff00;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            height: 300px;
            overflow-y: auto;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .status-online {
            background-color: #4CAF50;
        }
        .status-offline {
            background-color: #f44336;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Redis AI Server Dashboard</h1>
            <p>Revolutionary AI Development Platform - Running Persistently</p>
            <div id="connection-status">
                <span class="status-indicator status-offline" id="status-dot"></span>
                <span id="status-text">Connecting...</span>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>Server Uptime</h3>
                <div class="stat-value" id="uptime">0s</div>
            </div>
            <div class="stat-card">
                <h3>Active Agents</h3>
                <div class="stat-value" id="active-agents">0</div>
            </div>
            <div class="stat-card">
                <h3>Work Completed</h3>
                <div class="stat-value" id="completed-work">0</div>
            </div>
            <div class="stat-card">
                <h3>Claude Available</h3>
                <div class="stat-value" id="claude-status">❌</div>
            </div>
        </div>

        <div class="agents-section">
            <h2>🤖 AI Agents</h2>
            <div id="agents-list">
                <p>Loading agents...</p>
            </div>
        </div>

        <div class="work-section">
            <h2>⚡ Assign Work</h2>
            <div class="work-form">
                <select id="work-agent">
                    <option value="test_agent_01">Test Agent</option>
                    <option value="doc_agent_01">Documentation Agent</option>
                    <option value="quality_agent_01">Quality Agent</option>
                </select>
                <select id="work-type">
                    <option value="test_generation">Generate Tests</option>
                    <option value="documentation">Generate Docs</option>
                    <option value="code_quality">Code Quality</option>
                </select>
                <input type="text" id="work-description" placeholder="Work description">
                <input type="text" id="work-files" placeholder="Target files (comma-separated)">
            </div>
            <button class="btn" onclick="assignWork()">Assign Work</button>
        </div>

        <div class="lisp-section">
            <h2>🔥 Homoiconic Lisp Execution</h2>
            <textarea id="lisp-code" placeholder='Enter Lisp code as JSON: ["print", "Hello World"]' style="width: 100%; height: 100px;"></textarea>
            <br><br>
            <button class="btn" onclick="executeLisp()">Execute Lisp Code</button>
        </div>

        <div class="logs-section" id="logs">
            <div>Redis AI Server Logs:</div>
            <div>Waiting for log updates...</div>
        </div>
    </div>

    <script>
        const socket = io();
        
        socket.on('connect', function() {
            document.getElementById('status-dot').className = 'status-indicator status-online';
            document.getElementById('status-text').textContent = 'Connected';
            loadAgents();
        });
        
        socket.on('disconnect', function() {
            document.getElementById('status-dot').className = 'status-indicator status-offline';
            document.getElementById('status-text').textContent = 'Disconnected';
        });
        
        socket.on('status_update', function(status) {
            document.getElementById('uptime').textContent = formatUptime(status.uptime);
            document.getElementById('active-agents').textContent = status.active_agents;
            document.getElementById('completed-work').textContent = status.completed_work;
            document.getElementById('claude-status').textContent = status.claude_available ? '✅' : '❌';
        });
        
        socket.on('work_assigned', function(data) {
            addLog(`Work assigned to ${data.agent_id}: ${data.description}`);
        });
        
        socket.on('composition_completed', function(data) {
            addLog(`Composition ${data.name} completed. Success: ${data.success}`);
        });
        
        function formatUptime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            return `${hours}h ${minutes}m ${secs}s`;
        }
        
        function loadAgents() {
            fetch('/api/agents')
                .then(response => response.json())
                .then(agents => {
                    const agentsList = document.getElementById('agents-list');
                    agentsList.innerHTML = '';
                    
                    agents.forEach(agent => {
                        const agentDiv = document.createElement('div');
                        agentDiv.className = `agent-item ${agent.status === 'running' ? 'agent-running' : 'agent-stopped'}`;
                        agentDiv.innerHTML = `
                            <div>
                                <strong>${agent.id}</strong> (${agent.specialty})
                                <br>Status: ${agent.status} | Completed: ${agent.work_completed}
                            </div>
                            <div>
                                <button class="btn" onclick="viewLogs('${agent.id}')">Logs</button>
                                <button class="btn ${agent.status === 'running' ? 'btn-danger' : ''}" 
                                        onclick="${agent.status === 'running' ? 'stopAgent' : 'startAgent'}('${agent.id}')">
                                    ${agent.status === 'running' ? 'Stop' : 'Start'}
                                </button>
                            </div>
                        `;
                        agentsList.appendChild(agentDiv);
                    });
                });
        }
        
        function assignWork() {
            const workData = {
                agent_id: document.getElementById('work-agent').value,
                task_type: document.getElementById('work-type').value,
                description: document.getElementById('work-description').value,
                target_files: document.getElementById('work-files').value.split(',').map(f => f.trim()).filter(f => f)
            };
            
            fetch('/api/work/assign', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(workData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog(`Work assigned: ${workData.description}`);
                    document.getElementById('work-description').value = '';
                    document.getElementById('work-files').value = '';
                } else {
                    addLog(`Error: ${data.error}`);
                }
            });
        }
        
        function executeLisp() {
            const code = document.getElementById('lisp-code').value;
            
            fetch('/api/lisp/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({code: code})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog(`Lisp code executed: ${code}`);
                } else {
                    addLog(`Error: ${data.error}`);
                }
            });
        }
        
        function addLog(message) {
            const logs = document.getElementById('logs');
            const timestamp = new Date().toLocaleTimeString();
            logs.innerHTML += `<div>[${timestamp}] ${message}</div>`;
            logs.scrollTop = logs.scrollHeight;
        }
        
        function viewLogs(agentId) {
            fetch(`/api/logs/${agentId}`)
                .then(response => response.json())
                .then(data => {
                    const logs = document.getElementById('logs');
                    logs.innerHTML = `<div>Logs for ${agentId}:</div>`;
                    data.logs.forEach(line => {
                        logs.innerHTML += `<div>${line}</div>`;
                    });
                    logs.scrollTop = logs.scrollHeight;
                });
        }
        
        // Load agents every 30 seconds
        setInterval(loadAgents, 30000);
        
        // Initial load
        setTimeout(loadAgents, 1000);
    </script>
</body>
</html>"""

    with open(template_dir / "dashboard.html", "w") as f:
        f.write(dashboard_html)

    print("✅ Created web dashboard template")


def main():
    """Main entry point"""

    print("🚀 Redis AI Server - Production Persistent Server")
    print("=" * 60)

    # Create web dashboard
    create_web_dashboard_template()

    # Create and start server
    server = RedisAIServer(host="0.0.0.0", port=8883)

    try:
        server.run()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        server.shutdown()


if __name__ == "__main__":
    main()
