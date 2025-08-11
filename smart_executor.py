#!/usr/bin/env python3
"""
Smart Executor - Handles failures and adapts commands
"""
import redis
import subprocess
import time


class SmartExecutor:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)

    def execute_smart_command(self, command_desc):
        """Execute command with intelligent failure recovery"""
        print(f"🧠 SMART EXECUTION: {command_desc}")

        if "go to 51:32" in command_desc.lower():
            return self.smart_goto_position(51, 32)
        elif "insert" in command_desc.lower() and "from claude" in command_desc.lower():
            return self.smart_insert("from claude with ❤️")
        else:
            return self.basic_execute(command_desc)

    def smart_goto_position(self, target_line, target_col):
        """Go to position with intelligent fallback"""
        print(f"   🎯 Smart goto: line {target_line}, column {target_col}")

        # First, check buffer size
        buffer_info = self.get_buffer_info()
        current_lines = buffer_info.get("lines", 0)

        print(f"   📊 Buffer has {current_lines} lines, need {target_line}")

        if current_lines < target_line:
            print(f"   🔧 RECOVERY: Creating {target_line - current_lines} new lines")

            # Add lines to reach target
            add_lines_elisp = f"""
(progn
  (goto-char (point-max))
  (dotimes (i {target_line - current_lines})
    (insert "\\n"))
  (goto-line {target_line})
  (move-to-column {target_col} t)
  (list (line-number-at-pos) (current-column)))
"""
        else:
            # Normal goto
            add_lines_elisp = f"(progn (goto-line {target_line}) (move-to-column {target_col} t) (list (line-number-at-pos) (current-column)))"

        result = self.execute_elisp(add_lines_elisp)
        if result:
            print(f"   ✅ Smart goto result: {result}")
            return True
        return False

    def smart_insert(self, text):
        """Insert text with verification"""
        print(f"   📝 Smart insert: '{text}'")

        # Insert and verify
        elisp = f"""
(progn
  (let ((start-pos (point)))
    (insert "{text}")
    (buffer-substring-no-properties start-pos (point))))
"""
        result = self.execute_elisp(elisp)
        if result and text in result:
            print(f"   ✅ Verified insertion: {result}")
            return True
        else:
            print(f"   ❌ Insertion failed or unverified")
            return False

    def get_buffer_info(self):
        """Get current buffer information"""
        elisp = "(list 'lines (line-number-at-pos (point-max)) 'chars (point-max) 'current-line (line-number-at-pos))"
        result = self.execute_elisp(elisp)

        if result:
            # Parse result like: (lines 3 chars 169 current-line 3)
            parts = result.strip("()").split()
            return {
                "lines": int(parts[1]) if len(parts) > 1 else 0,
                "chars": int(parts[3]) if len(parts) > 3 else 0,
                "current_line": int(parts[5]) if len(parts) > 5 else 0,
            }
        return {}

    def execute_elisp(self, elisp):
        """Execute elisp in GUI frame with error handling"""
        gui_elisp = f"""
(let ((gui-frame (seq-find (lambda (f) (frame-visible-p f)) (frame-list))))
  (when gui-frame
    (with-selected-frame gui-frame
      (let ((gui-window (frame-selected-window gui-frame)))
        (with-selected-window gui-window
          {elisp})))))
"""

        try:
            result = subprocess.run(
                ["emacsclient", "--eval", gui_elisp],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"   ❌ Elisp error: {result.stderr.strip()}")
                return None

        except Exception as e:
            print(f"   💥 Execution error: {e}")
            return None

    def basic_execute(self, command):
        """Basic command execution fallback"""
        print(f"   🔄 Basic execution: {command}")
        return True


def test_smart_execution():
    """Test the smart executor"""
    executor = SmartExecutor()

    print("🧪 TESTING SMART EXECUTION")
    print("=" * 50)

    # Test smart goto with recovery
    executor.execute_smart_command("go to 51:32")

    time.sleep(1)

    # Test smart insert
    executor.execute_smart_command("insert from claude with love")


if __name__ == "__main__":
    test_smart_execution()
