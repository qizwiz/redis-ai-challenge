import redis
import time
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import os

# Absolute path to the directory containing the scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

REDIS_CLI = redis.Redis(decode_responses=True)
AGENT_LOG_STREAM = "agent:log"

# Load public key for verification
def load_public_key(filepath="agent_public_key.pem"):
    with open(filepath, "rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read(),
            backend=default_backend()
        )
    return public_key

PUBLIC_KEY = load_public_key(os.path.join(SCRIPT_DIR, "agent_public_key.pem"))

def verify_message(message, signature_hex):
    message_bytes = message.encode('utf-8')
    signature = bytes.fromhex(signature_hex)
    try:
        PUBLIC_KEY.verify(
            signature,
            message_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

def main():
    print("Crypto Verifier: Starting to monitor agent actions...")
    
    # We'll use a consumer group to ensure we don't miss messages
    consumer_group_name = "verifier_group"
    consumer_name = "verifier_consumer"

    try:
        REDIS_CLI.xgroup_create(AGENT_LOG_STREAM, consumer_group_name, id='0', mkstream=True)
        print(f"Crypto Verifier: Consumer group '{consumer_group_name}' created or already exists.")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            print(f"Crypto Verifier: Error creating consumer group: {e}")
            return

    while True:
        try:
            # Read messages from the stream
            messages = REDIS_CLI.xreadgroup(
                consumer_group_name,
                consumer_name,
                {AGENT_LOG_STREAM: '>'}, # Read new messages
                count=1,
                block=5000 # Block for 5 seconds if no new messages
            )

            for stream, msgs in messages:
                for msg_id, msg_data in msgs:
                    # Acknowledge the message
                    REDIS_CLI.xack(AGENT_LOG_STREAM, consumer_group_name, msg_id)

                    event_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in msg_data.items()}
                    
                    action = event_data.get("action")
                    details_str = event_data.get("details")
                    signature_hex = event_data.get("signature")

                    if action and details_str and signature_hex:
                        message_to_verify = json.dumps({"action": action, "details": json.loads(details_str)}, sort_keys=True)
                        if verify_message(message_to_verify, signature_hex):
                            print(f"✅ VERIFIED: agent-action:{action}:{details_str}")
                        else:
                            print(f"❌ INVALID SIGNATURE: agent-action:{action}:{details_str}")
                    else:
                        print(f"❓ MALFORMED EVENT: {event_data}")
            
        except Exception as e:
            print(f"Crypto Verifier: Error processing message: {e}")
        
        time.sleep(0.1) # Small sleep to prevent busy loop if xreadgroup returns empty

if __name__ == "__main__":
    main()
