#!/usr/bin/env python3
"""
Test Reactive Detection
Show that the facade detects user changes, not just AI commands
"""

import redis
import time
import json


def main():
    print("🔍 **TESTING REACTIVE DETECTION**")
    print("=" * 50)

    redis_client = redis.Redis(decode_responses=True)

    print("🎯 Watching for changes in the last 10 seconds...")
    print("   (Go split/merge windows in Emacs NOW!)")

    # Watch for changes
    start_time = time.time()
    changes_detected = []

    while time.time() - start_time < 10:
        try:
            # Get recent changes from the reactive facade
            recent = redis_client.xrevrange("emacs:live_changes", count=5)

            for change_id, fields in recent:
                timestamp = float(fields.get("timestamp", 0))
                if timestamp > start_time:
                    changes_detected.append(
                        {
                            "id": change_id,
                            "timestamp": timestamp,
                            "source": fields.get("source", "unknown"),
                            "changes": json.loads(fields.get("changes", "[]")),
                        }
                    )

            time.sleep(0.5)
        except:
            time.sleep(0.5)

    if changes_detected:
        print(f"\n✅ **DETECTED {len(changes_detected)} CHANGES!**")
        for change in changes_detected:
            time_str = time.strftime("%H:%M:%S", time.localtime(change["timestamp"]))
            source = change["source"].upper()
            changes_list = [c["type"] for c in change["changes"]]
            print(f"   [{time_str}] {source}: {changes_list}")

        # Check if any were user actions
        user_actions = [c for c in changes_detected if c["source"] == "user_action"]
        if user_actions:
            print(f"\n🎉 **REACTIVE FACADE IS WORKING!**")
            print(f"   Detected {len(user_actions)} USER-initiated changes!")
            print(
                "   This proves the facade monitors YOUR actions, not just AI commands!"
            )
        else:
            print(f"\n🤖 Only AI-initiated changes detected")
            print("   Try manually splitting/merging windows in Emacs")
    else:
        print("\n📊 No changes detected in the monitoring window")
        print("   The reactive facade server may not be running")
        print("   Or try making changes in Emacs (split windows, switch buffers)")


if __name__ == "__main__":
    main()
