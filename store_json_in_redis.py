import redis
import json
import sys

def store_json(file_path, redis_key):
    with open(file_path, 'r') as f:
        json_content = f.read()

    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.set(redis_key, json_content)
    print(f"Successfully stored {redis_key} in Redis.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python store_json_in_redis.py <json_file_path> <redis_key>")
        sys.exit(1)
    store_json(sys.argv[1], sys.argv[2])
