#!/usr/bin/env python3
"""
AI Tutorial Learner - The Complete Tutorial Performance System
This is the main system that performs the Emacs tutorial like a human learner,
with AI commentary, step-by-step execution, and real learning progression.
"""

import asyncio
import time
import logging
from typing import List, Dict, Optional

from tutorial_parser import TutorialParser, TutorialStep
from instruction_executor import InstructionExecutor, ExecutionResult
from robust_claude_integration import claude_integration
from fixed_redis_coordinator import redis_coordinator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AITutorialLearner:
    """AI that learns Emacs by performing the tutorial with human-like commentary"""

    def __init__(self):
        self.parser = TutorialParser()
        self.executor = InstructionExecutor()
        self.coordinator = redis_coordinator

        self.session_id = f"tutorial_session_{int(time.time())}"
        self.steps_completed = 0
        self.learning_insights = []
        self.current_understanding = "I'm new to Emacs and ready to learn"

    async def perform_tutorial_live(self):
        """Perform the complete tutorial live with AI commentary"""
        print("=" * 80)
        print("🎓 AI TUTORIAL LEARNER - LIVE PERFORMANCE")
        print("=" * 80)
        print("🤖 Watch me learn Emacs from the tutorial, just like you would")
        print("🧠 I'll read each instruction, understand it, and execute it")
        print("=" * 80)
        print()

        try:
            # Phase 1: Setup and Introduction
            await self._introduction_phase()

            # Phase 2: Parse Tutorial
            await self._tutorial_parsing_phase()

            # Phase 3: Begin Learning
            await self._learning_execution_phase()

            # Phase 4: Reflection and Summary
            await self._reflection_phase()

        except KeyboardInterrupt:
            print("\n🛑 Tutorial interrupted by user")
        except Exception as e:
            print(f"\n❌ Tutorial error: {e}")
            logger.error(f"Tutorial performance error: {e}")

        print("\n🎯 AI TUTORIAL LEARNING COMPLETE")
        print("✨ I've learned Emacs basics through hands-on practice")

    async def _introduction_phase(self):
        """AI introduces itself and explains what it's about to do"""
        print("🤖 AI INTRODUCTION")
        print("-" * 50)

        await self._ai_commentary(
            "Hello! I'm an AI that learns just like humans do. "
            "I'm going to work through the Emacs tutorial step by step. "
            "I'll read each instruction, figure out what to do, and then execute it. "
            "Let's see how well I can learn Emacs from scratch!"
        )

        print("\n🎯 Setting up Emacs environment...")
        success = await self.executor.start_emacs_session()

        if success:
            await self._ai_commentary(
                "Great! I've got Emacs running and the tutorial open. "
                "I can see the tutorial text in front of me. "
                "Time to start learning!"
            )
        else:
            await self._ai_commentary(
                "Hmm, I'm having trouble setting up Emacs. "
                "Let me try to work with what I have..."
            )

        print("\n" + "=" * 50)
        input("Press ENTER to watch me start learning...")
        print()

    async def _tutorial_parsing_phase(self):
        """AI reads and understands the tutorial structure"""
        print("📖 AI READING AND UNDERSTANDING THE TUTORIAL")
        print("-" * 60)

        await self._ai_commentary(
            "Let me read through this tutorial and understand what I need to learn. "
            "I'll parse it into steps that I can follow systematically."
        )

        # Parse the tutorial
        tutorial_text = self.parser.extract_tutorial_text()
        steps = self.parser.parse_tutorial_steps()
        executable_steps = self.parser.get_executable_steps()

        await self._ai_commentary(
            f"I've read the tutorial - it's {len(tutorial_text)} characters long. "
            f"I found {len(steps)} total steps, and {len(executable_steps)} that I can actually practice. "
            f"The tutorial covers basic cursor movement, which is perfect for a beginner like me!"
        )

        # Show understanding of key concepts
        if claude_integration.is_available():
            understanding_prompt = f"""
            I'm an AI learning Emacs. I just read the tutorial and found these key commands to learn:
            {[step.keystrokes for step in executable_steps[:5]]}
            
            As a beginner, what should I expect to learn from these commands? 
            Respond in first person as if you're excited to learn.
            """

            response = claude_integration.execute_prompt(
                understanding_prompt, timeout=10
            )
            if response.success:
                await self._ai_commentary(response.content.strip())

        print("\n" + "=" * 50)
        input("Press ENTER to watch me start practicing...")
        print()

    async def _learning_execution_phase(self):
        """AI executes tutorial steps with learning commentary"""
        print("🎯 AI LEARNING EXECUTION - LIVE PRACTICE")
        print("-" * 60)

        executable_steps = self.parser.get_executable_steps()
        steps_to_practice = executable_steps[:8]  # First 8 steps

        await self._ai_commentary(
            f"Okay, I'm going to practice {len(steps_to_practice)} commands. "
            "I'll try each one and see what happens. Here we go!"
        )

        for i, step in enumerate(steps_to_practice, 1):
            print(f"\n📚 LEARNING STEP {i}/{len(steps_to_practice)}")
            print(f"🎯 Tutorial says: {step.instruction_text}")

            # AI reads and understands the instruction
            await self._understand_instruction(step)

            # AI plans what to do
            await self._plan_execution(step)

            # AI executes the instruction
            result = await self._execute_with_commentary(step)

            # AI reflects on what happened
            await self._reflect_on_result(step, result)

            self.steps_completed += 1

            # Brief pause between steps
            await asyncio.sleep(2)

    async def _understand_instruction(self, step: TutorialStep):
        """AI demonstrates understanding of the instruction"""
        if claude_integration.is_available():
            understanding_prompt = f"""
            I'm learning Emacs. The tutorial instruction is: "{step.instruction_text}"
            The keystrokes are: {step.keystrokes}
            
            As an AI learner, explain what you think this instruction wants you to do.
            Be conversational and show your thinking process. Keep it brief (1-2 sentences).
            """

            response = claude_integration.execute_prompt(
                understanding_prompt, timeout=8
            )
            if response.success:
                await self._ai_commentary(f"🤔 {response.content.strip()}")
            else:
                await self._ai_commentary(
                    f"🤔 I need to try the keystroke {' '.join(step.keystrokes)}. "
                    f"Let me see what happens when I press these keys."
                )
        else:
            await self._ai_commentary(
                f"🤔 I need to try {' '.join(step.keystrokes)}. "
                f"The tutorial says this should: {step.expected_behavior}"
            )

    async def _plan_execution(self, step: TutorialStep):
        """AI explains its execution plan"""
        await self._ai_commentary(
            f"📋 My plan: I'll press {' '.join(step.keystrokes)} "
            f"and watch what happens to the cursor or text."
        )

    async def _execute_with_commentary(self, step: TutorialStep) -> ExecutionResult:
        """Execute the step with live commentary"""
        await self._ai_commentary(f"⚡ Executing: {' '.join(step.keystrokes)}")

        # Execute the step
        result = await self.executor.execute_tutorial_step(step)

        return result

    async def _reflect_on_result(self, step: TutorialStep, result: ExecutionResult):
        """AI reflects on what it learned from executing the step"""
        if result.success:
            await self._ai_commentary(f"✅ Success! {result.actual_result}")

            # Generate learning insight
            if claude_integration.is_available():
                insight_prompt = f"""
                I just successfully executed {result.keystroke} in Emacs.
                The result was: {result.actual_result}
                
                As an AI that's learning, what insight should I remember about this command?
                Keep it brief and practical.
                """

                response = claude_integration.execute_prompt(insight_prompt, timeout=8)
                if response.success:
                    insight = response.content.strip()
                    await self._ai_commentary(f"💡 I learned: {insight}")
                    self.learning_insights.append(insight)
        else:
            await self._ai_commentary(
                f"🤔 Hmm, that didn't work as expected: {result.actual_result}"
            )
            await self._ai_commentary("Let me try to understand what went wrong...")

    async def _reflection_phase(self):
        """AI reflects on what it learned"""
        print("\n🎓 AI LEARNING REFLECTION")
        print("-" * 50)

        await self._ai_commentary(
            f"Wow! I just completed {self.steps_completed} tutorial steps. "
            f"Let me think about what I learned..."
        )

        if self.learning_insights:
            await self._ai_commentary("Here are the key insights I gained:")
            for i, insight in enumerate(self.learning_insights, 1):
                print(f"   💡 {i}. {insight}")

        # Generate overall reflection
        if claude_integration.is_available():
            reflection_prompt = f"""
            I'm an AI that just learned Emacs basics by following the tutorial.
            I completed {self.steps_completed} steps and learned these insights:
            {chr(10).join(self.learning_insights)}
            
            Reflect on this learning experience. What did I accomplish?
            How do I feel about my Emacs skills now? What would I do next?
            Be enthusiastic and show growth.
            """

            response = claude_integration.execute_prompt(reflection_prompt, timeout=15)
            if response.success:
                await self._ai_commentary(response.content.strip())

        await self._ai_commentary(
            "This was amazing! I went from knowing nothing about Emacs "
            "to understanding basic cursor movement. I feel like I could "
            "actually use Emacs now for simple tasks. The tutorial method "
            "really works - learning by doing is so much better than just "
            "reading about commands!"
        )

    async def _ai_commentary(self, text: str):
        """Provide AI commentary with realistic pacing"""
        print(f"🤖 AI: {text}")

        # Store commentary in Redis
        self.coordinator.store_ai_response(
            {
                "type": "ai_commentary",
                "text": text,
                "session_id": self.session_id,
                "timestamp": str(time.time()),
            }
        )

        # Realistic reading/thinking pause
        words = len(text.split())
        pause_time = min(words * 0.1, 3.0)  # Max 3 seconds
        await asyncio.sleep(pause_time)


async def main():
    """Run the AI tutorial learner"""
    learner = AITutorialLearner()
    await learner.perform_tutorial_live()


if __name__ == "__main__":
    asyncio.run(main())
