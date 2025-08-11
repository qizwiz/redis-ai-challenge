#!/usr/bin/env python3
"""
Emacs AI Tutor - Autonomous tutorial performer with vocalized reasoning
Built on redis-ai-patterns library foundation

The killer demo: Watch AI actually learn Emacs while explaining its process
"""

import subprocess
import time
import re
from typing import Dict, List, Any, Optional
from redis_ai_patterns import (
    HomoiconicRedis,
    StreamProcessor,
    SemanticExtractor,
    DevAssistant,
)
from redis_ai_patterns.streams import StreamEvent, EventType
from redis_emacs_bridge import RedisEmacsBridge


class TutorialParser:
    """Parse Emacs tutorial into executable steps"""

    def __init__(self):
        self.lisp_engine = HomoiconicRedis(namespace="tutorial")

    def extract_tutorial_text(self) -> str:
        """Get the Emacs tutorial text"""
        try:
            # Get tutorial via Emacs batch mode
            result = subprocess.run(
                [
                    "emacs",
                    "--batch",
                    "--eval",
                    "(with-temp-buffer (help-with-tutorial) (buffer-string))",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
            else:
                print("DEBUG: Emacs command failed, using fallback")
                return self._get_basic_tutorial_steps()

        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("DEBUG: Emacs not found, using fallback")
            return self._get_basic_tutorial_steps()

    def _get_basic_tutorial_steps(self) -> str:
        """Fallback tutorial steps if Emacs unavailable"""
        return """
        EMACS TUTORIAL
        
        Emacs commands generally involve the CONTROL key (sometimes labeled CTRL or
        CTL) or the META key (sometimes labeled EDIT or ALT).
        
        >> Type C-v (View next screen) to move to the next screen.
        
        >> Now type C-p to move the cursor to the line above.
        
        >> Type C-f to move forward a character.
        
        >> Type C-b to move backward a character.
        
        >> Type C-n to move to next line.
        
        >> Type C-a to move to beginning of line.
        
        >> Type C-e to move to end of line.
        """

    def parse_into_steps(self, tutorial_text: str) -> List[Dict[str, Any]]:
        """Parse tutorial text into executable steps"""
        steps = []
        lines = tutorial_text.split("\n")

        for i, line in enumerate(lines):
            line = line.strip()

            # Look for instruction patterns like ">> Type C-v"
            if line.startswith(">>"):
                instruction = line[2:].strip()

                # Extract the key command
                key_match = re.search(r"Type\s+([C-][a-z]|[A-Z]-[a-z])", instruction)
                if key_match:
                    key_command = key_match.group(1)

                    # Get explanation (next non-empty line or within parens)
                    explanation = self._extract_explanation(instruction, lines, i)

                    step = {
                        "step_number": len(steps) + 1,
                        "instruction": instruction,
                        "key_command": key_command,
                        "explanation": explanation,
                        "emacs_command": self._translate_key_to_command(key_command),
                        "expected_behavior": self._extract_expected_behavior(
                            instruction
                        ),
                    }

                    # Store as executable Lisp in Redis
                    step_code = [
                        "tutorial-step",
                        step["step_number"],
                        step["key_command"],
                        step["explanation"],
                    ]
                    self.lisp_engine.store_code(f"step_{len(steps)}", step_code)

                    steps.append(step)

        return steps


class ActionExecutor:
    """Execute tutorial steps in Emacs via Redis bridge"""

    def __init__(self):
        self.event_processor = StreamProcessor(namespace="tutor_actions")
        self.emacs_bridge = RedisEmacsBridge(session_id="ai_tutor")
        self.current_step = 0

        # Set up the tutorial environment
        print("🎭 Setting up AI Tutorial environment via Redis...")
        self.emacs_bridge.create_tutorial_buffer()

    def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tutorial step and observe results"""
        step_id = f"step_{step['step_number']}"

        print(f"\n🎯 Executing Step {step['step_number']}: {step['instruction']}")

        # Record step start
        self.event_processor.add_event(
            StreamEvent(
                event_type=EventType.COMMAND,
                data={
                    "step_number": step["step_number"],
                    "key_command": step["key_command"],
                    "phase": "start",
                },
            )
        )

        # Execute the key command via Redis bridge
        execution_result = self.emacs_bridge.send_keyboard_command(step["key_command"])

        # Log the command execution in the tutorial buffer
        self.emacs_bridge.log_command_to_buffer(
            step["key_command"], f"{step['explanation']} (Step {step['step_number']})"
        )

        # Observe the result via Redis
        observation = self.emacs_bridge.observe_emacs_state()

        result = {
            "step_number": step["step_number"],
            "executed": execution_result["success"],
            "observation": observation,
            "expected_behavior": step["expected_behavior"],
            "actual_behavior": self._classify_behavior(observation),
            "success": self._evaluate_success(step, observation),
            "timestamp": time.time(),
        }

        # Record step completion
        self.event_processor.add_event(
            StreamEvent(
                event_type=EventType.COMMAND, data={**result, "phase": "complete"}
            )
        )

        return result

    def _evaluate_success(
        self, step: Dict[str, Any], observation: Dict[str, Any]
    ) -> bool:
        """Evaluate if step was executed successfully via Redis"""
        return (
            observation.get("method") == "redis_stream"
            and "cursor_position" in observation
        )


class ThoughtVocalizer:
    """Convert AI thoughts to speech and handle voice input"""

    def __init__(self):
        self.semantic_extractor = SemanticExtractor(namespace="tutor_thoughts")

    def speak_thought(self, thought: str, thought_type: str = "observation") -> None:
        """Convert thought to speech"""
        print(f"🤖💭 [{thought_type.upper()}] {thought}")

        # Store thought for analysis
        self.semantic_extractor.store_json(
            f"thought_{int(time.time())}",
            {"content": thought, "type": thought_type, "timestamp": time.time()},
        )

        # Use real TTS - make it actually speak
        try:
            subprocess.run(["say", thought], timeout=15)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("   (TTS not available - would be speaking)")
            pass

    def vocalize_step_reasoning(self, step: Dict[str, Any]) -> None:
        """Vocalize reasoning about a tutorial step"""
        reasoning = f"I need to execute {step['key_command']}. "
        reasoning += f"This should {step['explanation']}. "
        reasoning += f"The expected behavior is {step['expected_behavior']}."

        self.speak_thought(reasoning, "planning")

    def vocalize_execution_result(self, result: Dict[str, Any]) -> None:
        """Vocalize what happened after executing a step"""
        if result["success"]:
            observation = f"Step {result['step_number']} completed successfully. "
            observation += f"I observed {result['actual_behavior']}."
        else:
            observation = f"Step {result['step_number']} failed. "
            observation += "I need to understand what went wrong."

        self.speak_thought(observation, "reflection")


class EmacsAITutor:
    """Main autonomous Emacs tutor coordinator"""

    def __init__(self):
        self.tutorial_parser = TutorialParser()
        self.action_executor = ActionExecutor()
        self.thought_vocalizer = ThoughtVocalizer()
        self.dev_assistant = DevAssistant(namespace="tutor_learning")

        print("🚀 Emacs AI Tutor initialized - ready to learn!")

        # Check Redis connection for Emacs bridge
        self._check_redis_connection()

        self.thought_vocalizer.speak_thought(
            "Hello! I'm an AI that will learn the Emacs tutorial while explaining my reasoning. Let's begin!",
            "introduction",
        )

    def perform_tutorial(self) -> None:
        """Autonomously perform the complete Emacs tutorial"""
        # Parse tutorial into steps
        self.thought_vocalizer.speak_thought(
            "First, I'll parse the Emacs tutorial into executable steps.", "planning"
        )

        tutorial_text = self.tutorial_parser.extract_tutorial_text()
        steps = self.tutorial_parser.parse_into_steps(tutorial_text)

        self.thought_vocalizer.speak_thought(
            f"I found {len(steps)} tutorial steps to execute.", "analysis"
        )

        # Execute each step with vocalized reasoning
        for step in steps:
            # Vocalize plan
            self.thought_vocalizer.vocalize_step_reasoning(step)

            # Execute step
            result = self.action_executor.execute_step(step)

            # Vocalize result
            self.thought_vocalizer.vocalize_execution_result(result)

            # Pause between steps for comprehension
            time.sleep(2)

        self.thought_vocalizer.speak_thought(
            "Tutorial complete! I have learned the basic Emacs navigation commands through autonomous practice.",
            "completion",
        )

    def demonstrate_understanding(self) -> None:
        """Demonstrate learned competence"""
        self.thought_vocalizer.speak_thought(
            "Now I'll demonstrate my understanding by explaining what I learned.",
            "demonstration",
        )

        # Analyze stored execution data
        status = self.dev_assistant.get_system_status()
        self.thought_vocalizer.speak_thought(
            f"I executed {status.get('events:commands_length', 0)} commands during the tutorial.",
            "analysis",
        )


def main():
    """Run the autonomous Emacs tutorial performer"""
    tutor = EmacsAITutor()
    tutor.perform_tutorial()
    tutor.demonstrate_understanding()


if __name__ == "__main__":
    main()
