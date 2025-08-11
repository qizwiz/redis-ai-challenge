#!/usr/bin/env python3
"""
Persistent Agent Daemon - Bulletproof background AI agents

This is the system that ensures my AI agents NEVER stop working. They survive:
- System crashes and reboots
- Network disconnections
- Power outages
- Code updates and deployments
- Me forgetting about them entirely

The ultimate "set it and forget it" AI workforce that just keeps making my life better.
"""

import os
import sys
import json
import time
import signal
import daemon
import lockfile
import logging
import logging.handlers
import redis
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import psutil
import threading
import atexit


@dataclass
class DaemonConfig:
    """Configuration for the persistent daemon"""

    pid_file: str
    log_file: str
    redis_host: str = "localhost"
    redis_port: int = 6379
    work_dir: str = os.getcwd()
    max_memory_mb: int = 1024  # Maximum memory usage
    restart_on_crash: bool = True
    check_interval: int = 30  # Health check interval
    backup_interval: int = 300  # Backup interval (5 minutes)


class PersistentAgentDaemon:
    """A daemon that ensures AI agents never stop working"""

    def __init__(self, config: DaemonConfig):
        self.config = config
        self.redis = None
        self.agents = {}
        self.running = False
        self.health_thread = None
        self.backup_thread = None

        # Setup logging
        self.logger = self._setup_logging()

        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _setup_logging(self) -> logging.Logger:
        """Setup persistent logging"""

        log_dir = Path(self.config.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger("agent_daemon")
        logger.setLevel(logging.INFO)

        # File handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            self.config.log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def start_daemon(self):
        """Start the daemon process"""

        # Check if already running
        if self._is_already_running():
            print(f"Daemon already running (PID file: {self.config.pid_file})")
            return False

        print(f"Starting persistent agent daemon...")
        print(f"PID file: {self.config.pid_file}")
        print(f"Log file: {self.config.log_file}")

        # Create daemon context
        daemon_context = daemon.DaemonContext(
            pidfile=lockfile.FileLock(self.config.pid_file),
            working_directory=self.config.work_dir,
            umask=0o002,
            signal_map={
                signal.SIGTERM: self._signal_handler,
                signal.SIGINT: self._signal_handler,
            },
        )

        try:
            with daemon_context:
                self._run_daemon()
        except Exception as e:
            self.logger.error(f"Failed to start daemon: {e}")
            return False

        return True

    def _run_daemon(self):
        """Main daemon loop"""

        self.logger.info("Agent daemon started")
        self.running = True

        try:
            # Initialize Redis connection
            self._connect_to_redis()

            # Load saved agent state
            self._restore_agent_state()

            # Start health monitoring
            self.health_thread = threading.Thread(
                target=self._health_monitor_loop, daemon=True
            )
            self.health_thread.start()

            # Start backup system
            self.backup_thread = threading.Thread(target=self._backup_loop, daemon=True)
            self.backup_thread.start()

            # Main daemon loop
            while self.running:
                try:
                    # Check agent health and restart if needed
                    self._check_and_restart_agents()

                    # Process daemon commands
                    self._process_daemon_commands()

                    # Monitor system resources
                    self._monitor_system_resources()

                    # Sleep
                    time.sleep(self.config.check_interval)

                except Exception as e:
                    self.logger.error(f"Error in daemon loop: {e}")
                    time.sleep(60)  # Longer sleep on error

        except Exception as e:
            self.logger.error(f"Fatal daemon error: {e}")
        finally:
            self.cleanup()

    def _connect_to_redis(self):
        """Connect to Redis with retry logic"""

        max_retries = 5
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                self.redis = redis.Redis(
                    host=self.config.redis_host,
                    port=self.config.redis_port,
                    decode_responses=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30,
                )

                # Test connection
                self.redis.ping()
                self.logger.info(
                    f"Connected to Redis at {self.config.redis_host}:{self.config.redis_port}"
                )
                return

            except Exception as e:
                self.logger.warning(
                    f"Redis connection attempt {attempt + 1} failed: {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

        raise Exception("Failed to connect to Redis after all retries")

    def _restore_agent_state(self):
        """Restore agent state from previous runs"""

        try:
            # Get list of agents that should be running
            agent_keys = self.redis.keys("agent_daemon:*")

            for key in agent_keys:
                agent_data = self.redis.get(key)
                if agent_data:
                    agent_info = json.loads(agent_data)
                    agent_id = agent_info["agent_id"]

                    # Check if agent process is still running
                    if self._is_agent_process_running(agent_info.get("pid")):
                        self.logger.info(
                            f"Agent {agent_id} still running (PID: {agent_info['pid']})"
                        )
                        self.agents[agent_id] = agent_info
                    else:
                        self.logger.info(f"Restarting agent {agent_id}")
                        self._start_agent(agent_info)

        except Exception as e:
            self.logger.error(f"Error restoring agent state: {e}")

    def _start_agent(self, agent_info: Dict[str, Any]) -> bool:
        """Start an individual agent process"""

        try:
            # Create agent start script
            agent_script = self._create_agent_script(agent_info)

            # Start agent process
            process = subprocess.Popen(
                [sys.executable, agent_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Update agent info
            agent_info["pid"] = process.pid
            agent_info["started_at"] = time.time()
            agent_info["restart_count"] = agent_info.get("restart_count", 0) + 1

            # Save to Redis
            self.redis.setex(
                f"agent_daemon:{agent_info['agent_id']}",
                86400,  # 24 hour TTL
                json.dumps(agent_info),
            )

            self.agents[agent_info["agent_id"]] = agent_info
            self.logger.info(
                f"Started agent {agent_info['agent_id']} (PID: {process.pid})"
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to start agent {agent_info['agent_id']}: {e}")
            return False

    def _create_agent_script(self, agent_info: Dict[str, Any]) -> str:
        """Create a temporary script to run the agent"""

        script_dir = Path.home() / ".redis-ai-scripts"
        script_dir.mkdir(exist_ok=True)

        agent_id = agent_info["agent_id"]
        script_path = script_dir / f"{agent_id}_runner.py"

        script_content = f"""#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, "{os.path.dirname(__file__)}")

from always_on_ai_workforce import PersistentBackgroundAgent, BackgroundTaskType
import redis

# Agent configuration
agent_id = "{agent_id}"
specialty = BackgroundTaskType.{agent_info['specialty']}
redis_client = redis.Redis(host="{self.config.redis_host}", port={self.config.redis_port}, decode_responses=True)

# Create and start agent
agent = PersistentBackgroundAgent(agent_id, specialty, redis_client)
agent.start_background_work()

# Keep agent running
try:
    while True:
        import time
        time.sleep(60)
except KeyboardInterrupt:
    agent.shutdown()
"""

        with open(script_path, "w") as f:
            f.write(script_content)

        # Make executable
        os.chmod(script_path, 0o755)

        return str(script_path)

    def _check_and_restart_agents(self):
        """Check agent health and restart if needed"""

        for agent_id, agent_info in list(self.agents.items()):
            try:
                # Check if process is still running
                if not self._is_agent_process_running(agent_info.get("pid")):
                    self.logger.warning(f"Agent {agent_id} process died, restarting...")

                    if self.config.restart_on_crash:
                        self._start_agent(agent_info)
                    else:
                        # Remove dead agent
                        del self.agents[agent_id]
                        self.redis.delete(f"agent_daemon:{agent_id}")

                # Check agent heartbeat
                elif not self._check_agent_heartbeat(agent_info):
                    self.logger.warning(
                        f"Agent {agent_id} heartbeat timeout, restarting..."
                    )

                    # Kill unresponsive agent
                    self._kill_agent_process(agent_info.get("pid"))

                    if self.config.restart_on_crash:
                        self._start_agent(agent_info)

            except Exception as e:
                self.logger.error(f"Error checking agent {agent_id}: {e}")

    def _kill_agent_process(self, pid: Optional[int]):
        """Kill an agent process"""

        if not pid:
            return

        try:
            process = psutil.Process(pid)
            process.terminate()

            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
            except psutil.TimeoutExpired:
                # Force kill if doesn't shut down gracefully
                process.kill()

        except psutil.NoSuchProcess:
            pass  # Process already dead
        except Exception as e:
            self.logger.error(f"Error killing process {pid}: {e}")

    def _process_daemon_commands(self):
        """Process commands sent to the daemon"""

        try:
            command_data = self.redis.lpop("daemon_commands")
            if not command_data:
                return

            command = json.loads(command_data)
            command_type = command.get("type")

            if command_type == "start_agent":
                self._handle_start_agent_command(command)
            elif command_type == "stop_agent":
                self._handle_stop_agent_command(command)
            elif command_type == "restart_agent":
                self._handle_restart_agent_command(command)
            elif command_type == "status":
                self._handle_status_command(command)
            elif command_type == "shutdown":
                self._handle_shutdown_command(command)

        except Exception as e:
            self.logger.error(f"Error processing daemon command: {e}")

    def _backup_loop(self):
        """Background state backup"""

        while self.running:
            try:
                # Backup agent states
                backup_data = {"timestamp": time.time(), "agents": self.agents}

                backup_file = (
                    Path.home() / ".redis-ai-backup" / f"agents_{int(time.time())}.json"
                )
                backup_file.parent.mkdir(exist_ok=True)

                with open(backup_file, "w") as f:
                    json.dump(backup_data, f, indent=2)

                # Keep only recent backups
                self._cleanup_old_backups()

                time.sleep(self.config.backup_interval)

            except Exception as e:
                self.logger.error(f"Backup error: {e}")
                time.sleep(300)  # 5 minute retry on error

    def cleanup(self):
        """Cleanup daemon resources"""

        self.logger.info("Cleaning up daemon...")
        self.running = False

        # Stop all agents
        for agent_id, agent_info in self.agents.items():
            self._kill_agent_process(agent_info.get("pid"))

        # Remove PID file
        try:
            os.unlink(self.config.pid_file)
        except:
            pass

        self.logger.info("Daemon cleanup complete")


class DaemonController:
    """Controller for the persistent agent daemon"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def start_daemon(self, config: DaemonConfig) -> bool:
        """Start the daemon"""

        daemon = PersistentAgentDaemon(config)
        return daemon.start_daemon()

    def send_command(self, command_type: str, **kwargs) -> Any:
        """Send command to running daemon"""

        command = {"type": command_type, "command_id": str(time.time()), **kwargs}

        self.redis.rpush("daemon_commands", json.dumps(command))

        # Wait for response
        timeout = 30  # 30 second timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            response_data = self.redis.lpop("daemon_responses")
            if response_data:
                response = json.loads(response_data)
                if response.get("command_id") == command["command_id"]:
                    return response["response"]

            time.sleep(0.5)

        return None  # Timeout

    def get_daemon_status(self) -> Dict[str, Any]:
        """Get daemon status"""
        return self.send_command("status")

    def start_agent(self, agent_id: str, specialty: str) -> str:
        """Start an agent"""
        return self.send_command("start_agent", agent_id=agent_id, specialty=specialty)

    def stop_agent(self, agent_id: str) -> str:
        """Stop an agent"""
        return self.send_command("stop_agent", agent_id=agent_id)

    def shutdown_daemon(self) -> str:
        """Shutdown the daemon"""
        return self.send_command("shutdown")


def main():
    """Main entry point for daemon control"""

    if len(sys.argv) < 2:
        print("Usage: python persistent_agent_daemon.py <start|stop|status|restart>")
        sys.exit(1)

    command = sys.argv[1]

    # Configuration
    config = DaemonConfig(
        pid_file=str(Path.home() / ".redis-ai-daemon.pid"),
        log_file=str(Path.home() / ".redis-ai-logs" / "daemon.log"),
        work_dir=os.getcwd(),
    )

    if command == "start":
        daemon = PersistentAgentDaemon(config)
        if daemon.start_daemon():
            print("✅ Daemon started successfully")
        else:
            print("❌ Failed to start daemon")

    elif command == "status":
        redis_client = redis.Redis(
            host=config.redis_host, port=config.redis_port, decode_responses=True
        )
        controller = DaemonController(redis_client)

        status = controller.get_daemon_status()
        if status:
            print("📊 DAEMON STATUS:")
            print(f"   Running: Yes")
            print(f"   Uptime: {status['uptime']/3600:.1f} hours")
            print(f"   Active Agents: {status['active_agents']}")

            for agent_id, agent_info in status["agents"].items():
                print(
                    f"   • {agent_id}: {agent_info['specialty']} (PID: {agent_info['pid']})"
                )
        else:
            print("❌ Daemon not responding")

    elif command == "stop":
        redis_client = redis.Redis(
            host=config.redis_host, port=config.redis_port, decode_responses=True
        )
        controller = DaemonController(redis_client)

        result = controller.shutdown_daemon()
        if result:
            print("✅ Daemon shutdown initiated")
        else:
            print("❌ Failed to shutdown daemon")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
