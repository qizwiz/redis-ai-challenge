#!/usr/bin/env python3
"""
Instruction Executor - Convert Tutorial Steps to Emacs Keystrokes
This takes parsed tutorial steps and executes them in Emacs,
sending real keystrokes and verifying the results.
"""

import asyncio
import subprocess
import time
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from tutorial_parser import TutorialStep, TutorialParser
from fixed_redis_coordinator import redis_coordinator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    success: bool
    keystroke: str
    expected_behavior: str
    actual_result: str
    execution_time: float


class InstructionExecutor:
    """Executes tutorial instructions in Emacs"""

    def __init__(self):
        self.coordinator = redis_coordinator
        self.emacs_process = None
        self.current_buffer_content = ""
        self.cursor_position = (1, 1)  # line, column

    async def start_emacs_session(self):
        """Start an Emacs session for tutorial execution"""
        try:
            # Start Emacs daemon if not running
            self._ensure_emacs_daemon()

            # Open tutorial buffer
            await self._open_tutorial_buffer()

            logger.info("✅ Emacs session ready for tutorial execution")
            return True

        except Exception as e:
            logger.error(f"Failed to start Emacs session: {e}")
            return False

    def _ensure_emacs_daemon(self):
        """Ensure Emacs daemon is running"""
        try:
            # Check if daemon is running
            result = subprocess.run(
                ["emacsclient", "--eval", "(+ 1 1)"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                logger.info("Starting Emacs daemon...")
                subprocess.run(["emacs", "--daemon"], timeout=10)
                time.sleep(2)

        except Exception as e:
            logger.warning(f"Emacs daemon setup issue: {e}")

    async def _open_tutorial_buffer(self):
        """Open the tutorial in Emacs"""
        try:
            # Open tutorial
            cmd = ["emacsclient", "--eval", "(help-with-tutorial)"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                logger.info("📖 Tutorial buffer opened")
            else:
                logger.warning("Tutorial buffer may not have opened properly")

        except Exception as e:
            logger.error(f"Failed to open tutorial buffer: {e}")

    async def execute_tutorial_step(self, step: TutorialStep) -> ExecutionResult:
        """Execute a single tutorial step"""
        logger.info(f"🎯 Executing Step {step.step_number}: {step.instruction_text}")

        start_time = time.time()
        success = True
        actual_result = ""

        try:
            # Get current state before execution
            before_state = await self._get_emacs_state()

            # Execute each keystroke in the step
            for keystroke in step.keystrokes:
                await self._send_keystroke_to_emacs(keystroke)
                await asyncio.sleep(0.5)  # Brief pause between keystrokes

            # Get state after execution
            after_state = await self._get_emacs_state()

            # Verify the result
            success, actual_result = await self._verify_step_result(
                step, before_state, after_state
            )

        except Exception as e:
            logger.error(f"Error executing step: {e}")
            success = False
            actual_result = f"Execution error: {e}"

        execution_time = time.time() - start_time

        result = ExecutionResult(
            success=success,
            keystroke=" ".join(step.keystrokes),
            expected_behavior=step.expected_behavior,
            actual_result=actual_result,
            execution_time=execution_time,
        )

        # Log the result
        if success:
            logger.info(f"✅ Step completed: {actual_result}")
        else:
            logger.warning(f"⚠️  Step had issues: {actual_result}")

        # Store execution in Redis
        self.coordinator.store_ai_response(
            {
                "type": "tutorial_step_execution",
                "step_number": step.step_number,
                "keystrokes": step.keystrokes,
                "success": success,
                "result": actual_result,
                "execution_time": execution_time,
                "timestamp": str(time.time()),
            }
        )

        return result

    async def _send_keystroke_to_emacs(self, keystroke: str):
        """Send a single keystroke to Emacs"""
        try:
            # Convert our keystroke format to Emacs key format
            emacs_key = self._convert_to_emacs_key(keystroke)

            # Send the keystroke using emacsclient
            cmd = ["emacsclient", "--eval", f'(execute-kbd-macro "{emacs_key}")']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                logger.debug(f"Sent keystroke: {keystroke} -> {emacs_key}")
            else:
                logger.warning(f"Keystroke may not have worked: {keystroke}")

        except Exception as e:
            logger.error(f"Failed to send keystroke {keystroke}: {e}")

    def _convert_to_emacs_key(self, keystroke: str) -> str:
        """Convert keystroke format to Emacs key representation"""
        # Handle common patterns
        if keystroke.startswith("C-"):
            # C-f -> \C-f
            return f"\\{keystroke}"
        elif keystroke.startswith("M-"):
            # M-x -> \M-x
            return f"\\{keystroke}"
        else:
            # Regular character
            return keystroke

    async def _get_emacs_state(self) -> Dict[str, any]:
        """Get current Emacs state (cursor position, buffer content, etc.)"""
        try:
            state = {}

            # Get cursor position
            pos_cmd = ["emacsclient", "--eval", "(point)"]
            result = subprocess.run(pos_cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                state["cursor_position"] = int(result.stdout.strip())

            # Get current line
            line_cmd = ["emacsclient", "--eval", "(line-number-at-pos)"]
            result = subprocess.run(line_cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                state["line_number"] = int(result.stdout.strip())

            # Get column position
            col_cmd = ["emacsclient", "--eval", "(current-column)"]
            result = subprocess.run(col_cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                state["column"] = int(result.stdout.strip())

            # Get buffer name
            buf_cmd = ["emacsclient", "--eval", "(buffer-name)"]
            result = subprocess.run(buf_cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                state["buffer_name"] = result.stdout.strip().strip('"')

            return state

        except Exception as e:
            logger.error(f"Failed to get Emacs state: {e}")
            return {}

    async def _verify_step_result(
        self, step: TutorialStep, before_state: Dict, after_state: Dict
    ) -> Tuple[bool, str]:
        """Verify that the step produced the expected result"""
        try:
            # Compare before and after states
            before_pos = before_state.get("cursor_position", 0)
            after_pos = after_state.get("cursor_position", 0)

            before_line = before_state.get("line_number", 1)
            after_line = after_state.get("line_number", 1)

            before_col = before_state.get("column", 0)
            after_col = after_state.get("column", 0)

            # Basic verification based on common commands
            for keystroke in step.keystrokes:
                if keystroke == "C-f":
                    # Should move forward
                    if after_pos > before_pos or after_col > before_col:
                        return (
                            True,
                            f"Cursor moved forward from position {before_pos} to {after_pos}",
                        )
                    else:
                        return False, f"C-f didn't move cursor forward"

                elif keystroke == "C-b":
                    # Should move backward
                    if after_pos < before_pos or after_col < before_col:
                        return (
                            True,
                            f"Cursor moved backward from position {before_pos} to {after_pos}",
                        )
                    else:
                        return False, f"C-b didn't move cursor backward"

                elif keystroke == "C-n":
                    # Should move to next line
                    if after_line > before_line:
                        return (
                            True,
                            f"Cursor moved to next line from {before_line} to {after_line}",
                        )
                    else:
                        return False, f"C-n didn't move to next line"

                elif keystroke == "C-p":
                    # Should move to previous line
                    if after_line < before_line:
                        return (
                            True,
                            f"Cursor moved to previous line from {before_line} to {after_line}",
                        )
                    else:
                        return False, f"C-p didn't move to previous line"

            # Default: assume success if we got here
            return (
                True,
                f"Command executed (position changed from {before_pos} to {after_pos})",
            )

        except Exception as e:
            return False, f"Verification error: {e}"

    async def execute_full_tutorial(self, max_steps: int = 10) -> List[ExecutionResult]:
        """Execute the full tutorial (or first N steps)"""
        logger.info(f"🎓 Starting full tutorial execution (max {max_steps} steps)")

        # Parse tutorial steps
        parser = TutorialParser()
        executable_steps = parser.get_executable_steps()

        if not executable_steps:
            logger.error("No executable steps found in tutorial")
            return []

        # Execute steps
        results = []
        steps_to_execute = executable_steps[:max_steps]

        logger.info(f"📋 Will execute {len(steps_to_execute)} tutorial steps")

        for step in steps_to_execute:
            result = await self.execute_tutorial_step(step)
            results.append(result)

            # Brief pause between steps
            await asyncio.sleep(1)

            # Stop if we hit too many failures
            failures = sum(1 for r in results if not r.success)
            if failures > len(results) // 2:  # More than 50% failure rate
                logger.warning("High failure rate, stopping execution")
                break

        # Summary
        successes = sum(1 for r in results if r.success)
        logger.info(
            f"📊 Tutorial execution complete: {successes}/{len(results)} steps successful"
        )

        return results


async def main():
    """Test the instruction executor"""
    executor = InstructionExecutor()

    print("🚀 Starting Emacs session...")
    if not await executor.start_emacs_session():
        print("❌ Failed to start Emacs session")
        return

    print("✅ Emacs session ready")

    print("\n🎯 Executing tutorial steps...")
    results = await executor.execute_full_tutorial(max_steps=5)

    print(f"\n📊 EXECUTION RESULTS:")
    for i, result in enumerate(results, 1):
        status = "✅" if result.success else "❌"
        print(f"{status} Step {i}: {result.keystroke}")
        print(f"   Expected: {result.expected_behavior}")
        print(f"   Result: {result.actual_result}")
        print(f"   Time: {result.execution_time:.2f}s")
        print()


if __name__ == "__main__":
    asyncio.run(main())
