"""
Stream Processing - High-throughput event processing with Redis Streams
"""

import redis
import json
import time
import uuid
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from .core import RedisAIBase


class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class EventType(Enum):
    KEYSTROKE = "keystroke"
    COMMAND = "command"
    BUFFER_CHANGE = "buffer_change"
    ML_REQUEST = "ml_request"
    ML_RESPONSE = "ml_response"


@dataclass
class MLJob:
    id: str
    priority: int
    job_type: str
    payload: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    created_at: float = None
    attempts: int = 0
    max_attempts: int = 3

    def __post_init__(self):
        """
        TODO: Document __post_init__ function

        This function requires documentation.
        Args and return value need to be documented based on the implementation.
        """
        if self.created_at is None:
            self.created_at = time.time()


@dataclass
class StreamEvent:
    event_type: EventType
    data: Dict[str, Any]
    timestamp: float = None
    session_id: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class StreamProcessor(RedisAIBase):
    """High-throughput Redis Streams processor for AI coordination"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.consumer_group = f"{self.namespace}_consumers"
        self.consumer_id = f"consumer_{uuid.uuid4().hex[:8]}"
        self._init_streams()

    def _init_streams(self):
        """Initialize Redis streams and consumer groups"""
        streams = [
            "events:keystrokes",
            "events:commands",
            "events:buffer_changes",
            "ml:requests",
            "ml:responses",
        ]

        for stream in streams:
            stream_key = self.key(stream)
            try:
                # Create consumer group if it doesn't exist
                self.redis_client.xgroup_create(
                    stream_key, self.consumer_group, id="0", mkstream=True
                )
            except redis.exceptions.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

    def add_event(self, event: StreamEvent) -> str:
        """Add event to appropriate stream"""
        stream_map = {
            EventType.KEYSTROKE: "events:keystrokes",
            EventType.COMMAND: "events:commands",
            EventType.BUFFER_CHANGE: "events:buffer_changes",
            EventType.ML_REQUEST: "ml:requests",
            EventType.ML_RESPONSE: "ml:responses",
        }

        stream_key = self.key(stream_map[event.event_type])
        event_data = {
            "type": event.event_type.value,
            "data": json.dumps(event.data),
            "timestamp": event.timestamp,
            "session_id": event.session_id or self.session_id,
        }

        return self.redis_client.xadd(stream_key, event_data)

    def process_events(
        self,
        stream_names: List[str],
        processor_func: Callable,
        batch_size: int = 10,
        block_ms: int = 1000,
    ) -> int:
        """Process events from streams with callback function"""
        stream_keys = {self.key(name): ">" for name in stream_names}

        try:
            messages = self.redis_client.xreadgroup(
                self.consumer_group,
                self.consumer_id,
                stream_keys,
                count=batch_size,
                block=block_ms,
            )

            processed_count = 0
            for stream_key, stream_messages in messages:
                for msg_id, fields in stream_messages:
                    try:
                        # Reconstruct event
                        event_data = {
                            "id": msg_id,
                            "stream": (
                                stream_key.decode()
                                if isinstance(stream_key, bytes)
                                else stream_key
                            ),
                            "type": fields.get("type"),
                            "data": json.loads(fields.get("data", "{}")),
                            "timestamp": float(fields.get("timestamp", 0)),
                            "session_id": fields.get("session_id"),
                        }

                        # Process with callback
                        result = processor_func(event_data)

                        # Acknowledge message
                        self.redis_client.xack(stream_key, self.consumer_group, msg_id)
                        processed_count += 1

                    except Exception as e:
                        print(f"Error processing message {msg_id}: {e}")
                        # Could implement dead letter queue here

            return processed_count

        except redis.exceptions.ResponseError:
            return 0

    def enqueue_ml_job(self, job: MLJob) -> None:
        """Add ML job to priority queue"""
        job_data = asdict(job)
        # Serialize payload to JSON string
        job_data["payload"] = json.dumps(job_data["payload"])
        job_data["status"] = job_data["status"].value

        # Use sorted set for priority queue
        queue_key = self.key("ml:job_queue")
        self.redis_client.zadd(queue_key, {job.id: job.priority})

        # Store job details
        job_key = self.key(f"ml:job:{job.id}")
        self.redis_client.hset(job_key, mapping=job_data)

    def dequeue_ml_job(self) -> Optional[MLJob]:
        """Get highest priority ML job"""
        queue_key = self.key("ml:job_queue")

        # Get highest priority job (lowest score)
        jobs = self.redis_client.zrange(queue_key, 0, 0, withscores=True)
        if not jobs:
            return None

        job_id, priority = jobs[0]

        # Remove from queue
        self.redis_client.zrem(queue_key, job_id)

        # Get job details
        job_key = self.key(f"ml:job:{job_id}")
        job_data = self.redis_client.hgetall(job_key)

        if job_data:
            # Convert back to MLJob
            job_data["status"] = JobStatus(job_data["status"])
            job_data["priority"] = int(job_data["priority"])
            job_data["created_at"] = float(job_data["created_at"])
            job_data["attempts"] = int(job_data["attempts"])
            job_data["max_attempts"] = int(job_data["max_attempts"])
            job_data["payload"] = json.loads(job_data["payload"])

            return MLJob(**job_data)

        return None

    def update_job_status(
        self, job_id: str, status: JobStatus, result: Any = None
    ) -> None:
        """Update job status and optionally store result"""
        job_key = self.key(f"ml:job:{job_id}")

        updates = {"status": status.value}
        if result is not None:
            updates["result"] = json.dumps(result)
            updates["completed_at"] = time.time()

        self.redis_client.hset(job_key, mapping=updates)

    def get_stream_info(self, stream_name: str) -> Dict:
        """Get information about a stream"""
        stream_key = self.key(stream_name)
        try:
            info = self.redis_client.xinfo_stream(stream_key)
            return {
                "length": info.get("length", 0),
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry"),
                "consumer_groups": info.get("groups", 0),
            }
        except:
            return {"length": 0}

    def simulate_high_throughput_processing(self, event_count: int = 100):
        """Simulate processing high-throughput events"""
        print(f"📊 Simulating high-throughput processing of {event_count} events...")

        # Generate sample events
        for i in range(event_count):
            if i % 3 == 0:
                event = StreamEvent(
                    event_type=EventType.KEYSTROKE,
                    data={"key": chr(97 + (i % 26)), "modifiers": []},
                    session_id=self.session_id,
                )
            elif i % 3 == 1:
                event = StreamEvent(
                    event_type=EventType.COMMAND,
                    data={"command": f"test-command-{i}", "args": []},
                    session_id=self.session_id,
                )
            else:
                event = StreamEvent(
                    event_type=EventType.BUFFER_CHANGE,
                    data={"buffer": "test.py", "change_type": "insert"},
                    session_id=self.session_id,
                )

            self.add_event(event)

        # Generate ML jobs
        for i in range(10):
            job = MLJob(
                id=f"job_{i}",
                priority=i % 3,
                job_type="text_classification",
                payload={"text": f"Sample text {i}"},
            )
            self.enqueue_ml_job(job)

        print(f"✅ Generated {event_count} events and 10 ML jobs")
