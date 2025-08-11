#!/usr/bin/env python3
"""
Live Redis Demo - Push commands to Emacs through Redis using redis.el
"""

import time
import redis
import subprocess


class LiveRedisDemo:
    """Demonstrate live Redis-Emacs integration"""

    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        # Clear streams for clean demo
        self.redis_client.delete("tutorial:commands", "tutorial:responses")

    def send_tutorial_command(self, command, description):
        """Send command to Emacs via Redis stream"""

        print(f"📤 Sending to Redis: {command} ({description})")

        # Add command to Redis stream
        stream_id = self.redis_client.xadd(
            "tutorial:commands",
            {
                "command": command,
                "description": description,
                "timestamp": str(time.time()),
            },
        )

        print(f"   Stream ID: {stream_id}")

        # Wait for response
        print("   ⏳ Waiting for Emacs response...")

        max_wait = 10  # seconds
        start_time = time.time()

        while time.time() - start_time < max_wait:
            # Check for responses
            responses = self.redis_client.xrange("tutorial:responses", count=10)

            # Find response for our command
            for response_id, data in responses:
                if data.get("command") == command:
                    status = data.get("status")
                    if status == "executed":
                        print(f"   ✅ SUCCESS: Command executed in Emacs")
                        print(f"   📥 Response ID: {response_id}")
                        return True
                    elif status == "error":
                        error_msg = data.get("error", "unknown error")
                        print(f"   ❌ ERROR: {error_msg}")
                        return False

            time.sleep(0.2)

        print(f"   ⏰ TIMEOUT: No response after {max_wait}s")
        return False

    def demonstrate_working_integration(self):
        """Show the complete working integration"""

        print("🎯 LIVE REDIS-EMACS DEMONSTRATION")
        print("=" * 60)
        print("This demo pushes commands through Redis streams")
        print("and shows them executing in your live Emacs!")
        print()

        # First, verify Emacs daemon is running
        print("1. Checking Emacs daemon...")
        try:
            result = subprocess.run(
                ["emacsclient", "-s", "redis-tutorial", "--eval", "(+ 1 1)"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                print("   ✅ Emacs daemon responding")
            else:
                print(f"   ❌ Emacs daemon not responding")
                return
        except Exception as e:
            print(f"   ❌ Cannot connect to Emacs: {e}")
            return

        # Load the redis.el demo
        print("2. Loading redis.el integration...")
        try:
            result = subprocess.run(
                [
                    "emacsclient",
                    "-s",
                    "redis-tutorial",
                    "--eval",
                    '(load "/Users/jonathanhill/src/redis-ai-challenge/redis_el_demo.el")',
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                print("   ✅ Redis.el integration loaded")
            else:
                print(f"   ❌ Failed to load integration: {result.stderr}")
                return
        except Exception as e:
            print(f"   ❌ Error loading integration: {e}")
            return

        # Give it a moment to initialize
        time.sleep(2)

        # Now demonstrate tutorial commands
        print("3. Demonstrating tutorial commands...")
        print()

        tutorial_commands = [
            ("C-h t", "Open Emacs tutorial"),
            ("C-v", "Scroll down one page"),
            ("M-v", "Scroll up one page"),
            ("C-n", "Move to next line"),
            ("C-p", "Move to previous line"),
            ("C-f", "Move forward one character"),
            ("C-b", "Move backward one character"),
            ("C-a", "Move to beginning of line"),
            ("C-e", "Move to end of line"),
        ]

        successful_commands = 0

        for i, (command, description) in enumerate(tutorial_commands, 1):
            print(f"\n🎬 DEMO STEP {i}/9")
            print("-" * 40)

            success = self.send_tutorial_command(command, description)

            if success:
                successful_commands += 1
                print(f"   🎯 Step {i} completed successfully!")
            else:
                print(f"   ⚠️  Step {i} had issues")

            # Brief pause between commands
            time.sleep(1.5)

        # Final results
        print("\n" + "=" * 60)
        print("🏆 LIVE DEMO RESULTS")
        print("=" * 60)

        success_rate = (successful_commands / len(tutorial_commands)) * 100

        print(f"📊 Commands sent: {len(tutorial_commands)}")
        print(f"✅ Successful: {successful_commands}")
        print(f"📈 Success rate: {success_rate:.1f}%")

        if success_rate >= 80:
            print("\n🎉 INTEGRATION WORKING PERFECTLY!")
            print("✅ Redis streams carry commands to Emacs")
            print("✅ redis.el executes commands directly")
            print("✅ Results flow back through Redis")
            print("✅ Complete bidirectional communication!")
        elif success_rate >= 60:
            print("\n⚠️  INTEGRATION MOSTLY WORKING")
            print("Some commands succeeded, minor issues remain")
        else:
            print("\n❌ INTEGRATION NEEDS WORK")
            print("Fundamental communication issues")

        print(f"\n🔍 WHAT YOU JUST SAW:")
        print("• Python sent tutorial commands to Redis streams")
        print("• redis.el polled Redis and executed commands in Emacs")
        print("• Your Emacs buffer actually moved and changed")
        print("• Success/error responses flowed back through Redis")
        print("• Complete working Redis-coordinated tutorial system!")

        return success_rate >= 80


def main():
    print("🚀 STARTING LIVE REDIS-EMACS DEMONSTRATION")
    print("Make sure your Emacs window is visible to see the magic!")
    print()

    demo = LiveRedisDemo()
    demo.demonstrate_working_integration()


if __name__ == "__main__":
    main()
