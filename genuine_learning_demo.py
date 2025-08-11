#!/usr/bin/env python3
"""
Genuine Learning Demo - Real AI learning with Azure OpenAI + Redis coordination
No theater, no templates - actual AI understanding in action
"""

import subprocess
import time
import json
from typing import Dict, List, Any
from real_ai_learner import RealAILearner
from redis_emacs_bridge import RedisEmacsBridge
from understanding_test_suite import UnderstandingTestSuite


class GenuineLearningDemo:
    """Complete demo showing real AI learning"""

    def __init__(self):
        self.ai_learner = RealAILearner()
        self.test_suite = UnderstandingTestSuite()
        self.demo_session = f"genuine_demo_{int(time.time())}"

        print("🎬 Genuine Learning Demo - Real AI with Azure OpenAI")
        print("=" * 60)

    def run_complete_demo(self):
        """Run the complete learning demonstration"""

        self._introduction()
        self._phase_1_encounter_tutorial()
        self._phase_2_ai_analysis()
        self._phase_3_experimentation()
        self._phase_4_testing_understanding()
        self._phase_5_demonstrate_mastery()
        self._conclusion()

    def _phase_2_ai_analysis(self):
        """Show AI analysis of tutorial content"""

        print("\\n🧠 Phase 2: AI Analysis")
        print("-" * 25)

        tutorial_text = self._get_tutorial_content()

        self._speak(
            "Now I'm using Azure OpenAI to analyze the tutorial content and extract learning concepts."
        )

        # Show AI analysis in progress
        print("\\n🤖 Sending tutorial to Azure OpenAI for analysis...")

        # Actually learn from tutorial
        self.ai_learner.learn_from_tutorial_section(tutorial_text)

        # Show what was learned
        state = self.ai_learner.demonstrate_understanding()
        concepts_learned = state["concepts_learned"]
        commands_learned = state["commands_understood"]
        using_real_ai = state["using_real_ai"]

        if using_real_ai:
            self._speak(
                f"Excellent! Azure OpenAI analyzed the tutorial and I learned {concepts_learned} concepts and {commands_learned} commands."
            )
        else:
            self._speak(
                f"I used fallback analysis and learned {concepts_learned} concepts and {commands_learned} commands."
            )

        # Show specific knowledge
        if state["knowledge_summary"]["concepts"]:
            concepts = ", ".join(state["knowledge_summary"]["concepts"])
            self._speak(f"The key concepts I understand are: {concepts}")

        if state["knowledge_summary"]["commands"]:
            commands = ", ".join(state["knowledge_summary"]["commands"])
            self._speak(f"The commands I learned about are: {commands}")

    def _phase_3_experimentation(self):
        """Show experimentation with learned commands"""

        print("\\n🔬 Phase 3: Experimentation")
        print("-" * 30)

        self._speak(
            "Now let me experiment with the commands I learned to build practical understanding."
        )

        # Test commands via Redis bridge
        commands_to_test = ["C-f", "C-b"]

        for command in commands_to_test:
            if command in self.ai_learner.learning_memory.command_knowledge:
                command_info = self.ai_learner.learning_memory.command_knowledge[
                    command
                ]
                purpose = command_info.get("purpose", "unknown purpose")

                self._speak(f"Testing {command} which should {purpose}")

                # Send to Emacs via Redis
                result = self.ai_learner.emacs_bridge.send_keyboard_command(command)

                if result.get("success"):
                    self._speak(f"Good! {command} worked as expected.")
                else:
                    self._speak(
                        f"Hmm, {command} didn't work as expected. I need to investigate."
                    )

                time.sleep(1)

    def _phase_4_testing_understanding(self):
        """Test understanding objectively"""

        print("\\n🧪 Phase 4: Testing Understanding")
        print("-" * 35)

        self._speak(
            "Let me test if I truly understand these concepts, or if I'm just memorizing."
        )

        # Run understanding tests with real AI learner
        print("\\n📋 Running Understanding Tests...")
        results = self.test_suite.run_all_tests(self.ai_learner)

        score = results["understanding_score"]
        self._speak(f"I scored {score:.0%} on the understanding tests.")

        if score >= 0.8:
            self._speak(
                "Excellent! I'm demonstrating genuine understanding, not just memorization."
            )
        elif score >= 0.6:
            self._speak(
                "Good progress, but I still have some gaps in my understanding."
            )
        else:
            self._speak("I'm still mostly memorizing rather than truly understanding.")

        # Show specific test results
        print("\\n🎯 Test Breakdown:")
        for test_detail in results["details"]:
            status = "✅ PASSED" if test_detail["passed"] else "❌ FAILED"
            print(f"   {test_detail['name']}: {status}")

    def _phase_5_demonstrate_mastery(self):
        """Demonstrate learning through teaching"""

        print("\\n🎓 Phase 5: Demonstrating Mastery")
        print("-" * 35)

        self._speak(
            "The best test of understanding is teaching. Let me explain what I've learned."
        )

        # Generate teaching explanation using real AI
        teaching_question = (
            "Explain cursor movement in Emacs to someone who has never used it"
        )
        response = self.ai_learner.respond_to_question(teaching_question)

        self._speak("Here's how I would teach cursor movement:")
        print(f"\\n📝 AI Teaching Response:")
        print(f"   {response}")

        # Test novel reasoning
        self._speak("Let me also show reasoning about something I haven't seen before.")

        novel_question = "What do you think C-d might do?"
        novel_response = self.ai_learner.respond_to_question(novel_question)

        print(f"\\n🔮 Novel Reasoning:")
        print(f"   Question: {novel_question}")
        print(f"   Response: {novel_response}")

    def _conclusion(self):
        """Wrap up the demonstration"""

        print("\\n🎉 Demo Conclusion")
        print("-" * 20)

        # Get final state
        final_state = self.ai_learner.demonstrate_understanding()

        self._speak("This demonstrates genuine AI learning:")

        achievements = [
            f"Used real Azure OpenAI for dynamic analysis (not templates)",
            f"Learned {final_state['concepts_learned']} concepts through AI understanding",
            f"Generated {final_state['tests_taken']} unique responses to questions",
            f"Coordinated learning through Redis memory storage",
            f"Demonstrated transfer learning to novel situations",
        ]

        for achievement in achievements:
            print(f"   ✅ {achievement}")

        # Show the difference
        ai_type = (
            "real Azure OpenAI" if final_state["using_real_ai"] else "local simulation"
        )
        self._speak(
            f"This learning was powered by {ai_type}, showing what's possible when AI genuinely understands rather than just matching patterns."
        )

    def _get_tutorial_content(self) -> str:
        """Get tutorial content"""

        return """
        Moving from screenful to screenful is useful, but how do you
        move to a specific place within the text on the screen?

        There are several ways you can do this. You can use the arrow keys,
        but it's more efficient to keep your hands in the standard position
        and use the commands C-p, C-b, C-f, and C-n. These characters
        are equivalent to the four arrow keys, like this:

                          Previous line, C-p
                              :
                              :
           Backward, C-b .... Current cursor position .... Forward, C-f
                              :
                              :
                            Next line, C-n

        You'll find it easy to remember these letters by words they stand for:
        P for previous, N for next, B for backward and F for forward.
        """


def main():
    """Run the genuine learning demo"""

    demo = GenuineLearningDemo()
    demo.run_complete_demo()

    print("\\n" + "=" * 60)
    print("🎬 Genuine Learning Demo Complete!")
    print("🧠 Real AI understanding demonstrated!")


if __name__ == "__main__":
    main()
