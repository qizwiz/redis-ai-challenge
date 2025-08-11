#!/usr/bin/env python3
"""
Real Tutorial System - Using our actual working AI with real Emacs
"""

import subprocess
import time
from intelligent_dev_assistant import IntelligentDevAssistant
from real_emacs_server import RealEmacsServer
import redis


def check_emacs_ready():
    """Check if Emacs is actually running and ready"""
    try:
        # Check if Emacs process exists
        result = subprocess.run(["pgrep", "emacs"], capture_output=True, text=True)
        emacs_running = result.returncode == 0

        if not emacs_running:
            print("❌ Emacs is not running")
            print("💡 Please start Emacs first:")
            print("   1. Open Emacs: emacs &")
            print("   2. Start server: M-x server-start")
            return False

        # Check if emacsclient works
        result = subprocess.run(
            ["emacsclient", "--eval", '(message "Tutorial system check")'],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            print("✅ Emacs server is ready")
            return True
        else:
            print("❌ Emacs server not ready")
            print("💡 In Emacs, run: M-x server-start")
            return False

    except Exception as e:
        print(f"❌ Error checking Emacs: {e}")
        return False


def setup_tutorial_buffer():
    """Create a real tutorial buffer in running Emacs"""
    print("\n🎯 Setting up tutorial buffer in real Emacs...")

    elisp_code = """
    (progn
      (switch-to-buffer "*AI-Tutorial-Real*")
      (erase-buffer)
      (insert "🤖 REAL AI TUTORIAL SESSION\\n")
      (insert "=================================\\n\\n")
      (insert "This AI is using our real intelligent development assistant\\n")
      (insert "with zero-timeout Redis coordination to learn Emacs.\\n\\n")
      (insert "Watch this buffer for real AI interactions!\\n\\n")
      (insert "Tutorial Steps:\\n")
      (insert "==============\\n\\n")
      (goto-char (point-max)))
    """

    try:
        result = subprocess.run(
            ["emacsclient", "--eval", elisp_code],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("✅ Tutorial buffer created in real Emacs")
            print("   Check your Emacs window for '*AI-Tutorial-Real*' buffer")
            return True
        else:
            print(f"❌ Failed to create buffer: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error creating buffer: {e}")
        return False


def log_to_emacs(message):
    """Log a message to the real Emacs tutorial buffer"""
    escaped_message = message.replace('"', '\\"').replace("\\", "\\\\")
    elisp_code = f"""
    (when (get-buffer "*AI-Tutorial-Real*")
      (with-current-buffer "*AI-Tutorial-Real*"
        (goto-char (point-max))
        (insert "{escaped_message}\\n")
        (goto-char (point-max))))
    """

    try:
        subprocess.run(
            ["emacsclient", "--eval", elisp_code],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except:
        pass


def perform_real_tutorial():
    """Perform tutorial using our real AI system"""

    print("🚀 REAL AI TUTORIAL SYSTEM")
    print("=" * 50)

    # Check prerequisites
    if not check_emacs_ready():
        return False

    if not setup_tutorial_buffer():
        return False

    # Initialize our real AI system
    assistant = IntelligentDevAssistant()
    assistant.update_context(
        working_directory="/Users/jonathanhill/src/redis-ai-challenge",
        current_file="real_tutorial_system.py",
        cursor_line=100,
        project_language="python",
    )

    log_to_emacs("🧠 Real AI assistant initialized")
    print("✅ Real AI assistant ready")

    # Tutorial commands to learn
    tutorial_commands = [
        "move cursor forward",
        "move cursor backward",
        "go to next line",
        "go to previous line",
        "move to beginning of line",
        "move to end of line",
    ]

    print(f"\n🎯 Starting real tutorial with {len(tutorial_commands)} commands...")
    log_to_emacs(f"Starting tutorial with {len(tutorial_commands)} commands...")

    results = []

    for i, command in enumerate(tutorial_commands, 1):
        print(f"\n📚 Step {i}: Learning '{command}'")
        log_to_emacs(f"Step {i}: Learning '{command}'")

        # Use our real AI to understand the command
        start_time = time.time()
        analysis = assistant.process_user_intent(command)
        ai_time = time.time() - start_time

        # Log AI analysis
        ai_result = f"AI Analysis: {analysis['intent']} (confidence: {analysis['confidence']:.2f}, method: {analysis['method']}, time: {ai_time:.3f}s)"
        print(f"   🧠 {ai_result}")
        log_to_emacs(f"   {ai_result}")

        # Convert to Emacs key binding
        key_binding = None
        if "forward" in command.lower():
            key_binding = "C-f"
        elif "backward" in command.lower():
            key_binding = "C-b"
        elif "next line" in command.lower():
            key_binding = "C-n"
        elif "previous line" in command.lower():
            key_binding = "C-p"
        elif "beginning" in command.lower():
            key_binding = "C-a"
        elif "end of line" in command.lower():
            key_binding = "C-e"

        if key_binding:
            # Execute the real command in Emacs
            print(f"   ⌨️  Executing: {key_binding}")
            log_to_emacs(f"   Executing: {key_binding}")

            try:
                # Execute the actual keystroke in Emacs
                exec_result = subprocess.run(
                    [
                        "emacsclient",
                        "--eval",
                        f'(call-interactively (key-binding "{key_binding}"))',
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if exec_result.returncode == 0:
                    success_msg = f"   ✅ Successfully executed {key_binding}"
                    print(success_msg)
                    log_to_emacs(success_msg)

                    # Get cursor position after command
                    pos_result = subprocess.run(
                        ["emacsclient", "--eval", "(point)"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )

                    if pos_result.returncode == 0:
                        position = pos_result.stdout.strip()
                        pos_msg = f"   📍 Cursor now at position: {position}"
                        print(pos_msg)
                        log_to_emacs(pos_msg)

                else:
                    error_msg = f"   ❌ Failed to execute {key_binding}"
                    print(error_msg)
                    log_to_emacs(error_msg)

            except Exception as e:
                error_msg = f"   ❌ Error executing {key_binding}: {e}"
                print(error_msg)
                log_to_emacs(error_msg)

        # Store results in Redis
        result_data = {
            "step": str(i),
            "command": command,
            "ai_intent": analysis["intent"],
            "ai_confidence": str(analysis["confidence"]),
            "ai_method": analysis["method"],
            "ai_time": str(ai_time),
            "key_binding": key_binding or "unknown",
            "timestamp": str(time.time()),
        }

        redis_client = redis.Redis(decode_responses=True)
        redis_client.xadd("real_tutorial:steps", result_data)

        results.append(result_data)

        # Pause between steps
        time.sleep(1)

    # Summary
    print(f"\n" + "=" * 50)
    print("🎉 REAL TUTORIAL COMPLETE")
    log_to_emacs("\\n🎉 REAL TUTORIAL COMPLETE")

    # Show statistics
    total_steps = len(results)
    fast_ai = len([r for r in results if float(r["ai_time"]) < 0.1])
    high_conf = len([r for r in results if float(r["ai_confidence"]) >= 0.8])

    stats = f"📊 Stats: {total_steps} steps, {fast_ai} fast AI responses, {high_conf} high confidence"
    print(stats)
    log_to_emacs(stats)

    # Redis verification
    tutorial_count = redis_client.xlen("real_tutorial:steps")
    redis_msg = f"📊 Redis: {tutorial_count} tutorial steps stored"
    print(redis_msg)
    log_to_emacs(redis_msg)

    print(
        "\n✅ Check your Emacs '*AI-Tutorial-Real*' buffer to see the complete session!"
    )

    return True


if __name__ == "__main__":
    perform_real_tutorial()
