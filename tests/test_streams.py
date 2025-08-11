"""
Tests for StreamProcessor - High-throughput event processing
"""

import pytest
import json
import time
from unittest.mock import Mock, patch
from redis_ai_patterns.streams import (
    StreamProcessor,
    MLJob,
    StreamEvent,
    JobStatus,
    EventType,
)


class TestStreamProcessor:

    @pytest.fixture
    def mock_redis(self):
        with patch("redis.Redis") as mock:
            mock_client = Mock()
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def processor(self, mock_redis):
        return StreamProcessor(namespace="test_stream")

    def test_initialization(self, processor, mock_redis):
        """Test proper initialization"""
        assert processor.namespace == "test_stream"
        assert processor.consumer_group == "test_stream_consumers"
        assert processor.consumer_id.startswith("consumer_")

        # Should try to create consumer groups
        assert mock_redis.xgroup_create.call_count == 5  # 5 streams

    def test_add_keystroke_event(self, processor, mock_redis):
        """Test adding keystroke events"""
        event = StreamEvent(
            event_type=EventType.KEYSTROKE,
            data={"key": "a", "modifiers": []},
            session_id="test_session",
        )

        mock_redis.xadd.return_value = "stream_id_123"

        result = processor.add_event(event)

        assert result == "stream_id_123"
        mock_redis.xadd.assert_called_once()

        # Check the call arguments
        call_args = mock_redis.xadd.call_args
        stream_key = call_args[0][0]
        event_data = call_args[0][1]

        assert "events:keystrokes" in stream_key
        assert event_data["type"] == "keystroke"
        assert json.loads(event_data["data"]) == {"key": "a", "modifiers": []}

    def test_add_command_event(self, processor, mock_redis):
        """Test adding command events"""
        event = StreamEvent(
            event_type=EventType.COMMAND,
            data={"command": "save-buffer", "args": []},
            session_id="test_session",
        )

        processor.add_event(event)

        call_args = mock_redis.xadd.call_args
        stream_key = call_args[0][0]
        assert "events:commands" in stream_key

    def test_process_events(self, processor, mock_redis):
        """Test event processing with callback"""
        # Mock xreadgroup response
        mock_redis.xreadgroup.return_value = [
            (
                "test_stream:events:keystrokes",
                [
                    (
                        "msg_id_1",
                        {
                            "type": "keystroke",
                            "data": '{"key": "a"}',
                            "timestamp": "1234567890",
                            "session_id": "test",
                        },
                    )
                ],
            )
        ]

        processed_events = []

        def test_processor(event_data):
            processed_events.append(event_data)
            return True

        result = processor.process_events(["events:keystrokes"], test_processor)

        assert result == 1  # One event processed
        assert len(processed_events) == 1
        assert processed_events[0]["type"] == "keystroke"
        assert processed_events[0]["data"] == {"key": "a"}

        # Should acknowledge the message
        mock_redis.xack.assert_called_once()

    def test_enqueue_ml_job(self, processor, mock_redis):
        """Test ML job enqueueing"""
        job = MLJob(
            id="test_job_123",
            priority=1,
            job_type="text_classification",
            payload={"text": "hello world"},
        )

        processor.enqueue_ml_job(job)

        # Should add to sorted set for priority queue
        mock_redis.zadd.assert_called_once()
        # Should store job details in hash
        mock_redis.hset.assert_called_once()

        zadd_call = mock_redis.zadd.call_args
        assert "ml:job_queue" in zadd_call[0][0]
        assert zadd_call[0][1] == {"test_job_123": 1}

    def test_dequeue_ml_job(self, processor, mock_redis):
        """Test ML job dequeueing"""
        # Mock sorted set response
        mock_redis.zrange.return_value = [("test_job_123", 1.0)]

        # Mock job data
        job_data = {
            "id": "test_job_123",
            "priority": "1",
            "job_type": "text_classification",
            "payload": '{"text": "hello"}',
            "status": "pending",
            "created_at": "1234567890.0",
            "attempts": "0",
            "max_attempts": "3",
        }
        mock_redis.hgetall.return_value = job_data

        job = processor.dequeue_ml_job()

        assert job is not None
        assert job.id == "test_job_123"
        assert job.priority == 1
        assert job.status == JobStatus.PENDING
        assert job.payload == {"text": "hello"}

        # Should remove from queue
        mock_redis.zrem.assert_called_once_with(
            "test_stream:ml:job_queue", "test_job_123"
        )

    def test_dequeue_empty_queue(self, processor, mock_redis):
        """Test dequeueing from empty queue"""
        mock_redis.zrange.return_value = []

        job = processor.dequeue_ml_job()
        assert job is None

    def test_update_job_status(self, processor, mock_redis):
        """Test updating job status"""
        processor.update_job_status(
            "test_job_123", JobStatus.COMPLETED, {"result": "success"}
        )

        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args

        updates = call_args[1]["mapping"]
        assert updates["status"] == "completed"
        assert json.loads(updates["result"]) == {"result": "success"}
        assert "completed_at" in updates

    def test_get_stream_info(self, processor, mock_redis):
        """Test getting stream information"""
        mock_redis.xinfo_stream.return_value = {
            "length": 42,
            "first-entry": ["1234-0", {}],
            "last-entry": ["5678-0", {}],
            "groups": 1,
        }

        info = processor.get_stream_info("events:keystrokes")

        assert info["length"] == 42
        assert info["consumer_groups"] == 1

    def test_simulate_high_throughput(self, processor, mock_redis):
        """Test high-throughput simulation"""
        processor.simulate_high_throughput_processing(50)

        # Should generate events and jobs
        assert mock_redis.xadd.call_count == 50  # 50 events
        assert mock_redis.zadd.call_count == 10  # 10 ML jobs


class TestMLJob:

    def test_job_creation(self):
        """Test MLJob creation with defaults"""
        job = MLJob(
            id="test_123",
            priority=1,
            job_type="classification",
            payload={"data": "test"},
        )

        assert job.id == "test_123"
        assert job.priority == 1
        assert job.status == JobStatus.PENDING
        assert job.attempts == 0
        assert job.max_attempts == 3
        assert job.created_at is not None

    def test_job_with_custom_values(self):
        """Test MLJob with custom values"""
        custom_time = time.time()
        job = MLJob(
            id="custom_job",
            priority=5,
            job_type="custom",
            payload={},
            status=JobStatus.PROCESSING,
            created_at=custom_time,
            attempts=2,
            max_attempts=5,
        )

        assert job.status == JobStatus.PROCESSING
        assert job.created_at == custom_time
        assert job.attempts == 2
        assert job.max_attempts == 5


class TestStreamEvent:

    def test_event_creation(self):
        """Test StreamEvent creation"""
        event = StreamEvent(
            event_type=EventType.KEYSTROKE, data={"key": "x"}, session_id="test_session"
        )

        assert event.event_type == EventType.KEYSTROKE
        assert event.data == {"key": "x"}
        assert event.session_id == "test_session"
        assert event.timestamp is not None

    def test_event_with_custom_timestamp(self):
        """Test StreamEvent with custom timestamp"""
        custom_time = 1234567890.0
        event = StreamEvent(
            event_type=EventType.COMMAND, data={}, timestamp=custom_time
        )

        assert event.timestamp == custom_time
