import subprocess
import redis
import json
import os
import time


def get_running_mcp_processes():
    try:
        # Get all Python processes
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, check=True
        )
        lines = result.stdout.splitlines()

        mcp_processes = []
        # Filter for processes related to our MCP servers
        mcp_server_scripts = [
            "mcp_redis_lisp_server.py",
            "emacs_persistent_vision_mcp.py",
            "mcp_ai_assistant.py",
            "redis_state_diff_mcp.py",
            "redis_emacs_mcp_server.py",
        ]

        for line in lines:
            if "python3" in line and any(
                script in line for script in mcp_server_scripts
            ):
                # Extract relevant info (PID, command)
                parts = line.split()
                pid = parts[1]
                command = " ".join(parts[10:])  # Full command line

                # Exclude the check_mcp_processes.py itself
                if "check_mcp_processes.py" not in command:
                    mcp_processes.append({"pid": pid, "command": command})
        return mcp_processes
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    r = redis.Redis(decode_responses=True)

    # Ensure Redis is reachable
    try:
        r.ping()
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        exit(1)

    processes = get_running_mcp_processes()

    # Store the status in Redis
    r.set("emacs:mcp_process_status", json.dumps(processes))
    print(f"MCP process status updated in Redis: {json.dumps(processes)}")
