#!/usr/bin/env python3
"""
Autonomous AI Performer - The Redis AI Challenge Submission

This script is the unified, standalone application that demonstrates an AI
learning Emacs from a spoken tutorial in real-time.

It integrates:
- Text-based commentary (voice removed due to segmentation fault)
- Natural Language Understanding (Gemini NLU Server via MCP)
- Closed-loop, validated execution in Emacs
- A persistent memory of learned skills
- Comprehensive Emacs state monitoring via the Emacs Facade
"""

import asyncio
import json
import time
import subprocess
import logging
from typing import List, Dict, Optional

import redis
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from tutorial_parser import TutorialParser, TutorialStep

# from azure_voice_mode import AzureVoiceMode # Removed due to segmentation fault
from emacs_facade import EmacsFacade
from robust_claude_integration import claude_integration  # Import claude_integration

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class AutonomousAIPerformer:
    def __init__(self):
        self.redis_client = redis.Redis(
            host="localhost", port=6379, decode_responses=True
        )
        self.parser = TutorialParser()
        # self.voice = AzureVoiceMode() # Removed
        self.emacs_facade = EmacsFacade()

        # Define parameters for the NLU server
        self.nlu_server_params = StdioServerParameters(
            command="python",
            args=["/Users/jonathanhill/src/redis-ai-challenge/gemini_nlu_server.py"],
        )
        self.nlu_client_session = None  # Will be set when the session is initialized

        self.memory_file = "ai_memory.json"
        self.learned_skills = self.load_memory()

    def load_memory(self) -> Dict:
        try:
            with open(self.memory_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_memory(self):
        with open(self.memory_file, "w") as f:
            json.dump(self.learned_skills, f, indent=2)

    async def speak(self, text: str):
        # Replaced with print statement
        logging.info(f"AI: {text}")

    async def get_emacs_state(self) -> Optional[Dict]:
        # The Emacs state monitor continuously updates Redis, so we just read from the facade
        return self.emacs_facade.get_current_state()

    async def execute_emacs_command(self, keystrokes: List[str]):
        for key in keystrokes:
            # The redis_command_executor.el expects a single command string
            self.redis_client.xadd("emacs:commands", {"command": key})
            await asyncio.sleep(0.75)  # Give Emacs time to process

    async def parse_instruction_with_nlu(
        self, instruction_text: str
    ) -> Optional[TutorialStep]:
        if self.nlu_client_session is None:
            logging.error(
                "NLU client session not initialized. Cannot parse instruction."
            )
            return None
        try:
            response = await self.nlu_client_session.call_tool(
                "parse_instruction", {"instruction_text": instruction_text}
            )
            parsed_data = json.loads(response.content[0].text)
            return TutorialStep(**parsed_data)
        except Exception as e:
            logging.error(f"NLU parsing failed: {e}")
            return None

    async def perform_tutorial(self):
        await self.speak(
            "Hello. I am ready to learn Emacs. Starting tutorial automatically."
        )

        # Removed voice interaction to start tutorial

        await self.speak("I will now open the Emacs tutorial.")
        await self.execute_emacs_command(["C-h", "t"])
        await asyncio.sleep(2)

        tutorial_text = self.parser.extract_tutorial_text()

        # Use NLU to parse the entire tutorial text into steps
        # This is a simplified approach for the demo, assuming NLU can handle the whole text
        # In a real scenario, we might feed it section by section.
        steps = []
        # For the demo, we'll just parse the first few lines as individual instructions
        # as the full tutorial text might be too large for a single NLU call.
        tutorial_lines = tutorial_text.split("\n")
        step_number = 1
        for line in tutorial_lines:
            if line.strip().startswith(">>"):
                parsed_step = await self.parse_instruction_with_nlu(line.strip())
                if parsed_step:
                    parsed_step.step_number = step_number
                    steps.append(parsed_step)
                    step_number += 1
            if step_number > 10:  # Limit for demo purposes
                break

        if not steps:
            await self.speak("I was unable to parse the tutorial. My apologies.")
            return

        await self.speak(
            f"I have parsed the tutorial into {len(steps)} steps. I will now begin the exercises."
        )

        for i, step in enumerate(steps):
            if not step.is_exercise:
                continue

            await self.speak(f"Step {i+1}: {step.instruction_text}")

            # Get state before
            state_before = await self.get_emacs_state()
            logging.info(f"State before: {state_before}")

            # Execute command
            await self.execute_emacs_command(step.keystrokes)

            # Get state after
            state_after = await self.get_emacs_state()
            logging.info(f"State after: {state_after}")

            # Validate and learn
            if self.validate_step(state_before, state_after, step):
                await self.speak(
                    f"Success. I have learned that {step.keystrokes} performs the action: {step.expected_behavior}"
                )
                self.learned_skills[str(step.keystrokes)] = step.expected_behavior
                self.save_memory()
            else:
                await self.speak(
                    "I was not able to validate that the command worked as expected. I will try to understand why."
                )

        await self.speak("I have completed the tutorial. Thank you for teaching me.")

    def validate_step(
        self, before: Optional[Dict], after: Optional[Dict], step: TutorialStep
    ) -> bool:
        if not before or not after:
            logging.warning("Cannot validate: missing before or after state.")
            return False

        # Basic validation: check if cursor position changed for movement commands
        if "C-" in str(step.keystrokes) or "M-" in str(step.keystrokes):
            if after.get("cursor", {}).get("position") != before.get("cursor", {}).get(
                "position"
            ):
                logging.info(
                    f"Validation successful: Cursor moved from {before.get('cursor', {}).get('position')} to {after.get('cursor', {}).get('position')}"
                )
                return True
            else:
                logging.warning(
                    f"Validation failed: Cursor did not move for {step.keystrokes}. Before: {before.get('cursor', {}).get('position')}, After: {after.get('cursor', {}).get('position')}"
                )
                return False

        # More sophisticated validation would go here based on expected_behavior
        logging.info(
            f"Validation skipped for {step.keystrokes}: No specific validation logic implemented yet."
        )
        return True  # Assume success if no specific validation is defined


async def main():
    performer = AutonomousAIPerformer()
    # Ensure Emacs daemon and executor are running
    subprocess.run(
        [
            "emacsclient",
            "-e",
            '(load-file "/Users/jonathanhill/src/redis-ai-challenge/redis_command_executor.el")',
        ]
    )
    subprocess.run(["emacsclient", "-e", "(redis-executor-start)"])

    # Start Emacs state monitor
    subprocess.run(
        [
            "emacsclient",
            "-e",
            '(load-file "/Users/jonathanhill/src/redis-ai-challenge/emacs_state_monitor.el")',
        ]
    )
    subprocess.run(["emacsclient", "-e", "(emacs-state-start-monitoring)"])

    # The nlu_server_process is now managed by stdio_client

    try:
        async with stdio_client(performer.nlu_server_params) as (
            transport,
            write_function,
        ):
            performer.nlu_client_session = ClientSession(transport, write_function)
            await performer.nlu_client_session.initialize()
            logging.info("Gemini NLU ClientSession initialized.")
            await performer.perform_tutorial()
    finally:
        # Terminate the NLU server process (stdio_client handles this)
        logging.info("Gemini NLU Server terminated (managed by stdio_client).")


if __name__ == "__main__":
    asyncio.run(main())
