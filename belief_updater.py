import redis
import time
import json
import os

# Absolute path to the directory containing the scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REDIS_CLI = redis.Redis(decode_responses=True)
SUPERVISOR_LOG_STREAM = "supervisor:log"
BELIEF_STORE = "belief_store"
BELIEF_LOG_STREAM = "belief:log"

def log_belief_event(action, belief_key=None, confidence=None, message=None):
    """Logs belief updater actions to a Redis stream."""
    event_data = {
        "timestamp": time.time(),
        "action": action,
    }
    if belief_key:
        event_data["belief_key"] = belief_key
    if confidence is not None:
        event_data["confidence"] = confidence
    if message:
        event_data["message"] = message
    REDIS_CLI.xadd(BELIEF_LOG_STREAM, event_data)

def update_belief(belief_key, confidence, evidence_id=None, statement=""):
    """Updates a belief with a new confidence score and adds evidence."""
    current_confidence = float(REDIS_CLI.hget(BELIEF_STORE, f"{belief_key}:confidence") or 0.0)
    
    # Simple confidence update: take the new confidence if higher
    new_confidence = max(current_confidence, confidence)

    REDIS_CLI.hset(BELIEF_STORE, f"{belief_key}:confidence", new_confidence)
    if statement:
        REDIS_CLI.hset(BELIEF_STORE, f"{belief_key}:statement", statement)
    if evidence_id:
        REDIS_CLI.sadd(f"{belief_key}:evidence", evidence_id)
    
    log_belief_event("belief_updated", belief_key=belief_key, confidence=new_confidence, message=f"Confidence updated to {new_confidence}")
    print(f"Belief Updater: Updated belief '{belief_key}' to confidence {new_confidence}")


def process_supervisor_event(event_data, event_id):
    action = event_data.get("action")
    service_name = event_data.get("service")

    if action == "service_started" and service_name:
        belief_key = f"belief:{service_name.replace('.', '_')}_running"
        statement = f"The service {service_name} is running."
        update_belief(belief_key, 0.9, evidence_id=event_id, statement=statement) # High confidence
    elif action == "service_crashed" and service_name:
        belief_key = f"belief:{service_name.replace('.', '_')}_running"
        statement = f"The service {service_name} is running."
        update_belief(belief_key, 0.1, evidence_id=event_id, statement=statement) # Low confidence
    # Add more rules for other event types and their impact on beliefs

def main():
    log_belief_event("belief_updater_started", message="Belief Updater agent initiated.")
    print("Belief Updater: Starting to monitor supervisor log...")

    consumer_group_name = "belief_updater_group"
    consumer_name = "belief_updater_consumer"

    try:
        REDIS_CLI.xgroup_create(SUPERVISOR_LOG_STREAM, consumer_group_name, id='0', mkstream=True)
        print(f"Belief Updater: Consumer group '{consumer_group_name}' created or already exists.")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            print(f"Belief Updater: Error creating consumer group: {e}")
            return

    while True:
        try:
            messages = REDIS_CLI.xreadgroup(
                consumer_group_name,
                consumer_name,
                {SUPERVISOR_LOG_STREAM: '>'},
                count=1,
                block=5000
            )

            for stream, msgs in messages:
                for msg_id, msg_data in msgs:
                    REDIS_CLI.xack(SUPERVISOR_LOG_STREAM, consumer_group_name, msg_id)
                    event_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in msg_data.items()}
                    process_supervisor_event(event_data, msg_id)
        except Exception as e:
            log_belief_event("error", message=f"Error in Belief Updater loop: {e}")
        
        time.sleep(0.1)

if __name__ == "__main__":
    main()