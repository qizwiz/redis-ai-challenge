#!/usr/bin/env python3
"""
Test if we can make the Redis-Emacs bridge actually work
"""

import time
import redis
import subprocess


def test_emacs_redis_integration():
    """Test the complete integration"""

    print("🧪 TESTING REAL EMACS-REDIS INTEGRATION")
    print("=" * 60)

    redis_client = redis.Redis(decode_responses=True)

    # Test 1: Check if Emacs daemon is running
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
            print(f"   ❌ Emacs daemon not responding: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot connect to Emacs daemon: {e}")
        return False

    # Test 2: Check if Redis bridge is loaded
    print("2. Checking Redis bridge...")
    try:
        result = subprocess.run(
            ["emacsclient", "-s", "redis-tutorial", "--eval", "redis-bridge-active"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if "t" in result.stdout:
            print("   ✅ Redis bridge is active")
        else:
            print(f"   ❌ Redis bridge not active: {result.stdout}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot check bridge status: {e}")
        return False

    # Test 3: Manual command execution test
    print("3. Testing manual command execution...")
    try:
        result = subprocess.run(
            [
                "emacsclient",
                "-s",
                "redis-tutorial",
                "--eval",
                '(execute-kbd-macro (kbd "C-g"))',
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        print("   ✅ Manual command execution works")
    except Exception as e:
        print(f"   ❌ Manual command execution failed: {e}")
        return False

    # Test 4: Test Redis connection from Emacs
    print("4. Testing Redis from Emacs...")
    test_cmd = "redis-cli PING"
    try:
        result = subprocess.run(
            [
                "emacsclient",
                "-s",
                "redis-tutorial",
                "--eval",
                f'(shell-command-to-string "{test_cmd}")',
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if "PONG" in result.stdout:
            print("   ✅ Emacs can reach Redis")
        else:
            print(f"   ❌ Emacs cannot reach Redis: {result.stdout}")
            return False
    except Exception as e:
        print(f"   ❌ Redis test from Emacs failed: {e}")
        return False

    # Test 5: Direct polling test
    print("5. Testing direct Redis polling...")

    # Clear Redis first
    redis_client.flushdb()

    # Add a test command
    stream_id = redis_client.xadd(
        "emacs:commands", {"action": "test", "command": "C-g"}
    )
    print(f"   📤 Added test command: {stream_id}")

    # Try to read it from Emacs
    read_cmd = "redis-cli XREAD COUNT 1 STREAMS emacs:commands 0"
    try:
        result = subprocess.run(
            [
                "emacsclient",
                "-s",
                "redis-tutorial",
                "--eval",
                f'(shell-command-to-string "{read_cmd}")',
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if "C-g" in result.stdout:
            print("   ✅ Emacs can read from Redis stream")
            print(f"   📥 Got: {result.stdout.strip()}")
        else:
            print(f"   ❌ Emacs cannot read from Redis stream: {result.stdout}")
            return False
    except Exception as e:
        print(f"   ❌ Redis read test failed: {e}")
        return False

    # Test 6: Complete workflow test
    print("6. Testing complete workflow...")

    # Inject a command that will execute and respond
    workflow_elisp = """
(progn
  (let ((result (shell-command-to-string "redis-cli XREAD COUNT 1 STREAMS emacs:commands 0")))
    (when (string-match "command.*C-g" result)
      (execute-kbd-macro (kbd \"C-g\"))
      (shell-command-to-string "redis-cli XADD emacs:responses * command C-g status executed")
      (message "✅ Workflow test completed")))
  "workflow-test-done")
"""

    try:
        result = subprocess.run(
            ["emacsclient", "-s", "redis-tutorial", "--eval", workflow_elisp],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if "workflow-test-done" in result.stdout:
            print("   ✅ Workflow executed")

            # Check for response
            responses = redis_client.xrange("emacs:responses")
            if responses:
                print(f"   ✅ Got response: {responses[0]}")
                return True
            else:
                print("   ❌ No response in Redis")
                return False
        else:
            print(f"   ❌ Workflow failed: {result.stdout}")
            return False

    except Exception as e:
        print(f"   ❌ Workflow test failed: {e}")
        return False


def run_actual_tutorial_if_working():
    """Run the actual tutorial if the integration works"""

    if not test_emacs_redis_integration():
        print("❌ Integration not working - cannot run tutorial")
        return

    print("\n🎓 RUNNING ACTUAL TUTORIAL")
    print("=" * 60)

    redis_client = redis.Redis(decode_responses=True)
    redis_client.flushdb()

    # Tutorial steps
    tutorial_steps = [
        ("C-h t", "Open tutorial"),
        ("C-v", "Scroll down"),
        ("M-v", "Scroll up"),
        ("C-n", "Next line"),
        ("C-p", "Previous line"),
        ("C-f", "Forward char"),
        ("C-b", "Backward char"),
    ]

    successful_steps = 0

    for i, (command, description) in enumerate(tutorial_steps, 1):
        print(f"\n{i}. {description}: {command}")

        # Send command to Redis
        stream_id = redis_client.xadd(
            "emacs:commands", {"action": "tutorial", "command": command, "step": i}
        )
        print(f"   📤 Sent: {stream_id}")

        # Execute via Emacs
        exec_elisp = f"""
(progn
  (let ((result (shell-command-to-string "redis-cli XREAD COUNT 1 STREAMS emacs:commands 0")))
    (when (string-match "command.*{command}" result)
      (condition-case err
          (progn
            (execute-kbd-macro (kbd "{command}"))
            (shell-command-to-string "redis-cli XADD emacs:responses * command {command} status executed step {i}")
            (message "✅ Executed: {command}"))
        (error 
         (shell-command-to-string "redis-cli XADD emacs:responses * command {command} status error")
         (message "❌ Error executing: {command}")))))
  "step-{i}-done")
"""

        try:
            result = subprocess.run(
                ["emacsclient", "-s", "redis-tutorial", "--eval", exec_elisp],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if f"step-{i}-done" in result.stdout:
                # Check response
                responses = redis_client.xrange("emacs:responses", count=1)
                if responses:
                    _, data = responses[-1]
                    if data.get("status") == "executed":
                        print(f"   ✅ Success: {command}")
                        successful_steps += 1
                    else:
                        print(f"   ❌ Failed: {data.get('status', 'unknown')}")
                else:
                    print(f"   ❌ No response")
            else:
                print(f"   ❌ Execution failed")

        except Exception as e:
            print(f"   💥 Error: {e}")

        time.sleep(1)

    # Results
    success_rate = (successful_steps / len(tutorial_steps)) * 100
    print(f"\n🏆 RESULTS:")
    print(f"   📊 Steps: {len(tutorial_steps)}")
    print(f"   ✅ Successful: {successful_steps}")
    print(f"   📈 Success rate: {success_rate:.1f}%")

    if success_rate >= 80:
        print("   🎯 TUTORIAL SYSTEM WORKING!")
    else:
        print("   ⚠️  Tutorial system needs improvement")


if __name__ == "__main__":
    run_actual_tutorial_if_working()
