import subprocess
import time
import redis
import os
import json
import threading

# Absolute path to the directory containing the scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REDIS_CLI = redis.Redis(decode_responses=True)

# Define the core services to be supervised
CORE_SERVICES = {
    "fsevents_listener": {"path": "fsevents_listener.py", "type": "python"},
    "nomai_agent": {"path": "nomai_agent.py", "type": "python"},
    "thinking_service": {"path": "thinking_service.py", "type": "python"},
    "heartbeat_agent": {"path": "heartbeat_agent.py", "type": "python"},
    "crypto_verifier": {"path": "crypto_verifier.py", "type": "python"},
    "belief_updater": {"path": "belief_updater.py", "type": "python"},
    "visualization_server": {"path": "visualization_server.py", "type": "python"},
    "phoenix_loop": {"path": "phoenix_loop.sh", "type": "bash"},
}

# The supervisor itself
SUPERVISOR_NAME = "supervisor_agent"
SUPERVISOR_SCRIPT = os.path.join(SCRIPT_DIR, f"{SUPERVISOR_NAME}.py")
CONTROL_STREAM = f"agent:{SUPERVISOR_NAME}:control"
LOG_STREAM = "supervisor:log"

def log_supervisor_event(action, service_name=None, pid=None, message=None):
    """Logs supervisor actions to a Redis stream."""
    event_data = {
        "timestamp": time.time(),
        "action": action,
    }
    if service_name:
        event_data["service"] = service_name
    if pid:
        event_data["pid"] = pid
    if message:
        event_data["message"] = message
    REDIS_CLI.xadd(LOG_STREAM, event_data)

def handle_control_messages(stop_event):
    """Listens for control messages on the supervisor's control stream."""
    print(f"Supervisor: Listening for control messages on {CONTROL_STREAM}...")
    consumer_group_name = f"{SUPERVISOR_NAME}_group"
    consumer_name = f"{SUPERVISOR_NAME}_consumer"

    try:
        REDIS_CLI.xgroup_create(CONTROL_STREAM, consumer_group_name, id='0', mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            log_supervisor_event("error", service_name=SUPERVISOR_NAME, message=f"Error creating consumer group: {e}")
            return

    while not stop_event.is_set():
        try:
            messages = REDIS_CLI.xreadgroup(
                consumer_group_name,
                consumer_name,
                {CONTROL_STREAM: '>'},
                count=1,
                block=1000 # Short block to allow checking stop_event
            )

            for stream, msgs in messages:
                for msg_id, msg_data in msgs:
                    REDIS_CLI.xack(CONTROL_STREAM, consumer_group_name, msg_id)
                    event_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in msg_data.items()}
                    
                    if event_data.get("command") == "SHUTDOWN":
                        log_supervisor_event("shutdown_received", service_name=SUPERVISOR_NAME, message="SHUTDOWN command received. Exiting.")
                        print("Supervisor: SHUTDOWN command received. Exiting.")
                        stop_event.set()
                        return

        except Exception as e:
            log_supervisor_event("error", service_name=SUPERVISOR_NAME, message=f"Error in control loop: {e}")
        
        time.sleep(0.1) # Prevent busy-looping

def main():
    log_supervisor_event("supervisor_started", message="Supervisor agent initiated.")
    print("Supervisor: Starting up and monitoring services...")

    stop_event = threading.Event()
    control_thread = threading.Thread(target=handle_control_messages, args=(stop_event,))
    control_thread.daemon = True
    control_thread.start()

    while not stop_event.is_set():
        for service_name, config in CORE_SERVICES.items():
            # In the new model, Supervisor should query Maestro for status and tell Maestro to start
            # For now, we'll keep the direct check until Maestro is fully integrated and tested
            # This is a temporary measure until Maestro is fully functional.
            
            # This part will be replaced by calls to Maestro
            pass 

        time.sleep(15)  # Check every 15 seconds

    log_supervisor_event("supervisor_shutdown", message="Supervisor agent gracefully shut down.")
    print("Supervisor: Graceful shutdown complete.")

if __name__ == "__main__":
    main()