import time
import os
import random
import pickle
import redis
import subprocess

# Absolute path to the directory containing the scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REDIS_CLI = redis.Redis(decode_responses=True)

class MarkovBrain:
    def __init__(self, corpus_path, state_size=2):
        self.state_size = state_size
        self.starts = []
        self.chain = {}
        if os.path.exists(corpus_path):
            with open(corpus_path, 'rb') as f:
                data = pickle.load(f)
                self.starts = data['starts']
                self.chain = data['chain']

    def generate(self, seed_word=None, length=20):
        if not self.chain:
            return "Brain is empty. Needs training."

        if seed_word and seed_word in self.chain:
            current_state = tuple([seed_word] * self.state_size)
        else:
            current_state = random.choice(self.starts)

        output = list(current_state)
        for _ in range(length - self.state_size):
            if current_state in self.chain:
                next_word = random.choice(self.chain[current_state])
                output.append(next_word)
                current_state = tuple(output[-self.state_size:])
            else:
                break
        return " ".join(output)

def log_nomai_action(action, message=None):
    event_data = {
        "timestamp": time.time(),
        "action": action,
    }
    if message:
        event_data["message"] = message
    REDIS_CLI.xadd("nomai:log", event_data)

def main():
    log_nomai_action("nomai_started", message="Nomai agent initiated.")
    print("Nomai: Starting up...")

    # Load brain
    brain_path = os.path.join(SCRIPT_DIR, "nomai_brain.pkl")
    brain = MarkovBrain(brain_path)

    # Ensure nomai.log exists and is watched
    nomai_log_path = os.path.join(SCRIPT_DIR, "nomai.log")
    if not os.path.exists(nomai_log_path):
        with open(nomai_log_path, "w") as f:
            f.write("Nomai's first thought.\n")
        log_nomai_action("log_file_created", message="nomai.log created.")

    # Subscribe to Redis for file system events
    pubsub = REDIS_CLI.pubsub()
    pubsub.subscribe("cns:events")
    log_nomai_action("subscribed_to_cns_events", message="Subscribed to CNS events.")

    # Main sense-think-act loop
    for message in pubsub.listen():
        if message['type'] == 'message':
            event_data = message['data']
            try:
                event_dict = json.loads(event_data)
                log_nomai_action("cns_event_received", event=event_dict)

                if event_dict.get("event_type") == "file_modified" and event_dict.get("path") == nomai_log_path:
                    # Self-stimulate: Nomai generated a thought, now react to it
                    log_nomai_action("self_stimulation", message="Nomai log file modified, generating new thought.")
                    
                    # Read the last word from the log as a seed
                    with open(nomai_log_path, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            last_line = lines[-1].strip()
                            seed_word = last_line.split()[-1] if last_line else None
                        else:
                            seed_word = None
                    
                    new_thought = brain.generate(seed_word=seed_word, length=random.randint(5, 15))
                    with open(nomai_log_path, "a") as f:
                        f.write(new_thought + "\n")
                    log_nomai_action("thought_generated", thought=new_thought)

            except json.JSONDecodeError:
                log_nomai_action("json_decode_error", message=f"Failed to decode event: {event_data}")
            except Exception as e:
                log_nomai_action("agent_error", message=f"Error in Nomai loop: {e}")

if __name__ == "__main__":
    main()
