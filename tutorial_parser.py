#!/usr/bin/env python3
"""
Tutorial Parser - Extract and Parse Real Emacs Tutorial
This extracts the actual Emacs tutorial and converts it into structured steps
that an AI can follow like a human learning Emacs.
"""

import re
import subprocess
import logging
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from robust_claude_integration import claude_integration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TutorialStep:
    step_number: int
    instruction_text: str
    keystrokes: List[str]
    expected_behavior: str
    section: str
    is_exercise: bool = False


class TutorialParser:
    """Parses the real Emacs tutorial into executable steps"""

    def __init__(self):
        self.tutorial_text = ""
        self.parsed_steps: List[TutorialStep] = []

    def extract_tutorial_text(self) -> str:
        """Extract the actual Emacs tutorial text"""
        try:
            # Get the tutorial using emacs --batch
            result = subprocess.run(
                [
                    "emacs",
                    "--batch",
                    "--eval",
                    "(progn (help-with-tutorial) (princ (buffer-string)))",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                self.tutorial_text = result.stdout
                logger.info(f"Extracted tutorial: {len(self.tutorial_text)} characters")
                return self.tutorial_text
            else:
                logger.error(f"Failed to extract tutorial: {result.stderr}")
                return self._get_fallback_tutorial()

        except Exception as e:
            logger.error(f"Error extracting tutorial: {e}")
            return self._get_fallback_tutorial()

    def _get_fallback_tutorial(self) -> str:
        """Fallback tutorial content if extraction fails"""
        return """
EMACS TUTORIAL

Emacs commands generally involve the CONTROL key (sometimes labeled
CTRL or CTL) or the META key (sometimes labeled EDIT or ALT). Rather than
write that in full each time, we'll use the following abbreviations:

 C-<chr>  means hold the CONTROL key while typing the character <chr>
          Thus, C-f would be: hold the CONTROL key and type f.
 M-<chr>  means hold the META or EDIT or ALT key down while typing <chr>.

Important note: to end the Emacs session, type C-x C-c.

>> The characters ">>" at the left margin indicate directions for you to
try using a command. For instance:

<<Blank lines inserted around following line by help-with-tutorial>>
[Middle of page left blank for practice]
<<Blank lines inserted around following line by help-with-tutorial>>

>> Now type C-v (View next screen) to move to the next screen.

The most basic cursor motion commands are C-f, C-b, C-n, and C-p.

>> Try moving around with these commands:
   C-f  Move forward a character
   C-b  Move backward a character
   C-n  Move to next line
   C-p  Move to previous line

>> Try C-f now to move the cursor forward by one character.

You should see the cursor advance to the next character.

>> Try C-n to move down to the next line.

>> Try C-p to move back up.

>> Try C-b to move backward.

You can repeat a command by giving it a numeric argument.
For example, type C-u 8 C-f to move forward eight characters.

>> Try it now: C-u 8 C-f

>> Try moving backward: C-u 8 C-b

The preceding commands move the cursor, but do not change the text.
        """

    async def parse_tutorial_steps_with_nlu(self) -> List[TutorialStep]:
        """Parse tutorial text into structured steps using NLU"""
        if not self.tutorial_text:
            self.extract_tutorial_text()

        prompt = f"""
You are an expert Emacs user and a parsing specialist. Your task is to read the following Emacs tutorial text and convert it into a structured JSON format.

The JSON output should be a list of objects, where each object represents a single, executable step for a beginner to follow.

For each step, provide the following fields:
- "step_number": An integer starting from 1.
- "instruction_text": The exact, complete instruction from the tutorial.
- "keystrokes": A list of the precise keystrokes to be executed. For example, ["C-f"], ["C-x", "C-s"], ["M-x", "auto-fill-mode"].
- "expected_behavior": A clear and concise description of what should happen when the keystrokes are executed.
- "section": The name of the tutorial section the instruction belongs to.
- "is_exercise": A boolean that is true if the instruction is a hands-on exercise (usually marked with ">>" ).

Here is the tutorial text:

{self.tutorial_text}
"""

        response = claude_integration.execute_prompt(prompt, timeout=120)
        if not response.success:
            logger.error("NLU parsing failed. Falling back to regex.")
            return self.parse_tutorial_steps()

        try:
            parsed_json = json.loads(response.content)
            steps = []
            for item in parsed_json:
                steps.append(TutorialStep(**item))
            self.parsed_steps = steps
            logger.info(f"Successfully parsed {len(steps)} steps with NLU.")
            return steps
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse NLU response: {e}")
            return self.parse_tutorial_steps()

    def parse_tutorial_steps(self) -> List[TutorialStep]:
        """Parse tutorial text into structured steps"""
        if not self.tutorial_text:
            self.extract_tutorial_text()

        steps = []
        step_number = 1
        current_section = "Introduction"

        lines = self.tutorial_text.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and dividers
            if not line or line.startswith("<<") or line.startswith("--"):
                i += 1
                continue

            # Detect section headers
            if self._is_section_header(line):
                current_section = line
                i += 1
                continue

            # Look for instruction patterns
            if line.startswith(">>"):
                step = self._parse_instruction_step(
                    lines, i, step_number, current_section
                )
                if step:
                    steps.append(step)
                    step_number += 1
                i += 1
                continue

            # Look for command explanations
            if self._contains_command_pattern(line):
                step = self._parse_command_explanation(
                    lines, i, step_number, current_section
                )
                if step:
                    steps.append(step)
                    step_number += 1
                i += 1
                continue

            i += 1

        self.parsed_steps = steps
        logger.info(f"Parsed {len(steps)} tutorial steps")
        return steps

    def _is_section_header(self, line: str) -> bool:
        """Check if line is a section header"""
        # Simple heuristics for section headers
        if line.isupper() and len(line) > 5:
            return True
        if line.startswith("*") and line.endswith("*"):
            return True
        return False

    def _parse_instruction_step(
        self, lines: List[str], index: int, step_num: int, section: str
    ) -> Optional[TutorialStep]:
        """Parse a >> instruction step"""
        line = lines[index].strip()

        # Remove the >> prefix
        instruction = line[2:].strip()

        # Extract keystrokes from the instruction
        keystrokes = self._extract_keystrokes(instruction)

        # Get expected behavior from following lines
        expected_behavior = self._get_expected_behavior(lines, index + 1)

        return TutorialStep(
            step_number=step_num,
            instruction_text=instruction,
            keystrokes=keystrokes,
            expected_behavior=expected_behavior,
            section=section,
            is_exercise=True,
        )

    def _parse_command_explanation(
        self, lines: List[str], index: int, step_num: int, section: str
    ) -> Optional[TutorialStep]:
        """Parse command explanation lines like 'C-f  Move forward a character'"""
        line = lines[index].strip()

        # Look for pattern: C-x  Description
        match = re.match(r"^\s*([CM]-\S+)\s+(.+)$", line)
        if match:
            keystroke = match.group(1)
            description = match.group(2)

            return TutorialStep(
                step_number=step_num,
                instruction_text=f"Try {keystroke}: {description}",
                keystrokes=[keystroke],
                expected_behavior=description,
                section=section,
                is_exercise=False,
            )

        return None

    def _contains_command_pattern(self, line: str) -> bool:
        """Check if line contains a command pattern like C-f, M-x, etc."""
        return bool(re.search(r"[CM]-\S+", line))

    def _extract_keystrokes(self, instruction: str) -> List[str]:
        """Extract keystroke sequences from instruction text"""
        # More specific regex for keystrokes
        keystroke_pattern = r"[CM]-\S+"

        # Find all single keystrokes
        keystrokes = re.findall(keystroke_pattern, instruction)

        # Handle multi-key sequences like C-x C-c
        multi_key_patterns = re.findall(r"([CM]-\S+\s+[CM]-\S+)", instruction)
        for pattern in multi_key_patterns:
            keys = pattern.split()
            if keys[0] in keystrokes:
                keystrokes.remove(keys[0])
            if keys[1] in keystrokes:
                keystrokes.remove(keys[1])
            keystrokes.append(pattern)

        # Remove duplicates while preserving order
        seen = set()
        unique_keystrokes = []
        for k in keystrokes:
            if k not in seen:
                seen.add(k)
                unique_keystrokes.append(k)

        return unique_keystrokes

    def _get_expected_behavior(self, lines: List[str], start_index: int) -> str:
        """Get expected behavior from lines following an instruction"""
        behavior_lines = []

        # Look at next few lines for expected behavior description
        for i in range(start_index, min(start_index + 3, len(lines))):
            if i < len(lines):
                line = lines[i].strip()
                if line and not line.startswith(">>") and not line.startswith("<<"):
                    behavior_lines.append(line)
                else:
                    break

        return " ".join(behavior_lines) if behavior_lines else "Execute the command"

    async def get_executable_steps(self) -> List[TutorialStep]:
        """Get only the steps that can be executed (have keystrokes)"""
        if claude_integration.is_available():
            return await self.parse_tutorial_steps_with_nlu()
        else:
            logger.warning("Claude not available, falling back to regex parser.")
            if not self.parsed_steps:
                self.parse_tutorial_steps()
            return [step for step in self.parsed_steps if step.keystrokes]

    def print_parsed_steps(self):
        """Print parsed steps for debugging"""
        if not self.parsed_steps:
            self.parse_tutorial_steps()

        print("\n=== PARSED TUTORIAL STEPS ===")
        for step in self.parsed_steps[:10]:  # Show first 10
            print(f"\nStep {step.step_number}: {step.section}")
            print(f"Instruction: {step.instruction_text}")
            print(f"Keystrokes: {step.keystrokes}")
            print(f"Expected: {step.expected_behavior}")
            print(f"Exercise: {step.is_exercise}")


async def main():
    """Test the tutorial parser"""
    parser = TutorialParser()

    print("Extracting Emacs tutorial...")
    tutorial_text = parser.extract_tutorial_text()
    print(f"Tutorial length: {len(tutorial_text)} characters")

    print("\nParsing tutorial steps with NLU...")
    steps = await parser.get_executable_steps()
    print(f"Total steps: {len(steps)}")

    print("\nFirst few executable steps:")
    for step in steps[:5]:
        print(f"{step.step_number}. {step.instruction_text}")
        print(f"   Keys: {step.keystrokes}")
        print(f"   Expected: {step.expected_behavior}")
        print()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
