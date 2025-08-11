#!/usr/bin/env python3
"""
Use the Real Learning System - Interactive AI that learns from your commands
"""

import subprocess
from genuine_ai_learning import RealLearner


def check_emacs_ready():
    """Check if Emacs is ready for real integration"""
    try:
        result = subprocess.run(
            ["emacsclient", "--eval", '(message "Learning system ready")'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except:
        return False


def interactive_learning_session():
    """Interactive session where you teach the AI"""

    print("🧠 INTERACTIVE AI LEARNING SESSION")
    print("=" * 50)

    if check_emacs_ready():
        print("✅ Emacs is ready - AI will learn from real execution")
        real_emacs = True
    else:
        print("⚠️  Emacs not ready - AI will learn from simulated execution")
        print("💡 To use real Emacs: start emacs, then M-x server-start")
        real_emacs = False

    learner = RealLearner()

    print("\n🎓 Teach the AI by giving it commands!")
    print("Examples: 'move cursor forward', 'save file', 'show git status'")
    print("Type 'quit' to exit, 'knowledge' to see what it learned")
    print()

    session_count = 0

    while True:
        try:
            user_input = input("🗣️  You: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                break
            elif user_input.lower() in ["knowledge", "k"]:
                show_knowledge(learner)
                continue
            elif user_input.lower() in ["stats", "s"]:
                show_stats(learner)
                continue
            elif not user_input:
                continue

            session_count += 1
            print(f"\n📖 Learning Session {session_count}")
            print("-" * 30)

            # Let the AI attempt the command and learn
            result = learner.attempt_command(user_input)

            # Show what happened
            outcome = result["execution"]["outcome"]
            if outcome == "success":
                print(f"✅ Success! AI learned something new")
            else:
                print(f"❌ Failed - but AI learned from the failure")

            if result["learning"]["learned"]:
                print(f"🎓 {result['learning']['insight']}")

            print(f"🧠 AI now knows {len(learner.knowledge)} patterns")

        except KeyboardInterrupt:
            print("\n\n👋 Learning session ended")
            break

    # Final summary
    print(f"\n" + "=" * 50)
    print("🎓 LEARNING SESSION COMPLETE")
    print(f"📊 Commands taught: {session_count}")
    print(f"📚 Patterns learned: {len(learner.knowledge)}")
    print(
        f"💾 Experiences in Redis: {learner.memory.redis_client.xlen('ai_experiences')}"
    )

    return learner


def show_knowledge(learner):
    """Show what the AI has learned"""
    print("\n📚 AI KNOWLEDGE BASE:")
    if not learner.knowledge:
        print("   (No patterns learned yet)")
    else:
        for pattern, info in learner.knowledge.items():
            key_binding = info.get("key_binding", info.get("action", "unknown"))
            success_count = info.get("times_successful", 0)
            print(f"   • {pattern} → {key_binding} ({success_count}x successful)")


def show_stats(learner):
    """Show learning statistics"""
    print("\n📊 LEARNING STATISTICS:")
    if not learner.confidence_adjustments:
        print("   (No attempts yet)")
    else:
        for intent, stats in learner.confidence_adjustments.items():
            rate = stats["successes"] / stats["attempts"]
            print(
                f"   • {intent}: {rate:.1%} success ({stats['successes']}/{stats['attempts']})"
            )


def quick_demo():
    """Quick demonstration of the learning system"""
    print("🚀 QUICK LEARNING DEMO")
    print("=" * 30)

    learner = RealLearner()

    demo_commands = ["move forward", "go backward", "save the file"]

    for cmd in demo_commands:
        print(f"\n🎯 Teaching: '{cmd}'")
        result = learner.attempt_command(cmd)
        if result["learning"]["learned"]:
            print(f"✅ Learned: {result['learning']['insight']}")

    show_knowledge(learner)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        quick_demo()
    else:
        interactive_learning_session()
