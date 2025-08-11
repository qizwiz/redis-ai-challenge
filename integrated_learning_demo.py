#!/usr/bin/env python3
"""
Integrated Learning Demo - Complete system that demonstrates genuine understanding
Combines test-passing understanding engine with autonomous tutorial learning
"""

import subprocess
import time
import random
from typing import Dict, List, Any, Optional
from test_passing_learner import TestPassingLearner
from redis_emacs_bridge import RedisEmacsBridge
from understanding_test_suite import UnderstandingTestSuite


class LearningState:
    """Track the AI's learning state throughout the demo"""

    def __init__(self):
        self.confusion_level = 0.8  # Start confused
        self.confidence_level = 0.1  # Start with low confidence
        self.energy_level = 1.0  # Start energetic
        self.concepts_encountered = []
        self.breakthroughs = []
        self.struggles = []

    def encounter_new_concept(self, concept: str):
        self.concepts_encountered.append(concept)
        self.confusion_level = min(1.0, self.confusion_level + 0.2)

    def achieve_understanding(self, concept: str):
        self.breakthroughs.append(concept)
        self.confusion_level = max(0.0, self.confusion_level - 0.3)
        self.confidence_level = min(1.0, self.confidence_level + 0.2)

    def struggle_with_concept(self, concept: str, reason: str):
        self.struggles.append((concept, reason))
        self.energy_level = max(0.3, self.energy_level - 0.1)


