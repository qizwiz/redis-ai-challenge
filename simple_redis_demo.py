#!/usr/bin/env python3
"""
Simple Redis Demo - Show single command execution
"""

import time
import redis
import subprocess


def demonstrate_single_command():
    """Show a single command working through Redis"""

    print("🎯 SIMPLE REDIS-EMACS COMMAND DEMO")
    print("=" * 50)
    print("This will send ONE command and show it executing!")
    print()

    redis_client = redis.Redis(decode_responses=True)

    # Clear streams
    redis_client.delete("simple:commands", "simple:responses")

    # Send a simple command
    command = "C-n"
    description = "Move to next line"

    print(f"📤 Sending command: {command} ({description})")

    stream_id = redis_client.xadd(
        "simple:commands",
        {"command": command, "description": description, "timestamp": str(time.time())},
    )

    print(f"   Stream ID: {stream_id}")

    # Now execute it manually in Emacs
    print("⚡ Executing in Emacs...")

    exec_elisp = f"""
(progn
  (let ((result (shell-command-to-string "redis-cli XREAD COUNT 1 STREAMS simple:commands 0")))
    (when (string-match "command.*{command}" result)
      (message "📥 Got command from Redis: {command}")
      (condition-case err
          (progn
            (execute-kbd-macro (kbd "{command}"))
            (shell-command-to-string "redis-cli XADD simple:responses '*' command {command} status executed")
            (message "✅ Executed: {command}"))
        (error 
         (shell-command-to-string "redis-cli XADD simple:responses '*' command {command} status error")
         (message "❌ Error: %s" (error-message-string err))))))
  "done")
"""

    try:
        result = subprocess.run(
            ["emacsclient", "-s", "redis-tutorial", "--eval", exec_elisp],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if "done" in result.stdout:
            print("   ✅ Emacs processed the command")

            # Check for response
            time.sleep(0.5)
            responses = redis_client.xrange("simple:responses")

            if responses:
                response_id, data = responses[0]
                status = data.get("status")

                print(f"📥 Response from Emacs: {status}")
                print(f"   Response ID: {response_id}")

                if status == "executed":
                    print("🎯 SUCCESS! The command executed in Emacs!")
                    print("   Your cursor should have moved down one line!")
                    return True
                else:
                    print("❌ Command failed to execute")
                    return False
            else:
                print("❌ No response from Emacs")
                return False
        else:
            print(f"❌ Emacs didn't process command: {result.stderr}")
            return False

    except Exception as e:
        print(f"💥 Error: {e}")
        return False


def show_redis_streams():
    """Show what's in Redis streams"""

    print("\n🔍 REDIS STREAMS CONTENT")
    print("=" * 50)

    redis_client = redis.Redis(decode_responses=True)

    print("Commands stream:")
    commands = redis_client.xrange("simple:commands")
    for cmd_id, data in commands:
        print(f"   {cmd_id}: {data}")

    print("\nResponses stream:")
    responses = redis_client.xrange("simple:responses")
    for resp_id, data in responses:
        print(f"   {resp_id}: {data}")


if __name__ == "__main__":
    print("🚀 SIMPLE REDIS COMMAND DEMONSTRATION")
    print("Make sure your Emacs window is visible!")
    print()

    success = demonstrate_single_command()
    show_redis_streams()

    if success:
        print("\n🎉 REDIS-EMACS INTEGRATION IS WORKING!")
        print("✅ Commands flow from Python → Redis → Emacs")
        print("✅ Responses flow from Emacs → Redis → Python")
        print("✅ Real Emacs commands execute!")
    else:
        print("\n⚠️  Integration needs debugging")
