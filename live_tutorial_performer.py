#!/usr/bin/env python3
"""
Live Tutorial Performer - Watch the AI Learn!
This script provides a live, closed-loop demonstration of the AI performing the Emacs tutorial.
It shows the AI's actions, the feedback from Emacs, and the validation of each step.
"""

import redis
import json
import time
import subprocess
from tutorial_parser import TutorialParser


class LiveTutorialPerformer:
    def __init__(self):
        self.redis_client = redis.Redis(
            host="localhost", port=6379, decode_responses=True
        )
        self.parser = TutorialParser()

    def get_emacs_state(self):
        """Get the current state of Emacs from Redis."""
        state_json = self.redis_client.get("emacs:state")
        if state_json:
            return json.loads(state_json)
        return None

    def report_emacs_state(self):
        """Tell Emacs to report its state."""
        subprocess.run(["emacsclient", "-e", "(redis-executor-report-state)"])

    def execute_command(self, commands):
        """Send a command to Emacs via Redis."""
        self.redis_client.xadd("emacs:commands", {"command": " ".join(commands)})

    async def run_tutorial(self):
        """Run the Emacs tutorial, with live commentary and validation."""
        print("--- Starting Live Emacs Tutorial Performance ---")

        # Get the tutorial steps
        steps = await self.parser.get_executable_steps()
        if not steps:
            print("Could not parse tutorial steps. Aborting.")
            return

        # Load the executor and start it
        subprocess.run(
            [
                "emacsclient",
                "-e",
                '(load-file "/Users/jonathanhill/src/redis-ai-challenge/redis_command_executor.el")',
            ]
        )
        subprocess.run(["emacsclient", "-e", "(redis-executor-start)"])
        time.sleep(1)

        for i, step in enumerate(steps):
            if i >= 10:  # Limit to the first 10 steps for this demo
                break

            print(f"\n--- Step {i+1}: {step.instruction_text} ---")

            # 1. Get state before
            print("Getting Emacs state before command...")
            self.report_emacs_state()
            time.sleep(0.5)
            state_before = self.get_emacs_state()
            if state_before:
                print(f"  - Cursor position: {state_before['position']}")

            # 2. Execute command
            print(f"Executing command: {step.keystrokes}")
            for key in step.keystrokes:
                self.execute_command(key)
                time.sleep(0.5)  # Give emacs time to process

            # 3. Get state after
            print("Getting Emacs state after command...")
            self.report_emacs_state()
            time.sleep(0.5)
            state_after = self.get_emacs_state()
            if state_after:
                print(f"  - Cursor position: {state_after['position']}")

            # 4. Validate and report
            if state_before and state_after:
                if state_after["position"] != state_before["position"]:
                    print("  ✅ Validation: Cursor position changed.")
                else:
                    print("  ⚠️  Validation: Cursor position did not change.")
            else:
                print("  Could not validate state change.")

        print("\n--- Live Tutorial Performance Complete ---")


if __name__ == "__main__":
    import asyncio

    performer = LiveTutorialPerformer()
    asyncio.run(performer.run_tutorial())
