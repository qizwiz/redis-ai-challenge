#!/usr/bin/env python3
"""
Production Reactive AI Server
Integrates all the revolutionary components into a working system.
"""

import asyncio
import logging
import threading
import time
import signal
import sys
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from flask import Flask, jsonify, request, render_template_string
from flask_socketio import SocketIO, emit
import redis

from robust_claude_integration import claude_integration, get_claude_status
from reactive_facade import reactive_facade, IntentType

# Set up production logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/Users/jonathanhill/.redis-ai-logs/production_server.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ProductionReactiveServer:
    """Production-ready Redis AI Server with reactive facade integration"""

    def __init__(
        self, host="localhost", port=8883, redis_host="localhost", redis_port=6379
    ):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "redis-ai-reactive-2025"
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Redis connection
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )

        # Server state
        self.running = False
        self.stats = {
            "start_time": None,
            "requests_processed": 0,
            "intents_captured": 0,
            "responses_generated": 0,
            "uptime_seconds": 0,
        }

        # Background loop control
        self.reactive_loop_task = None
        self.stats_update_thread = None

        self._setup_routes()
        self._setup_socketio()

    def _setup_routes(self):
        """Set up Flask routes"""

        @self.app.route("/")
        def dashboard():
            """Main dashboard"""
            return render_template_string(
                DASHBOARD_TEMPLATE, stats=self.stats, claude_status=get_claude_status()
            )

        @self.app.route("/api/status")
        def api_status():
            """API status endpoint"""
            return jsonify(
                {
                    "server": {
                        "running": self.running,
                        "uptime": (
                            time.time() - self.stats["start_time"]
                            if self.stats["start_time"]
                            else 0
                        ),
                    },
                    "claude": get_claude_status(),
                    "reactive_facade": {
                        "active_modes": list(reactive_facade.active_modes),
                        "running": reactive_facade.running,
                    },
                    "redis": self._get_redis_stats(),
                    "stats": self.stats,
                }
            )

        @self.app.route("/api/capture_intent", methods=["POST"])
        def capture_intent():
            """Capture user intent via API"""
            data = request.json
            try:
                intent_id = reactive_facade.capture_intent(
                    IntentType(data["type"]),
                    data["content"],
                    data.get("context", {}),
                    "api",
                )

                self.stats["intents_captured"] += 1
                self.stats["requests_processed"] += 1

                return jsonify(
                    {
                        "success": True,
                        "intent_id": intent_id,
                        "message": "Intent captured successfully",
                    }
                )
            except Exception as e:
                logger.error(f"Error capturing intent: {e}")
                return jsonify({"success": False, "error": str(e)}), 400

        @self.app.route("/api/activate_mode", methods=["POST"])
        def activate_mode():
            """Activate a composable AI mode"""
            data = request.json
            mode = data.get("mode")
            if not mode:
                return jsonify({"success": False, "error": "Mode required"}), 400

            try:
                reactive_facade.active_modes.add(mode)

                # Notify via intent
                reactive_facade.capture_intent(
                    IntentType.MODE_SWITCH,
                    f"activate {mode}",
                    {"mode": mode, "to": mode},
                    "api",
                )

                return jsonify(
                    {
                        "success": True,
                        "message": f"Activated {mode} mode",
                        "active_modes": list(reactive_facade.active_modes),
                    }
                )
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

    def _setup_socketio(self):
        """Set up SocketIO event handlers"""

        @self.socketio.on("connect")
        def handle_connect():
            logger.info("Client connected")
            emit(
                "status", {"connected": True, "server_time": datetime.now().isoformat()}
            )

        @self.socketio.on("capture_intent")
        def handle_socketio_intent(data):
            try:
                intent_id = reactive_facade.capture_intent(
                    IntentType(data["type"]),
                    data["content"],
                    data.get("context", {}),
                    "socketio",
                )

                self.stats["intents_captured"] += 1
                emit("intent_captured", {"intent_id": intent_id, "success": True})

            except Exception as e:
                logger.error(f"SocketIO intent error: {e}")
                emit("error", {"message": str(e)})

    def _get_redis_stats(self):
        """Get Redis connection stats"""
        try:
            info = self.redis.info()
            return {
                "connected": True,
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    def _start_reactive_loop(self):
        """Start the reactive facade loop in background"""

        def run_reactive_loop():
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                logger.info("🚀 Starting reactive facade loop in background thread")
                loop.run_until_complete(reactive_facade.start_reactive_loop())

            except Exception as e:
                logger.error(f"Reactive loop error: {e}")
            finally:
                logger.info("Reactive loop stopped")

        self.reactive_loop_thread = threading.Thread(
            target=run_reactive_loop, daemon=True
        )
        self.reactive_loop_thread.start()

    def _start_stats_updater(self):
        """Start background stats updater"""

        def update_stats():
            while self.running:
                if self.stats["start_time"]:
                    self.stats["uptime_seconds"] = (
                        time.time() - self.stats["start_time"]
                    )
                time.sleep(5)

        self.stats_update_thread = threading.Thread(target=update_stats, daemon=True)
        self.stats_update_thread.start()

    def start(self):
        """Start the production server"""
        logger.info("🚀 Starting Production Reactive AI Server")

        # Initialize stats
        self.stats["start_time"] = time.time()
        self.running = True

        # Start background components
        self._start_reactive_loop()
        self._start_stats_updater()

        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(f"✅ Server starting on {self.host}:{self.port}")
        logger.info(f"✅ Claude Status: {get_claude_status()}")
        logger.info(f"✅ Redis Status: {self._get_redis_stats()}")

        try:
            # Start Flask-SocketIO server
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=False,
                allow_unsafe_werkzeug=True,
            )
        except Exception as e:
            logger.error(f"Server error: {e}")
            self.stop()

    def stop(self):
        """Stop the server gracefully"""
        logger.info("🛑 Stopping Production Reactive AI Server")
        self.running = False

        # Stop reactive facade
        reactive_facade.stop()

        # Update final stats
        if self.stats["start_time"]:
            self.stats["uptime_seconds"] = time.time() - self.stats["start_time"]

        logger.info(f"📊 Final Stats: {self.stats}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)


# Dashboard HTML template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Production Reactive AI Server</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Monaco', 'Menlo', monospace; margin: 40px; background: #1a1a1a; color: #00ff00; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 40px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .status-card { background: #2a2a2a; border: 1px solid #444; border-radius: 8px; padding: 20px; }
        .status-card h3 { margin: 0 0 15px 0; color: #00ffff; }
        .metric { margin: 10px 0; }
        .metric-label { color: #888; }
        .metric-value { color: #00ff00; font-weight: bold; }
        .available { color: #00ff00; }
        .unavailable { color: #ff4444; }
        .controls { background: #2a2a2a; border: 1px solid #444; border-radius: 8px; padding: 20px; }
        .btn { background: #444; color: #00ff00; border: 1px solid #666; padding: 10px 20px; margin: 5px; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #555; }
        .log { background: #000; border: 1px solid #333; border-radius: 4px; padding: 15px; height: 200px; overflow-y: auto; font-size: 12px; margin-top: 15px; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Production Reactive AI Server</h1>
            <p>Revolutionary AI Development Environment - Redis AI Challenge 2025</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>Server Status</h3>
                <div class="metric">
                    <span class="metric-label">Uptime:</span>
                    <span class="metric-value">{{ "%.1f"|format(stats.uptime_seconds) }}s</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Requests:</span>
                    <span class="metric-value">{{ stats.requests_processed }}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Intents:</span>
                    <span class="metric-value">{{ stats.intents_captured }}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Responses:</span>
                    <span class="metric-value">{{ stats.responses_generated }}</span>
                </div>
            </div>
            
            <div class="status-card">
                <h3>Claude Integration</h3>
                <div class="metric">
                    <span class="metric-label">Status:</span>
                    <span class="metric-value {{ 'available' if claude_status.available else 'unavailable' }}">
                        {{ "Available" if claude_status.available else "Unavailable" }}
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-label">Path:</span>
                    <span class="metric-value">{{ claude_status.claude_path or "Not found" }}</span>
                </div>
            </div>
            
            <div class="status-card">
                <h3>Reactive Facade</h3>
                <div class="metric">
                    <span class="metric-label">Loop:</span>
                    <span class="metric-value available">Running</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Keystroke → AI Response:</span>
                    <span class="metric-value available">Active</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Intent Capture:</span>
                    <span class="metric-value available">Ready</span>
                </div>
            </div>
        </div>
        
        <div class="controls">
            <h3>Interactive Controls</h3>
            <button class="btn" onclick="captureTestIntent()">Test Intent Capture</button>
            <button class="btn" onclick="activateMode('implementation')">Activate Implementation Mode</button>
            <button class="btn" onclick="activateMode('architect')">Activate Architect Mode</button>
            <button class="btn" onclick="refreshStatus()">Refresh Status</button>
            
            <div class="log" id="eventLog">
                <div>🚀 Production Reactive AI Server initialized</div>
                <div>✅ Claude integration: {{ "Available" if claude_status.available else "Using fallback" }}</div>
                <div>✅ Reactive facade: Active</div>
                <div>✅ Ready for revolutionary AI development</div>
            </div>
        </div>
    </div>
    
    <script>
        const socket = io();
        const log = document.getElementById('eventLog');
        
        function logEvent(message) {
            const div = document.createElement('div');
            div.textContent = new Date().toLocaleTimeString() + ' - ' + message;
            log.appendChild(div);
            log.scrollTop = log.scrollHeight;
        }
        
        socket.on('connect', () => logEvent('🔗 Connected to server'));
        socket.on('intent_captured', (data) => logEvent('📝 Intent captured: ' + data.intent_id));
        
        function captureTestIntent() {
            socket.emit('capture_intent', {
                type: 'query',
                content: 'Test query from dashboard',
                context: { source: 'dashboard', timestamp: Date.now() }
            });
            logEvent('🧪 Test intent sent');
        }
        
        function activateMode(mode) {
            fetch('/api/activate_mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: mode })
            }).then(r => r.json()).then(data => {
                logEvent('🎼 ' + (data.success ? 'Activated ' + mode + ' mode' : 'Error: ' + data.error));
            });
        }
        
        function refreshStatus() {
            location.reload();
        }
    </script>
</body>
</html>
"""


def main():
    """Main entry point"""
    print("🚀 Production Reactive AI Server")
    print("=" * 60)

    # Test Redis connection
    try:
        redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
        redis_client.ping()
        print("✅ Redis connection verified")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        sys.exit(1)

    # Start server
    server = ProductionReactiveServer()
    server.start()


if __name__ == "__main__":
    main()
