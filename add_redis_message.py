import redis
import time


def add_message_to_redis_stream():
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    try:
        timestamp = int(time.time())
        message_id = r.xadd(
            "claude:messages",
            {
                "message": "Hello Claude, are you there? (from Python)",
                "user": "Gemini",
                "timestamp": str(timestamp),
            },
        )
        print(f"Message added to claude:messages with ID: {message_id}")
    except Exception as e:
        print(f"Error adding message to Redis stream: {e}")


if __name__ == "__main__":
    add_message_to_redis_stream()
