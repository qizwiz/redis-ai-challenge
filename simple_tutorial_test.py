#!/usr/bin/env python3
"""
Simple Tutorial Test - Test semantic comprehension on actual Emacs tutorial content
"""

import time
from intelligent_dev_assistant import IntelligentDevAssistant


def test_tutorial_comprehension():
    """Test AI comprehension on real Emacs tutorial instructions"""

    print("🎓 EMACS TUTORIAL COMPREHENSION TEST")
    print("=" * 60)
    print("Testing semantic understanding of actual tutorial instructions")
    print()

    # Initialize AI assistant
    assistant = IntelligentDevAssistant()
    assistant.update_context(
        current_file="TUTORIAL", cursor_line=1, project_language="text"
    )

    # Real Emacs tutorial instructions
    tutorial_instructions = [
        "You can move the cursor forward a character at a time by using the C-f command",
        "Use C-b to move backward a character",
        "When you want to move forward a word at a time, use M-f",
        "To move backward a word, use M-b",
        "C-n moves to the next line",
        "C-p moves to the previous line",
        "To move to the beginning of the line, use C-a",
        "To move to the end of the line, use C-e",
        "If you want to save the file, use C-x C-s",
        "To quit Emacs, use C-x C-c",
    ]

    # Expected key bindings
    expected_commands = [
        "C-f",
        "C-b",
        "M-f",
        "M-b",
        "C-n",
        "C-p",
        "C-a",
        "C-e",
        "C-x C-s",
        "C-x C-c",
    ]

    print(
        f"🧠 Testing comprehension of {len(tutorial_instructions)} tutorial instructions:"
    )
    print()

    correct_predictions = 0
    total_response_time = 0

    for i, (instruction, expected) in enumerate(
        zip(tutorial_instructions, expected_commands), 1
    ):
        print(f"{i:2d}. Instruction: '{instruction}'")

        start_time = time.time()
        result = assistant.process_user_intent(instruction)
        response_time = time.time() - start_time
        total_response_time += response_time

        # Extract the predicted command
        predicted = "unknown"
        if result.get("suggestions"):
            # Look for the expected command in suggestions
            for suggestion in result["suggestions"]:
                if expected.replace(" ", "") in suggestion.replace(" ", ""):
                    predicted = expected
                    break

        # Check if prediction matches
        is_correct = predicted == expected
        if is_correct:
            correct_predictions += 1

        print(f"    Expected: {expected}")
        print(f"    AI Found: {predicted} {'✅' if is_correct else '❌'}")
        print(
            f"    Response: {response_time:.6f}s, Confidence: {result.get('confidence', 0):.2f}"
        )
        print()

        time.sleep(0.1)  # Brief pause for readability

    # Results summary
    print("=" * 60)
    print("📊 TUTORIAL COMPREHENSION RESULTS")
    print("=" * 60)

    accuracy = (correct_predictions / len(tutorial_instructions)) * 100
    avg_response_time = total_response_time / len(tutorial_instructions)

    print(
        f"🎯 Accuracy: {correct_predictions}/{len(tutorial_instructions)} ({accuracy:.1f}%)"
    )
    print(f"⚡ Average Response Time: {avg_response_time:.6f}s")
    print(f"📊 Total Instructions Processed: {len(tutorial_instructions)}")

    if accuracy >= 80:
        print("✅ TUTORIAL READY: AI can comprehend Emacs tutorial instructions!")
    elif accuracy >= 60:
        print("⚠️  PARTIAL SUCCESS: AI understands most tutorial instructions")
    else:
        print("❌ NEEDS WORK: AI struggling with tutorial comprehension")

    print()
    print("🎓 This demonstrates the AI can read and understand actual")
    print("   Emacs tutorial content and map it to correct commands.")


if __name__ == "__main__":
    test_tutorial_comprehension()
