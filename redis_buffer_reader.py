import redis
import json
import sys
import base64

def read_emacs_buffer_content(list_name, target_buffer_name):
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)

        # Get the last 100 elements from the list to check recent updates
        raw_entries = r.lrange(list_name, -100, -1) # Get last 100 entries

        latest_matching_content = None
        latest_matching_timestamp = -1.0 

        for raw_entry in reversed(raw_entries): 
            try:
                json_data = json.loads(raw_entry.decode('utf-8'))

                buffer_name = json_data.get('buffer-name')
                content_b64 = json_data.get('content')
                timestamp = json_data.get('timestamp', 0.0)

                if buffer_name == target_buffer_name:
                    if timestamp > latest_matching_timestamp:
                        decoded_content = base64.b64decode(content_b64).decode('utf-8')
                        latest_matching_content = decoded_content
                        latest_matching_timestamp = timestamp

            except json.JSONDecodeError as e:
                sys.stderr.write(f"Error decoding JSON from Redis list entry: {e}\n")
                sys.stderr.write(f"Raw entry: {raw_entry}\n")
            except base64.binascii.Error as e:
                sys.stderr.write(f"Error base64 decoding content: {e}\n")
            except Exception as e:
                sys.stderr.write(f"An unexpected error occurred during entry processing: {e}\n")

        return latest_matching_content

    except redis.exceptions.ConnectionError as e:
        sys.stderr.write(f"Could not connect to Redis: {e}\n")
        return None
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred: {e}\n")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: python redis_buffer_reader.py <redis_list_name> <target_buffer_name>\n")
        sys.exit(1)

    list_name = sys.argv[1]
    buffer_name = sys.argv[2]

    content = read_emacs_buffer_content(list_name, buffer_name)
    if content is not None:
        sys.stdout.write(content)
    else:
        sys.stdout.write("No content found for the specified buffer or error occurred.\n")