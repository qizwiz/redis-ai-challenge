#!/usr/bin/env python3
"""
Complete Tutorial Test - Full AI tutorial assistance capability
"""

import time
from intelligent_dev_assistant import IntelligentDevAssistant


def test_complete_tutorial_capability():
    """Test the complete AI tutorial assistance workflow"""

    print("🎓 COMPLETE TUTORIAL CAPABILITY TEST")
    print("=" * 70)
    print("Testing full AI-powered tutorial assistance workflow")
    print()

    # Initialize AI assistant
    assistant = IntelligentDevAssistant()
    assistant.update_context(
        current_file="TUTORIAL", cursor_line=1, project_language="text"
    )

    # Realistic tutorial interaction scenarios
    tutorial_scenarios = [
        {
            "user_input": "I want to move the cursor forward",
            "expected_intent": "navigation",
            "expected_command": "C-f",
        },
        {
            "user_input": "how do I go backward?",
            "expected_intent": "navigation",
            "expected_command": "C-b",
        },
        {
            "user_input": "move to the next line",
            "expected_intent": "navigation",
            "expected_command": "C-n",
        },
        {
            "user_input": "go to previous line",
            "expected_intent": "navigation",
            "expected_command": "C-p",
        },
        {
            "user_input": "beginning of line please",
            "expected_intent": "navigation",
            "expected_command": "C-a",
        },
        {
            "user_input": "jump to end of line",
            "expected_intent": "navigation",
            "expected_command": "C-e",
        },
        {
            "user_input": "I need to save this file",
            "expected_intent": "file_ops",
            "expected_command": "C-x C-s",
        },
        {
            "user_input": "how do I open another file?",
            "expected_intent": "file_ops",
            "expected_command": "C-x C-f",
        },
        {
            "user_input": "delete this word",
            "expected_intent": "editing",
            "expected_command": "M-d",
        },
        {
            "user_input": "help me debug this code",
            "expected_intent": "debugging",
            "expected_command": "M-x gdb",
        },
    ]

    print(f"🧠 Testing {len(tutorial_scenarios)} tutorial scenarios:")
    print()

    intent_correct = 0
    command_found = 0
    total_response_time = 0

    for i, scenario in enumerate(tutorial_scenarios, 1):
        user_input = scenario["user_input"]
        expected_intent = scenario["expected_intent"]
        expected_command = scenario["expected_command"]

        print(f"{i:2d}. User: '{user_input}'")

        # Step 1: Process user intent
        start_time = time.time()
        intent_analysis = assistant.process_user_intent(user_input)

        # Step 2: Generate suggestions
        suggestions = assistant.generate_suggestions(intent_analysis)
        response_time = time.time() - start_time
        total_response_time += response_time

        # Check intent accuracy
        actual_intent = intent_analysis.get("intent", "unknown")
        intent_match = actual_intent == expected_intent
        if intent_match:
            intent_correct += 1

        # Check if expected command is in suggestions
        command_match = False
        matching_suggestion = None
        for suggestion in suggestions:
            if expected_command in suggestion:
                command_match = True
                matching_suggestion = suggestion
                break

        if command_match:
            command_found += 1

        print(
            f"    Intent: {actual_intent} {'✅' if intent_match else '❌'} (expected: {expected_intent})"
        )
        print(f"    Command: {expected_command} {'✅' if command_match else '❌'}")
        if matching_suggestion:
            print(f"    AI Says: {matching_suggestion}")
        print(
            f"    Response: {response_time:.6f}s, Confidence: {intent_analysis.get('confidence', 0):.2f}"
        )
        print()

        # Brief pause for readability
        time.sleep(0.1)

    # Results Analysis
    print("=" * 70)
    print("📊 COMPLETE TUTORIAL CAPABILITY RESULTS")
    print("=" * 70)

    intent_accuracy = (intent_correct / len(tutorial_scenarios)) * 100
    command_accuracy = (command_found / len(tutorial_scenarios)) * 100
    avg_response_time = total_response_time / len(tutorial_scenarios)

    print(
        f"🎯 Intent Understanding: {intent_correct}/{len(tutorial_scenarios)} ({intent_accuracy:.1f}%)"
    )
    print(
        f"⌨️  Command Mapping: {command_found}/{len(tutorial_scenarios)} ({command_accuracy:.1f}%)"
    )
    print(f"⚡ Average Response Time: {avg_response_time:.6f}s")

    # Overall capability assessment
    if intent_accuracy >= 80 and command_accuracy >= 70:
        print("✅ TUTORIAL READY: AI can handle complete tutorial assistance!")
        print("   • Understands user intent correctly")
        print("   • Maps requests to specific Emacs commands")
        print("   • Provides actionable suggestions")
        print("   • Fast enough for real-time interaction")
    elif intent_accuracy >= 70:
        print(
            "⚠️  PARTIALLY READY: Good intent understanding, needs better command mapping"
        )
    else:
        print("❌ NOT READY: Fundamental issues with intent understanding")

    print()
    print("🔍 DETAILED WORKFLOW DEMONSTRATION:")
    print()

    # Demonstrate complete workflow with one example
    example_input = "I want to move to the beginning of the line"
    print(f"User Request: '{example_input}'")
    print()

    # Process intent
    intent_result = assistant.process_user_intent(example_input)
    print(f"1. Intent Analysis:")
    print(f"   • Intent: {intent_result.get('intent')}")
    print(f"   • Action: {intent_result.get('action')}")
    print(f"   • Confidence: {intent_result.get('confidence')}")
    print(f"   • Method: {intent_result.get('method')}")
    print()

    # Generate suggestions
    suggestions = assistant.generate_suggestions(intent_result)
    print(f"2. AI Suggestions:")
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f"   {i}. {suggestion}")
    print()

    # Simulate execution
    target_command = None
    for suggestion in suggestions:
        if "beginning" in example_input.lower() and "C-a" in suggestion:
            target_command = "C-a"
            break

    if target_command:
        print(f"3. Execute Command: {target_command}")
        print(f"   ✅ AI successfully mapped natural language to Emacs command!")
    else:
        print(f"3. Execute Command: Could not determine specific command")

    print()
    print("🎓 CONCLUSION: This demonstrates a complete AI tutorial assistant")
    print("   that can understand natural language and provide specific")
    print("   Emacs commands to accomplish user goals.")


if __name__ == "__main__":
    test_complete_tutorial_capability()
