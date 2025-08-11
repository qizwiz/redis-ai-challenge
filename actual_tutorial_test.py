#!/usr/bin/env python3
"""
Actual Tutorial Test - Test AI on the real Emacs tutorial instructions
"""

import time
from intelligent_dev_assistant import IntelligentDevAssistant


def test_actual_tutorial():
    """Test AI comprehension on actual Emacs tutorial text"""

    print("📖 ACTUAL EMACS TUTORIAL TEST")
    print("=" * 70)
    print("Testing AI on real tutorial instructions from the actual file")
    print()

    # Initialize AI assistant
    assistant = IntelligentDevAssistant()
    assistant.update_context(
        current_file="TUTORIAL", cursor_line=20, project_language="text"
    )

    # Actual instructions from the real Emacs tutorial
    actual_tutorial_instructions = [
        # From line 20: First instruction
        ("Now type C-v (View next screen) to scroll down in the tutorial", "C-v"),
        # From line 35-36: Screen navigation
        ("To move backwards one screen, type M-v", "M-v"),
        # From line 54: Clear screen command
        ("Find the cursor, and note what text is near it. Then type C-l", "C-l"),
        # From lines 72-73: Basic cursor movement
        ("use the commands C-p, C-b, C-f, and C-n", "C-p"),
        # From line 91: Next line movement
        ("Do a few C-n's to bring the cursor down to this line", "C-n"),
        # From line 93: Forward and up movement
        ("Move into the line with C-f's and then up with C-p's", "C-f"),
        # From line 100: Backward at beginning
        ("Try to C-b at the beginning of a line", "C-b"),
    ]

    # Read more of the tutorial for additional instructions
    print("🔍 Loading more tutorial content...")
    try:
        with open(
            "/opt/homebrew/Cellar/emacs-plus@31/31.0.50/share/emacs/31.0.50/etc/tutorials/TUTORIAL",
            "r",
        ) as f:
            tutorial_lines = f.readlines()

        # Extract more actual instructions
        additional_instructions = []
        for i, line in enumerate(tutorial_lines[100:200], 101):  # Lines 101-200
            line = line.strip()
            if ">>" in line and ("C-" in line or "M-" in line):
                # Extract the command
                if "C-a" in line:
                    additional_instructions.append((line, "C-a"))
                elif "C-e" in line:
                    additional_instructions.append((line, "C-e"))
                elif "M-f" in line:
                    additional_instructions.append((line, "M-f"))
                elif "M-b" in line:
                    additional_instructions.append((line, "M-b"))
                elif "C-k" in line:
                    additional_instructions.append((line, "C-k"))
                elif "C-d" in line:
                    additional_instructions.append((line, "C-d"))
                elif "C-x C-s" in line:
                    additional_instructions.append((line, "C-x C-s"))

        actual_tutorial_instructions.extend(
            additional_instructions[:5]
        )  # Add up to 5 more

    except Exception as e:
        print(f"⚠️  Could not read full tutorial: {e}")

    print(
        f"🧠 Testing AI on {len(actual_tutorial_instructions)} ACTUAL tutorial instructions:"
    )
    print()

    intent_correct = 0
    command_found = 0
    total_response_time = 0
    results = []

    for i, (instruction, expected_command) in enumerate(
        actual_tutorial_instructions, 1
    ):
        print(f"{i:2d}. Tutorial says: '{instruction}'")

        # Process the actual tutorial instruction
        start_time = time.time()
        intent_analysis = assistant.process_user_intent(instruction)
        suggestions = assistant.generate_suggestions(intent_analysis)
        response_time = time.time() - start_time
        total_response_time += response_time

        # Check if AI understands the intent
        intent = intent_analysis.get("intent", "unknown")
        intent_understood = intent != "unknown"
        if intent_understood:
            intent_correct += 1

        # Check if expected command appears in suggestions
        command_match = False
        matching_suggestion = None
        for suggestion in suggestions:
            if expected_command in suggestion:
                command_match = True
                matching_suggestion = suggestion
                break

        if command_match:
            command_found += 1

        results.append(
            {
                "instruction": instruction,
                "expected": expected_command,
                "intent": intent,
                "command_found": command_match,
                "suggestion": matching_suggestion,
                "response_time": response_time,
                "confidence": intent_analysis.get("confidence", 0),
            }
        )

        print(f"    AI Intent: {intent} {'✅' if intent_understood else '❌'}")
        print(
            f"    Expected Command: {expected_command} {'✅' if command_match else '❌'}"
        )
        if matching_suggestion:
            print(f"    AI Suggestion: {matching_suggestion}")
        print(
            f"    Response: {response_time:.6f}s, Confidence: {intent_analysis.get('confidence', 0):.2f}"
        )
        print()

        time.sleep(0.1)

    # Results Analysis
    print("=" * 70)
    print("📊 ACTUAL TUTORIAL TEST RESULTS")
    print("=" * 70)

    intent_accuracy = (intent_correct / len(actual_tutorial_instructions)) * 100
    command_accuracy = (command_found / len(actual_tutorial_instructions)) * 100
    avg_response_time = total_response_time / len(actual_tutorial_instructions)

    print(
        f"🎯 Intent Understanding: {intent_correct}/{len(actual_tutorial_instructions)} ({intent_accuracy:.1f}%)"
    )
    print(
        f"⌨️  Command Recognition: {command_found}/{len(actual_tutorial_instructions)} ({command_accuracy:.1f}%)"
    )
    print(f"⚡ Average Response Time: {avg_response_time:.6f}s")

    # Detailed breakdown
    print(f"\n📋 DETAILED BREAKDOWN:")
    for i, result in enumerate(results, 1):
        status = "✅" if result["command_found"] else "❌"
        print(
            f"   {i:2d}. {result['expected']:8} {status} ({result['confidence']:.2f}) - {result['instruction'][:50]}..."
        )

    # Final assessment
    if intent_accuracy >= 80 and command_accuracy >= 60:
        print(f"\n✅ ACTUAL TUTORIAL READY!")
        print("   The AI can understand real Emacs tutorial instructions")
        print("   and provide the correct commands users need to execute.")
    elif intent_accuracy >= 60:
        print(f"\n⚠️  PARTIALLY TUTORIAL READY")
        print("   AI understands most instructions but needs better command mapping")
    else:
        print(f"\n❌ NOT TUTORIAL READY")
        print("   AI struggles with actual tutorial instruction format")

    print(f"\n🏆 ULTIMATE TEST: Can it complete the actual tutorial?")
    if command_accuracy >= 60 and avg_response_time < 0.01:
        print("   YES - Fast enough and accurate enough for real tutorial completion")
    else:
        print("   NEEDS IMPROVEMENT - Either too slow or not accurate enough")


if __name__ == "__main__":
    test_actual_tutorial()
