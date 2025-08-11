#!/usr/bin/env python3
"""
AI Assistant - Actually use the learning AI to help you work
"""

import subprocess
import sys
from genuine_ai_learning import RealLearner


class WorkingAIAssistant:
    """AI assistant that you actually use to get work done"""

    def __init__(self):
        """Initializes the WorkingAIAssistant."""
        self.learner = RealLearner()
        self.emacs_available = self._check_emacs()

    def _check_emacs(self) -> bool:
        """Check if the Emacs server is running and accessible."""
        try:
            result = subprocess.run(
                ["emacsclient", "--eval", "t"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def do(self, command: str) -> bool:
        """Actually do what the user asks"""

        # Let the AI figure out what to do
        result = self.learner.attempt_command(command)

        if result["execution"]["outcome"] == "success":
            # Execute the actual command
            key_binding = result["execution"].get("key_used")

            if key_binding and self.emacs_available:
                try:
                    # Actually execute in Emacs
                    if key_binding.startswith("M-x"):
                        # Handle M-x commands
                        cmd = key_binding.replace("M-x ", "")
                        elisp = f'(call-interactively (intern "{cmd}"))'
                    else:
                        # Handle key bindings
                        elisp = f'(call-interactively (key-binding "{key_binding}"))'

                    exec_result = subprocess.run(
                        ["emacsclient", "--eval", elisp],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    if exec_result.returncode == 0:
                        print(f"✅ Done: {command}")
                        return True
                    else:
                        print(f"❌ Failed to execute: {exec_result.stderr}")
                        return False

                except Exception as e:
                    print(f"❌ Error: {e}")
                    return False
            else:
                if not self.emacs_available:
                    print(f"💡 Would execute: {key_binding}")
                    print(
                        "   (Start Emacs and run M-x server-start to enable real execution)"
                    )
                else:
                    print(
                        f"💡 Would do: {result['execution'].get('action', 'unknown action')}"
                    )
                return True
        else:
            print(f"❌ Don't know how to: {command}")
            return False


def main():
    """Command line AI assistant"""

    if len(sys.argv) < 2:
        print("🤖 AI Assistant - Tell me what to do!")
        print()
        print("Usage:")
        print("  python ai_assistant.py 'move cursor forward'")
        print("  python ai_assistant.py 'save this file'")
        print("  python ai_assistant.py 'show git status'")
        print()
        print("Interactive mode:")
        print("  python ai_assistant.py --interactive")
        return

    if sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        # Single command mode
        command = " ".join(sys.argv[1:])
        ai = WorkingAIAssistant()
        ai.do(command)


def interactive_mode():
    """Interactive AI assistant"""

    print("🤖 Interactive AI Assistant")
    print("=" * 40)
    print("Tell me what to do and I'll try to do it!")
    print("Type 'quit' to exit")
    print()

    ai = WorkingAIAssistant()

    if ai.emacs_available:
        print("✅ Connected to Emacs - I can actually execute commands")
    else:
        print("⚠️  Emacs not available - I'll show you what I would do")
        print("💡 Start Emacs and run M-x server-start for real execution")
    print()

    while True:
        try:
            command = input("🗣️  What should I do? ").strip()

            if command.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break
            elif not command:
                continue

            print(f"🤔 Working on: {command}")
            success = ai.do(command)

            if success:
                print("🎉 Task completed!")
            else:
                print("😞 Couldn't complete that task")
            print()

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    main()
