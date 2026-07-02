import subprocess
import time
import redis
import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REDIS_CLI = redis.Redis(decode_responses=True)
MAESTRO_STATUS_KEY = "maestro:status"
MAESTRO_MANIFEST_PATH = os.path.join(SCRIPT_DIR, "maestro_manifest.json")

def log_maestro_event(action, agent_name=None, pid=None, message=None):
    event_data = {
        "timestamp": time.time(),
        "action": action,
    }
    if agent_name:
        event_data["agent"] = agent_name
    if pid:
        event_data["pid"] = pid
    if message:
        event_data["message"] = message
    REDIS_CLI.xadd("maestro:log", event_data)

def load_manifest():
    if not os.path.exists(MAESTRO_MANIFEST_PATH):
        print(f"Maestro: Manifest file not found at {MAESTRO_MANIFEST_PATH}")
        return {}
    with open(MAESTRO_MANIFEST_PATH, 'r') as f:
        return json.load(f)

def is_process_running(pid):
    """Checks if a process with the given PID is running."""
    try:
        os.kill(pid, 0) # Signal 0 checks if the process exists
        return True
    except OSError:
        return False

def start_agent(agent_name):
    manifest = load_manifest()
    agent_config = manifest.get(agent_name)
    if not agent_config:
        log_maestro_event("error", agent_name=agent_name, message="Agent not found in manifest.")
        print(f"Maestro: Error: Agent '{agent_name}' not found in manifest.")
        return False

    script_path = os.path.join(SCRIPT_DIR, agent_config["path"])
    if not os.path.exists(script_path):
        log_maestro_event("error", agent_name=agent_name, message=f"Script not found at {script_path}.")
        print(f"Maestro: Error: Script for '{agent_name}' not found at {script_path}.")
        return False
    
    current_pid = REDIS_CLI.hget(MAESTRO_STATUS_KEY, f"{agent_name}:pid")
    if current_pid and is_process_running(int(current_pid)):
        log_maestro_event("info", agent_name=agent_name, pid=int(current_pid), message="Agent already running.")
        print(f"Maestro: Agent '{agent_name}' already running with PID {current_pid}.")
        return True

    try:
        process = None
        if agent_config["type"] == "python":
            process = subprocess.Popen(["python3", script_path], cwd=SCRIPT_DIR,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                       start_new_session=True)
        elif agent_config["type"] == "bash":
            subprocess.run(["chmod", "+x", script_path], check=True) # Ensure executable
            process = subprocess.Popen(["bash", script_path], cwd=SCRIPT_DIR,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                       start_new_session=True)
        else:
            log_maestro_event("error", agent_name=agent_name, message="Unknown agent type.")
            print(f"Maestro: Error: Unknown type for agent '{agent_name}'.")
            return False

        if process and process.pid:
            REDIS_CLI.hset(MAESTRO_STATUS_KEY, f"{agent_name}:pid", process.pid)
            REDIS_CLI.hset(MAESTRO_STATUS_KEY, f"{agent_name}:status", "running")
            log_maestro_event("agent_started", agent_name=agent_name, pid=process.pid)
            print(f"Maestro: Started '{agent_name}' with PID {process.pid}")
            return True
        return False
    except Exception as e:
        log_maestro_event("error", agent_name=agent_name, message=f"Failed to start: {e}")
        print(f"Maestro: Failed to start '{agent_name}': {e}")
        return False

def stop_agent(agent_name):
    pid = REDIS_CLI.hget(MAESTRO_STATUS_KEY, f"{agent_name}:pid")
    if pid and is_process_running(int(pid)):
        try:
            os.kill(int(pid), 9) # Force kill
            REDIS_CLI.hset(MAESTRO_STATUS_KEY, f"{agent_name}:status", "stopped")
            log_maestro_event("agent_stopped", agent_name=agent_name, pid=int(pid))
            print(f"Maestro: Stopped '{agent_name}' (PID: {pid})")
            return True
        except Exception as e:
            log_maestro_event("error", agent_name=agent_name, message=f"Failed to stop: {e}")
            print(f"Maestro: Failed to stop '{agent_name}': {e}")
            return False
    log_maestro_event("info", agent_name=agent_name, message="Agent not running or PID not found.")
    print(f"Maestro: Agent '{agent_name}' not running or PID not found.")
    return False

def status_agent(agent_name):
    pid = REDIS_CLI.hget(MAESTRO_STATUS_KEY, f"{agent_name}:pid")
    status = REDIS_CLI.hget(MAESTRO_STATUS_KEY, f"{agent_name}:status")
    if pid and is_process_running(int(pid)):
        return "running", pid
    return "stopped", None

def main():
    if len(sys.argv) < 2:
        print("Usage: maestro_agent.py <command> [agent_name]")
        print("Commands: start_all, stop_all, restart_all, start <agent_name>, stop <agent_name>, status <agent_name>")
        return

    command = sys.argv[1]
    
    if command == "start_all":
        manifest = load_manifest()
        for agent_name in manifest.keys():
            start_agent(agent_name)
    elif command == "stop_all":
        manifest = load_manifest()
        for agent_name in manifest.keys():
            stop_agent(agent_name)
    elif command == "restart_all":
        manifest = load_manifest()
        for agent_name in manifest.keys():
            stop_agent(agent_name)
            start_agent(agent_name)
    elif command == "start":
        if len(sys.argv) == 3:
            start_agent(sys.argv[2])
        else:
            print("Usage: maestro_agent.py start <agent_name>")
    elif command == "stop":
        if len(sys.argv) == 3:
            stop_agent(sys.argv[2])
        else:
            print("Usage: maestro_agent.py stop <agent_name>")
    elif command == "status":
        if len(sys.argv) == 3:
            status, pid = status_agent(sys.argv[2])
            print(f"Agent '{sys.argv[2]}' status: {status} (PID: {pid if pid else 'N/A'})")
        else:
            print("Usage: maestro_agent.py status <agent_name>")
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    import sys
    main()
