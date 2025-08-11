#!/usr/bin/env python3
"""
Quick Emacs state checker to determine current session type
"""
import redis
import json


def check_emacs_state():
    """
    TODO: Document check_emacs_state function

    This function requires documentation.
    Args and return value need to be documented based on the implementation.
    """
    try:
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)

        # Get current buffer info
        current_buffer = r.hgetall("emacs:current:buffer")
        all_buffers = r.get("emacs:current:buffers")

        print("=== CURRENT EMACS STATE ===")
        print(f"Active Buffer: {current_buffer.get('name', 'Unknown')}")
        print(f"Point: {current_buffer.get('point', 'Unknown')}")
        print(f"Line: {current_buffer.get('line', 'Unknown')}")
        print(f"Column: {current_buffer.get('column', 'Unknown')}")

        print("\n=== ALL BUFFERS ===")
        if all_buffers:
            buffers = all_buffers.split(",")
            helm_buffers = [b.strip() for b in buffers if "helm" in b.lower()]
            minibuf_buffers = [b.strip() for b in buffers if "*Minibuf" in b]

            print(f"Total buffers: {len(buffers)}")
            if helm_buffers:
                print(f"Helm buffers found: {helm_buffers}")
            if minibuf_buffers:
                print(f"Minibuffer activity: {minibuf_buffers}")

        # Check for message spam sources
        print("\n=== ACTIVITY CHECK ===")
        streams_to_check = [
            "emacs:commands",
            "emacs:responses",
            "emacs:keystrokes",
            "emacs:nlp-commands",
        ]
        for stream in streams_to_check:
            try:
                length = r.xlen(stream)
                print(f"{stream}: {length} messages")
            except:
                print(f"{stream}: Not found or empty")

        # Look for processes that might be spamming
        keys = r.keys("*")
        message_keys = [k for k in keys if "message" in k.lower()]
        spam_keys = [
            k
            for k in keys
            if any(word in k.lower() for word in ["spam", "flood", "rapid"])
        ]

        if message_keys:
            print(f"Message-related keys: {message_keys[:5]}...")  # Show first 5
        if spam_keys:
            print(f"Potential spam keys: {spam_keys}")

        return (
            current_buffer,
            all_buffers,
            helm_buffers if "helm_buffers" in locals() else [],
        )

    except Exception as e:
        print(f"Error checking state: {e}")
        return None, None, []


if __name__ == "__main__":
    check_emacs_state()
