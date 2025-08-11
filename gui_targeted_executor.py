#!/usr/bin/env python3
"""
GUI-Targeted Executor - Execute commands in actual visible frames
"""
import redis
import subprocess
import time


class GUITargetedExecutor:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.last_id = "0"

    def start_executing(self):
        """Start executing commands targeted at GUI frames"""
        print("🎯 GUI-TARGETED EXECUTOR STARTED")
        print("Executing commands in actual visible frames...")
        print("-" * 60)

        while True:
            try:
                result = self.redis_client.xread(
                    {"emacs:gui-commands": self.last_id}, count=1, block=1000
                )

                if result:
                    stream_name, messages = result[0]
                    for message_id, fields in messages:
                        self.execute_in_gui(message_id, fields)
                        self.last_id = message_id

            except KeyboardInterrupt:
                print("\n⏹️ GUI Executor stopped")
                break
            except Exception as e:
                print(f"❌ GUI Executor error: {e}")
                time.sleep(1)

    def execute_in_gui(self, message_id, fields):
        """Execute command in GUI frame context"""
        step = fields.get("step", "?")
        elisp = fields.get("elisp", "")
        description = fields.get("description", "")

        print(f"🎯 GUI STEP {step}: {description}")

        # Wrap elisp to execute in visible frame context
        gui_elisp = f"""
(let ((gui-frame (seq-find (lambda (f) (frame-visible-p f)) (frame-list))))
  (when gui-frame
    (with-selected-frame gui-frame
      (let ((gui-window (frame-selected-window gui-frame)))
        (with-selected-window gui-window
          {elisp})))))
"""

        print(f"   Targeting GUI frame...")

        try:
            result = subprocess.run(
                ["emacsclient", "--eval", gui_elisp],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                print(f"   ✅ GUI SUCCESS: {result.stdout.strip()}")
            else:
                print(f"   ❌ GUI FAILED: {result.stderr.strip()}")

        except Exception as e:
            print(f"   💥 GUI ERROR: {e}")

        print()
        time.sleep(0.5)


if __name__ == "__main__":
    executor = GUITargetedExecutor()
    executor.start_executing()
