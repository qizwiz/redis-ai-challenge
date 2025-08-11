import redis
import time
import subprocess

redis_client = redis.Redis(decode_responses=True)
stream_name = "emacs:content"
group_name = "ai_agents"
consumer_name = "test_consumer_123"

try:
    # Ensure the group exists
    try:
        redis_client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
        print(f"Created consumer group {group_name} for {stream_name}")
    except redis.ResponseError as e:
        if "BUSYGROUP" in str(e):
            print(f"Consumer group {group_name} already exists for {stream_name}")
        else:
            raise

    # Attempt to create the consumer
    redis_client.xgroup_createconsumer(stream_name, group_name, consumer_name)
    print(
        f"Attempted to create consumer {consumer_name} for group {group_name} on stream {stream_name}"
    )

    # Verify consumer creation
    result = subprocess.run(
        ["redis-cli", "XINFO", "CONSUMERS", stream_name, group_name],
        capture_output=True,
        text=True,
        check=True,
    )
    print(f"\nRedis XINFO CONSUMERS output:\n{result.stdout}")

except Exception as e:
    print(f"An error occurred: {e}")
