#!/usr/bin/env python3
"""
Test Competitive AI Performance - No timeouts allowed!
"""

import time
from intelligent_dev_assistant import IntelligentDevAssistant
import redis


def test_competitive_performance():
    """Test AI performance for competition readiness"""

    print("🏆 COMPETITIVE AI PERFORMANCE TEST")
    print("=" * 50)
    print("🎯 Goal: No timeouts, fast responses, high accuracy")
    print()

    assistant = IntelligentDevAssistant()
    assistant.update_context(
        working_directory="/Users/jonathanhill/src/redis-ai-challenge",
        current_file="intelligent_dev_assistant.py",
        cursor_line=150,
        project_language="python",
    )

    # Test cases that should be fast
    competitive_tests = [
        "magit status",
        "git status",
        "move cursor forward",
        "delete this line",
        "save file",
        "debug error",
        "go to function definition",
        "open new file",
        "commit changes",
        "show git diff",
    ]

    print("🚀 Testing competitive performance...")
    results = []

    for i, test_input in enumerate(competitive_tests, 1):
        print(f"\n{i}. Testing: '{test_input}'")

        start_time = time.time()
        analysis = assistant.process_user_intent(test_input)
        end_time = time.time()

        response_time = end_time - start_time

        result = {
            "input": test_input,
            "intent": analysis.get("intent"),
            "confidence": analysis.get("confidence"),
            "method": analysis.get("method"),
            "response_time": response_time,
        }
        results.append(result)

        # Performance scoring
        if response_time < 0.1:
            speed_score = "🚀 Lightning"
        elif response_time < 0.5:
            speed_score = "⚡ Fast"
        elif response_time < 2.0:
            speed_score = "✅ Good"
        else:
            speed_score = "❌ Too slow"

        print(
            f"   Result: {analysis['intent']} (confidence: {analysis['confidence']:.2f})"
        )
        print(f"   Method: {analysis['method']}")
        print(f"   Speed: {response_time:.3f}s - {speed_score}")

    # Summary statistics
    print("\n" + "=" * 50)
    print("📊 COMPETITIVE PERFORMANCE SUMMARY")
    print("=" * 50)

    total_tests = len(results)
    fast_responses = len([r for r in results if r["response_time"] < 0.5])
    high_confidence = len([r for r in results if r["confidence"] >= 0.8])
    ai_responses = len([r for r in results if r["method"] == "quick_ai"])
    local_responses = len(
        [
            r
            for r in results
            if r["method"] in ["smart_local", "pattern_match", "context_enhanced"]
        ]
    )

    avg_response_time = sum(r["response_time"] for r in results) / total_tests
    avg_confidence = sum(r["confidence"] for r in results) / total_tests

    print(f"🎯 Total tests: {total_tests}")
    print(
        f"⚡ Fast responses (<0.5s): {fast_responses}/{total_tests} ({fast_responses/total_tests*100:.1f}%)"
    )
    print(
        f"🎯 High confidence (≥0.8): {high_confidence}/{total_tests} ({high_confidence/total_tests*100:.1f}%)"
    )
    print(f"🤖 AI responses: {ai_responses}/{total_tests}")
    print(f"🧠 Local responses: {local_responses}/{total_tests}")
    print(f"⏱️  Average response time: {avg_response_time:.3f}s")
    print(f"📊 Average confidence: {avg_confidence:.2f}")

    # Competition readiness assessment
    print(f"\n🏆 COMPETITION READINESS:")
    if fast_responses >= total_tests * 0.9 and high_confidence >= total_tests * 0.8:
        print("✅ EXCELLENT - Ready to win competitions!")
        grade = "A+"
    elif fast_responses >= total_tests * 0.8 and high_confidence >= total_tests * 0.7:
        print("✅ GOOD - Competitive performance")
        grade = "A"
    elif fast_responses >= total_tests * 0.6:
        print("⚠️  ACCEPTABLE - Some improvements needed")
        grade = "B"
    else:
        print("❌ NEEDS WORK - Too many slow responses")
        grade = "C"

    print(f"🎯 Performance Grade: {grade}")

    # Redis data verification
    print(f"\n📊 Redis coordination working:")
    redis_client = redis.Redis(decode_responses=True)
    ai_suggestions = redis_client.xlen("dev_assistant:ai_suggestions")
    print(f"   AI suggestions stored: {ai_suggestions}")

    return results


if __name__ == "__main__":
    test_competitive_performance()
