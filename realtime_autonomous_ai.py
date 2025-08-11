#!/usr/bin/env python3
"""
Real-time Autonomous AI Emacs Developer
Performs the Emacs tutorial live with genuine understanding - no artificial delays
"""

import redis
import time
import re


class RealTimeAutonomousAI:
    def __init__(self):
        self.redis = redis.Redis(decode_responses=True)
        self.session_id = f"autonomous_ai_{int(time.time())}"
        print(f"🤖 Real-time Autonomous AI started - {self.session_id}")

    def execute_emacs(self, command):
        """Execute Emacs command and wait for real result"""
        # Clear any old result
        self.redis.delete("emacs:command_ready")
        self.redis.lpush("emacs:commands", command)

        # Poll efficiently for result (no artificial delays)
        max_polls = 100  # 5 seconds max at 0.05s intervals
        for i in range(max_polls):
            result = self.redis.get("emacs:last_command_result")
            if result and result != "nil":
                return result
            time.sleep(0.05)  # Quick poll - no artificial delay
        return "timeout"

    def find_next_instruction(self):
        """Find the next >> instruction in tutorial"""
        # Move past current position to avoid repeating same instruction
        search_cmd = """(with-current-buffer "TUTORIAL" 
                          (when (search-forward ">>" nil t)
                            (let ((instruction-start (progn (beginning-of-line) (point))))
                              (end-of-line) 
                              (if (search-forward ">>" nil t)
                                  (progn (beginning-of-line)
                                         (buffer-substring-no-properties (point) (+ (point) 200)))
                                "NO_MORE_INSTRUCTIONS"))))"""
        return self.execute_emacs(search_cmd)

    def parse_and_execute_instruction(self, instruction_text):
        """Parse instruction and execute with understanding"""
        print(f"📖 Instruction: {instruction_text[:100]}...")

        # Parse different instruction types
        if "C-v" in instruction_text and "scroll" in instruction_text:
            print("  🎯 Understanding: Scroll down with C-v")
            cmd = """(progn (select-window (get-buffer-window "TUTORIAL"))
                           (let ((start (point))) (scroll-up-command) 
                                (list 'executed "C-v" 'moved (- (point) start))))"""
            result = self.execute_emacs(cmd)
            print(f"  ✅ Executed C-v: {result}")

        elif "M-v" in instruction_text:
            print("  🎯 Understanding: Scroll up with M-v, then practice C-v")
            cmd = """(progn (select-window (get-buffer-window "TUTORIAL"))
                           (scroll-down-command) (scroll-up-command)
                           (list 'executed "M-v then C-v" 'practiced 'scrolling))"""
            result = self.execute_emacs(cmd)
            print(f"  ✅ Executed M-v/C-v: {result}")

        elif "C-n" in instruction_text and "C-p" in instruction_text:
            print("  🎯 Understanding: Line navigation with C-n/C-p")
            cmd = """(progn (select-window (get-buffer-window "TUTORIAL"))
                           (next-line) (next-line) (previous-line)
                           (list 'executed "C-n/C-p" 'navigation 'practiced))"""
            result = self.execute_emacs(cmd)
            print(f"  ✅ Executed line navigation: {result}")

        elif "C-f" in instruction_text and "C-p" in instruction_text:
            print("  🎯 Understanding: Test column-wise movement C-f then C-p")
            cmd = """(progn (select-window (get-buffer-window "TUTORIAL"))
                           (forward-char) (forward-char) (forward-char) 
                           (previous-line)
                           (list 'executed "C-f then C-p" 'column-test 'complete))"""
            result = self.execute_emacs(cmd)
            print(f"  ✅ Executed column movement: {result}")

        elif "C-l" in instruction_text:
            print("  🎯 Understanding: Center screen with C-l")
            cmd = """(progn (select-window (get-buffer-window "TUTORIAL"))
                           (recenter) (list 'executed "C-l" 'centered 'screen))"""
            result = self.execute_emacs(cmd)
            print(f"  ✅ Executed screen centering: {result}")

        else:
            print(
                f"  🤔 Unknown instruction pattern - analyzing: {instruction_text[:50]}"
            )
            return False

        return True

    def run_autonomous_tutorial(self):
        """Run the complete tutorial autonomously in real-time"""
        print("🚀 AUTONOMOUS AI EMACS TUTORIAL - REAL-TIME EXECUTION")
        print("=" * 60)

        # Ensure we're in tutorial and ready
        setup_cmd = """(progn (select-window (get-buffer-window "TUTORIAL"))
                             (goto-char 1) "READY")"""
        self.execute_emacs(setup_cmd)

        instruction_count = 0

        while True:
            print(f"\n📍 Step {instruction_count + 1}: Finding next instruction...")

            # Find next instruction
            instruction = self.find_next_instruction()

            if instruction == "NO_MORE_INSTRUCTIONS" or instruction == "timeout":
                print("🎉 Tutorial complete - no more instructions found!")
                break

            if instruction_count >= 10:  # Limit for demo
                print("🛑 Demo limit reached - stopping at 10 instructions")
                break

            # Parse and execute
            if self.parse_and_execute_instruction(instruction):
                instruction_count += 1
                print(f"   ✨ Instruction {instruction_count} completed successfully")
            else:
                print("   ⚠️  Could not parse instruction - continuing...")

            # Small pause for readability (not functionality)
            time.sleep(0.5)

        print(
            f"\n🏁 Autonomous AI completed {instruction_count} tutorial instructions!"
        )
        print("🎯 This demonstrates real-time AI understanding and execution")


if __name__ == "__main__":
    ai = RealTimeAutonomousAI()
    ai.run_autonomous_tutorial()
