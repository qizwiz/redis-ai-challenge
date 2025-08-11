#!/usr/bin/env python3
"""
Verify Facade System
Check that the facade accurately represents Emacs state
"""

import redis
import json
import subprocess
import time


class FacadeVerifier:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)

    def get_facade_state(self):
        """Get current facade state"""
        try:
            facade_json = self.redis_client.get("emacs:facade")
            if facade_json:
                return json.loads(facade_json)
            return None
        except:
            return None

    def get_real_emacs_state(self):
        """Get actual Emacs state via emacsclient"""
        try:
            # Get window count
            window_count = subprocess.run(
                ["emacsclient", "--eval", "(length (window-list))"],
                capture_output=True,
                text=True,
            ).stdout.strip()

            # Get current buffer
            current_buffer = (
                subprocess.run(
                    ["emacsclient", "--eval", "(buffer-name)"],
                    capture_output=True,
                    text=True,
                )
                .stdout.strip()
                .strip('"')
            )

            # Get buffer contents
            buffer_contents = (
                subprocess.run(
                    ["emacsclient", "--eval", "(buffer-string)"],
                    capture_output=True,
                    text=True,
                )
                .stdout.strip()
                .strip('"')
            )

            return {
                "window_count": int(window_count),
                "current_buffer": current_buffer,
                "buffer_contents": buffer_contents,
            }
        except Exception as e:
            print(f"Error getting real state: {e}")
            return None

    def verify_state_sync(self):
        """Verify facade matches reality"""
        print("🔍 **FACADE VERIFICATION**")
        print("=" * 40)

        facade_state = self.get_facade_state()
        real_state = self.get_real_emacs_state()

        if not facade_state:
            print("❌ No facade state found in Redis")
            return False

        if not real_state:
            print("❌ Could not get real Emacs state")
            return False

        print(f"📊 Facade State:")
        if facade_state:
            windows = facade_state.get("windows", {})
            buffers = facade_state.get("buffers", {})
            print(f"   Windows: {windows.get('count', 'unknown')}")
            print(f"   Current Buffer: {buffers.get('current', 'unknown')}")

        print(f"\n🎯 Real Emacs State:")
        print(f"   Windows: {real_state['window_count']}")
        print(f"   Current Buffer: {real_state['current_buffer']}")

        # Verify synchronization
        sync_issues = []

        if facade_state.get("windows", {}).get("count") != real_state["window_count"]:
            sync_issues.append(
                f"Window count mismatch: facade={facade_state.get('windows', {}).get('count')}, real={real_state['window_count']}"
            )

        if (
            facade_state.get("buffers", {}).get("current")
            != real_state["current_buffer"]
        ):
            sync_issues.append(
                f"Buffer mismatch: facade={facade_state.get('buffers', {}).get('current')}, real={real_state['current_buffer']}"
            )

        if sync_issues:
            print(f"\n❌ **SYNCHRONIZATION ISSUES:**")
            for issue in sync_issues:
                print(f"   • {issue}")
            return False
        else:
            print(f"\n✅ **FACADE IS SYNCHRONIZED!**")
            return True

    def test_command_verification(self):
        """Test sending a command and verifying facade updates"""
        print("\n🧪 **TESTING COMMAND VERIFICATION**")
        print("=" * 40)

        # Get initial state
        initial_windows = self.get_real_emacs_state()["window_count"]
        print(f"Initial windows: {initial_windows}")

        # Send split command
        print("📤 Sending split-window-right command...")
        self.redis_client.xadd("emacs:commands", {"action": "split-window-right"})

        # Wait for processing
        time.sleep(2)

        # Check results
        new_windows = self.get_real_emacs_state()["window_count"]
        print(f"Windows after command: {new_windows}")

        if new_windows > initial_windows:
            print("✅ Command executed successfully!")

            # Check if facade updated
            facade_state = self.get_facade_state()
            if (
                facade_state
                and facade_state.get("windows", {}).get("count") == new_windows
            ):
                print("✅ Facade synchronized!")
                return True
            else:
                print("❌ Facade not synchronized")
                return False
        else:
            print("❌ Command did not execute")
            return False


def main():
    verifier = FacadeVerifier()

    # Basic verification
    sync_ok = verifier.verify_state_sync()

    # Command test
    # command_ok = verifier.test_command_verification()

    if sync_ok:
        print(f"\n🌟 **FACADE SYSTEM IS WORKING!**")
    else:
        print(f"\n⚠️ **FACADE NEEDS SYNCHRONIZATION**")


if __name__ == "__main__":
    main()
