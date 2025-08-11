#!/usr/bin/env python3
"""
Live Tutorial Demo - Watch the AI process real tutorial instructions in real-time
"""

import time
import sys
from intelligent_dev_assistant import IntelligentDevAssistant


def live_tutorial_demo():
    """Live demonstration of AI processing actual tutorial instructions"""

    print("🎬 LIVE TUTORIAL PROCESSING DEMO")
    print("=" * 70)
    print("Watch the AI process real Emacs tutorial instructions in real-time")
    print("Press Enter after each step to continue...")
    print()

    # Initialize AI
    assistant = IntelligentDevAssistant()
    assistant.update_context(
        current_file="TUTORIAL", cursor_line=1, project_language="text"
    )

    # Load actual tutorial content
    try:
        with open(
            "/opt/homebrew/Cellar/emacs-plus@31/31.0.50/share/emacs/31.0.50/etc/tutorials/TUTORIAL",
            "r",
        ) as f:
            tutorial_content = f.read()
    except:
        print("❌ Could not load tutorial file")
        return

    # Real tutorial instructions in order
    tutorial_sequence = [
        {
            "instruction": "Now type C-v (View next screen) to scroll down in the tutorial.",
            "context": "First instruction in the tutorial - learning to scroll",
            "line": 20,
        },
        {
            "instruction": "Try typing M-v and then C-v, a few times.",
            "context": "Learning to scroll up and down",
            "line": 38,
        },
        {
            "instruction": "Find the cursor, and note what text is near it. Then type C-l.",
            "context": "Learning to recenter the screen",
            "line": 54,
        },
        {
            "instruction": "Do a few C-n's to bring the cursor down to this line.",
            "context": "First lesson in basic cursor movement",
            "line": 91,
        },
        {
            "instruction": "Move into the line with C-f's and then up with C-p's.",
            "context": "Combining forward and up movement",
            "line": 93,
        },
        {
            "instruction": "Try to C-b at the beginning of a line.",
            "context": "Learning what happens at line boundaries",
            "line": 100,
        },
        {
            "instruction": "Type a few M-f's and M-b's.",
            "context": "Learning word-based movement",
            "line": 120,
        },
        {
            "instruction": "Try a couple of C-a's, and then a couple of C-e's.",
            "context": "Learning beginning and end of line movement",
            "line": 140,
        },
    ]

    print(f"📖 Loaded tutorial with {len(tutorial_sequence)} instructions to process")
    input("Press Enter to start the live demo...")
    print()

    successful_instructions = 0
    total_time = 0

    for i, step in enumerate(tutorial_sequence, 1):
        print(f"📍 TUTORIAL STEP {i}/{len(tutorial_sequence)}")
        print(f"📄 Line {step['line']}: {step['context']}")
        print(f"📝 Instruction: \"{step['instruction']}\"")
        print()

        # Update context to match tutorial position
        assistant.update_context(cursor_line=step["line"])

        print("🧠 AI Processing...")
        start_time = time.time()

        # Process the instruction
        try:
            intent_analysis = assistant.process_user_intent(step["instruction"])
            suggestions = assistant.generate_suggestions(intent_analysis)
            processing_time = time.time() - start_time
            total_time += processing_time

            # Show results
            print(f"⚡ Response Time: {processing_time:.6f}s")
            print(f"🎯 AI Intent: {intent_analysis.get('intent')}")
            print(f"📊 Confidence: {intent_analysis.get('confidence'):.2f}")
            print(f"🔧 Method: {intent_analysis.get('method')}")

            if suggestions and intent_analysis.get("confidence", 0) >= 0.8:
                print(f"✅ AI Understanding:")
                for j, suggestion in enumerate(suggestions[:3], 1):
                    print(f"   {j}. {suggestion}")
                successful_instructions += 1
                status = "SUCCESS"
            else:
                print(f"❌ AI struggled with this instruction")
                status = "FAILED"

        except Exception as e:
            print(f"💥 Error processing instruction: {e}")
            processing_time = 0
            status = "ERROR"

        print(f"📋 Status: {status}")
        print("-" * 70)

        if i < len(tutorial_sequence):
            input("Press Enter for next instruction...")
        print()

    # Final results
    print("🏆 LIVE DEMO COMPLETE")
    print("=" * 70)

    success_rate = (successful_instructions / len(tutorial_sequence)) * 100
    avg_time = total_time / len(tutorial_sequence) if tutorial_sequence else 0

    print(f"📊 Instructions Processed: {len(tutorial_sequence)}")
    print(f"✅ Successful: {successful_instructions}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    print(f"⚡ Average Processing Time: {avg_time:.6f}s")

    if success_rate >= 85 and avg_time < 0.01:
        print(f"\n🎯 VERDICT: Tutorial completion is READY!")
        print("   The AI can handle real tutorial instructions effectively")
    elif success_rate >= 70:
        print(f"\n⚠️  VERDICT: Tutorial completion is MOSTLY ready")
        print("   AI handles most instructions but may struggle with some")
    else:
        print(f"\n❌ VERDICT: Tutorial completion needs more work")
        print("   AI struggles with tutorial instruction format")

    print(f"\n🔍 What you saw:")
    print("• Real tutorial instructions processed in real-time")
    print("• Actual AI decision-making with confidence scores")
    print("• Live performance metrics for each instruction")
    print("• Genuine semantic understanding being applied")

    print(f"\n🎓 This demonstrates whether the AI can actually")
    print("   follow the Emacs tutorial step by step.")


def quick_preview():
    """Quick preview of a few instructions"""
    print("🎬 QUICK PREVIEW - Processing 3 tutorial instructions")
    print()

    assistant = IntelligentDevAssistant()
    assistant.update_context(current_file="TUTORIAL", cursor_line=20)

    preview_instructions = [
        "Now type C-v (View next screen) to scroll down in the tutorial",
        "Do a few C-n's to bring the cursor down to this line",
        "Try a couple of C-a's, and then a couple of C-e's",
    ]

    for i, instruction in enumerate(preview_instructions, 1):
        print(f'{i}. "{instruction}"')

        start = time.time()
        result = assistant.process_user_intent(instruction)
        suggestions = assistant.generate_suggestions(result)
        elapsed = time.time() - start

        if result.get("confidence", 0) >= 0.8 and suggestions:
            print(f"   ✅ {suggestions[0]} ({elapsed:.6f}s)")
        else:
            print(f"   ❌ Failed to understand ({elapsed:.6f}s)")
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        quick_preview()
    else:
        live_tutorial_demo()
