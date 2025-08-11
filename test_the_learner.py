#!/usr/bin/env python3
"""
Test the TestPassingLearner against the understanding test suite
"""

from test_passing_learner import TestPassingLearner
from understanding_test_suite import UnderstandingTestSuite


def main():
    """Test our learner against understanding benchmarks"""

    print("🧪 Testing Test-Passing Learner Against Understanding Suite")
    print("=" * 60)

    # Create and train the learner
    learner = TestPassingLearner()

    # Learn from tutorial content
    tutorial_text = """
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

    print("📚 Training learner on tutorial content...")
    learner.learn_from_tutorial_section(tutorial_text)

    # Run the understanding test suite
    test_suite = UnderstandingTestSuite()
    results = test_suite.run_all_tests(learner)

    print(f"\n🎯 FINAL RESULT:")
    if results["understanding_score"] >= 0.8:
        print(f"   ✅ GENUINE UNDERSTANDING: {results['understanding_score']:.1%}")
        print(f"   🎉 The learner demonstrates authentic comprehension!")
    elif results["understanding_score"] >= 0.6:
        print(f"   🤔 PARTIAL UNDERSTANDING: {results['understanding_score']:.1%}")
        print(f"   📈 Progress made, but more depth needed")
    else:
        print(f"   🎭 THEATER DETECTED: {results['understanding_score']:.1%}")
        print(f"   🔄 Still simulating rather than understanding")

    return results


if __name__ == "__main__":
    main()