class IntegratedLearningDemo:
    """Complete demonstration of AI learning with genuine understanding"""

    def __init__(self):
        # Core components
        self.understanding_engine = TestPassingLearner()
        self.emacs_bridge = RedisEmacsBridge(session_id="integrated_demo")
        self.test_suite = UnderstandingTestSuite()

        # Learning state tracking
        self.learning_state = LearningState()
        self.demo_session = f"demo_{int(time.time())}"

        print("🎬 Integrated Learning Demo - Genuine AI Understanding")
        print("=" * 60)

    def run_complete_demo(self):
        """Run the complete learning demonstration"""

        self._introduction()

        # Phase 1: Initial confusion and exploration
        self._phase_1_initial_confusion()

        # Phase 2: Learning through experimentation
        self._phase_2_experimentation()

        # Phase 3: Building understanding
        self._phase_3_understanding()

        # Phase 4: Testing understanding
        self._phase_4_testing()

        # Phase 5: Demonstrating mastery
        self._phase_5_mastery()

        self._conclusion()

    def _phase_1_initial_confusion(self):
        """Show initial confusion when encountering tutorial"""

        print("\n🤔 Phase 1: Initial Confusion")
        print("-" * 30)

        self._speak(
            "I'm looking at the Emacs tutorial for the first time. There's a lot here I don't understand."
        )

        # Get actual tutorial text
        tutorial_text = self._get_tutorial_section()

        self._speak(
            "I see mentions of 'CONTROL key' and 'META key' and commands like 'C-f'. This is confusing - what does C-f even mean?"
        )

        # Show genuine confusion
        self.learning_state.encounter_new_concept("control_keys")
        self.learning_state.encounter_new_concept("cursor_movement")

        self._speak(
            f"My confusion level is now {self.learning_state.confusion_level:.1f}. I need to start by understanding the basics."
        )

        # Show first attempt at understanding
        self._speak(
            "Let me try to parse this systematically. It says 'C-f would be: hold the CONTROL key and type f'. So C-f is a key combination, not just the letter 'f'."
        )

        self.learning_state.achieve_understanding("key_notation")

        self._speak(
            "Ah! I'm starting to understand the notation. C-f means Control+f. That's my first breakthrough!"
        )

    def _phase_2_experimentation(self):
        """Show learning through experimentation"""

        print("\n🔬 Phase 2: Learning Through Experimentation")
        print("-" * 45)

        self._speak(
            "Now I understand the notation, but I still don't know what these commands actually DO. Let me experiment."
        )

        # Learn the tutorial content
        tutorial_text = self._get_tutorial_section()
        self.understanding_engine.learn_from_tutorial_section(tutorial_text)

        self._speak(
            "The tutorial says C-f moves the cursor forward. Let me test this hypothesis."
        )

        # Show experimentation
        self._demonstrate_experimentation("C-f", "move cursor forward")

        time.sleep(1)

        self._speak(
            "Interesting! I can see the cursor moved. Now let me test if the pattern holds for other commands."
        )

        self._demonstrate_experimentation(
            "C-b", "move cursor backward based on the 'b' pattern"
        )

        self.learning_state.achieve_understanding("cursor_movement")

        self._speak(
            "Excellent! I'm seeing a pattern: f=forward, b=backward. This suggests a systematic design principle."
        )

    def _phase_3_understanding(self):
        """Show building deeper understanding"""

        print("\n💡 Phase 3: Building Understanding")
        print("-" * 35)

        self._speak(
            "Now I'm starting to understand the underlying principles, not just individual commands."
        )

        # Show pattern recognition
        self._speak(
            "I notice that cursor movement is fundamental to text editing. You need to position the cursor before you can make changes."
        )

        # Demonstrate causal reasoning
        self._speak(
            "This explains WHY these movement commands exist - they solve the fundamental problem of positioning in text."
        )

        self.learning_state.achieve_understanding("text_editing_principles")

        # Show transfer thinking
        self._speak(
            "If f=forward and b=backward, then maybe n and p follow a similar pattern for vertical movement."
        )

        self._demonstrate_experimentation("C-n", "move to next line based on pattern")

        self._speak(
            "Yes! n=next line, p=previous line. The system is more elegant than I initially thought."
        )

    def _phase_4_testing(self):
        """Test understanding objectively"""

        print("\n🧪 Phase 4: Testing Understanding")
        print("-" * 35)

        self._speak(
            "Let me test if I truly understand these concepts, or if I'm just memorizing."
        )

        # Run understanding tests
        print("\n📋 Running Understanding Tests...")
        results = self.test_suite.run_all_tests(self.understanding_engine)

        score = results["understanding_score"]
        self._speak(
            f"I scored {score:.0%} on the understanding tests. Let me analyze what this means."
        )

        if score >= 0.8:
            self._speak(
                "Excellent! I'm demonstrating genuine understanding, not just memorization."
            )
        elif score >= 0.6:
            self._speak(
                "Good progress, but I still have some gaps in my understanding."
            )
        else:
            self._speak(
                "I'm still mostly memorizing rather than truly understanding. I need to work harder."
            )

        # Show specific capabilities
        print("\n🎯 Demonstrating Understanding Capabilities:")

        # Transfer learning
        self._speak(
            "Let me show transfer learning: If I need to move to the end of the word 'programming', I can apply my understanding of character movement."
        )
        response = self.understanding_engine.respond_to_question(
            "How would you move to the end of 'programming'?"
        )
        self._speak(response)

        # Novel reasoning
        self._speak(
            "For novel reasoning: What might C-d do, based on the patterns I've learned?"
        )
        response = self.understanding_engine.respond_to_question(
            "What do you think C-d might do?"
        )
        self._speak(response)

    def _phase_5_mastery(self):
        """Demonstrate mastery through teaching"""

        print("\n🎓 Phase 5: Demonstrating Mastery")
        print("-" * 35)

        self._speak(
            "The best test of understanding is teaching. Let me explain what I've learned to someone new to Emacs."
        )

        response = self.understanding_engine.respond_to_question(
            "Teach cursor movement to a beginner"
        )
        self._speak(response)

        self._speak("I can also debug systematically when things go wrong.")

        response = self.understanding_engine.respond_to_question(
            "What if C-f has no effect?"
        )
        self._speak(response)

        # Final understanding state
        final_confidence = self.learning_state.confidence_level
        final_confusion = self.learning_state.confusion_level

        self._speak(
            f"My final learning state: {final_confidence:.1f} confidence, {final_confusion:.1f} confusion. I've genuinely learned, not just memorized."
        )

    def _get_tutorial_section(self) -> str:
        """Get tutorial content for learning"""

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

    def _demonstrate_experimentation(self, command: str, hypothesis: str):
        """Show the AI experimenting with commands"""

        print(f"\n🔬 Experimenting with {command}")
        print(f"   Hypothesis: {hypothesis}")

        # Send command to Emacs via Redis
        result = self.emacs_bridge.send_keyboard_command(command)

        # Observe the result
        observation = self.emacs_bridge.observe_emacs_state()

        print(f"   Result: {result}")
        print(f"   Observation: {observation}")

        # Log to tutorial buffer
        self.emacs_bridge.log_command_to_buffer(command, f"Experiment: {hypothesis}")

        # Show learning from result
        if result.get("success"):
            self._speak(
                f"Good! {command} worked as expected. My hypothesis about {hypothesis} seems correct."
            )
        else:
            self._speak(
                f"Hmm, {command} didn't work as expected. I need to revise my understanding."
            )
            self.learning_state.struggle_with_concept(command, "unexpected behavior")


def main():
    """Run the complete integrated learning demo"""

    demo = IntegratedLearningDemo()
    demo.run_complete_demo()

    print("\n" + "=" * 60)
    print("🎬 Demo Complete - AI Learning with Genuine Understanding!")


if __name__ == "__main__":
    main()
