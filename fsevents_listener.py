import redis
import time
import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Absolute path to the directory containing the scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REDIS_CLI = redis.Redis(decode_responses=True)
CNS_EVENTS_STREAM = "cns:events"
WATCH_DIRECTORY = os.path.dirname(SCRIPT_DIR) # Watch the parent directory (src)

class MyEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        self._send_event("file_created", event)

    def on_deleted(self, event):
        self._send_event("file_deleted", event)

    def on_modified(self, event):
        self._send_event("file_modified", event)

    def on_moved(self, event):
        self._send_event("file_moved", event)

    def _send_event(self, event_type, event):
        event_data = {
            "event_type": event_type,
            "path": event.src_path,
            "is_directory": event.is_directory,
            "timestamp": time.time()
        }
        REDIS_CLI.xadd(CNS_EVENTS_STREAM, event_data)
        print(f"FSEvents Listener: Sent event to Redis: {event_data['event_type']} - {event_data['path']}")


def main():
    print(f"FSEvents Listener: Starting to watch directory: {WATCH_DIRECTORY}")
    event_handler = MyEventHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("FSEvents Listener: Stopped.")

if __name__ == "__main__":
    main()
