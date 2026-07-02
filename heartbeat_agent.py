import time
import json
import requests
import redis
import os
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Absolute path to the directory containing the scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REDIS_CLI = redis.Redis(decode_responses=True)
TASK_QUEUE = "heartbeat:tasks"
AGENT_LOG_STREAM = "agent:log"
THINKING_SERVICE_URL = "http://localhost:8001/think" # URL for our local thinking service

# Load private key for signing
def load_private_key(filepath="agent_private_key.pem"):
    with open(filepath, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

PRIVATE_KEY = load_private_key(os.path.join(SCRIPT_DIR, "agent_private_key.pem"))

def sign_message(message):
    message_bytes = message.encode('utf-8')
    signature = PRIVATE_KEY.sign(
        message_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature.hex()

def log_agent_action(action, details):
    message_to_sign = json.dumps({"action": action, "details": details}, sort_keys=True)
    signature = sign_message(message_to_sign)
    event_data = {
        "timestamp": time.time(),
        "action": action,
        "details": json.dumps(details),
        "signature": signature
    }
    REDIS_CLI.xadd(AGENT_LOG_STREAM, event_data)

def call_thinking_service(prompt, context=None):
    try:
        payload = {"prompt": prompt}
        if context:
            payload["context"] = context
        
        response = requests.post(THINKING_SERVICE_URL, json=payload)
        response.raise_for_status() # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        log_agent_action("thinking_service_error", {"prompt": prompt, "error": str(e)})
        return {"error": str(e)}

def main():
    log_agent_action("heartbeat_started", {"message": "Heartbeat agent initiated."})
    print("Heartbeat Agent: Starting up...")

    while True:
        # 1. Sense: Pull a task from the queue
        _, task_data = REDIS_CLI.brpop(TASK_QUEUE, timeout=10) # Blocking pop with timeout
        if task_data:
            task = json.loads(task_data)
            task_id = task.get("id", "no_id")
            task_type = task.get("type", "unknown_task")
            task_payload = task.get("payload", {})

            log_agent_action("task_pulled", {"task_id": task_id, "task_type": task_type, "payload": task_payload})
            print(f"Heartbeat Agent: Pulled task {task_type} (ID: {task_id})")

            # 2. Think: Call the thinking service
            prompt = task_payload.get("prompt", "What should I do next?")
            context = REDIS_CLI.hgetall("metagraph:context") # Example: get context from metagraph
            
            thinking_response = call_thinking_service(prompt, json.dumps(context))

            log_agent_action("thinking_service_called", {"prompt": prompt, "response": thinking_response})
            print(f"Heartbeat Agent: Thinking service responded for task {task_id}.")

            # 3. Act: Process the thinking service's response (simplified for now)
            if "decision" in thinking_response:
                decision = thinking_response["decision"]
                log_agent_action("decision_made", {"task_id": task_id, "decision": decision})
                print(f"Heartbeat Agent: Decision for task {task_id}: {decision}")
                # Here, you would typically translate decision into tool calls or new tasks
            else:
                log_agent_action("thinking_failed", {"task_id": task_id, "response": thinking_response})
                print(f"Heartbeat Agent: Thinking service failed for task {task_id}.")
        else:
            # If no tasks, periodically log a heartbeat or generate new tasks
            log_agent_action("heartbeat_idle", {"message": "No tasks in queue, waiting."})
            print("Heartbeat Agent: Idle, waiting for tasks...")

        time.sleep(1) # Prevent busy-looping

if __name__ == "__main__":
    main()
