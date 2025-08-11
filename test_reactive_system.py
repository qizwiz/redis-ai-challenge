#!/usr/bin/env python3
"""
Test the Reactive AI System Components
"""

import asyncio
import time
import sys
from pathlib import Path


def test_claude_integration():
    """Test Claude Code integration"""
    print("🧪 Testing Claude Code Integration...")

    try:
        from robust_claude_integration import claude_integration, get_claude_status

        status = get_claude_status()
        print(f"   Status: {status['status']}")
        print(f"   Available: {status['available']}")
        print(f"   Path: {status['claude_path']}")

        if status["available"]:
            print("   Testing prompt execution...")
            response = claude_integration.execute_prompt(
                "Say hello briefly", timeout=10
            )
            print(f"   Response: {response.success}")
            if response.success:
                print(f"   Content: {response.content[:100]}...")
            else:
                print(f"   Error: {response.error_message}")

        return status["available"]

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_reactive_facade():
    """Test the reactive facade"""
    print("\n🧪 Testing Reactive Facade...")

    try:
        from reactive_facade import reactive_facade, IntentType

        async def test_facade():
            print("   Starting reactive loop...")

            # Start the loop in background
            loop_task = asyncio.create_task(reactive_facade.start_reactive_loop())
            await asyncio.sleep(0.5)  # Give it time to start

            # Capture test intent
            print("   Capturing test intent...")
            intent_id = reactive_facade.capture_intent(
                IntentType.QUERY,
                "How do I implement error handling?",
                {"file": "test.py", "line": 42},
                "test",
            )
            print(f"   Intent ID: {intent_id}")

            # Let it process
            await asyncio.sleep(2)

            # Stop
            print("   Stopping reactive facade...")
            reactive_facade.stop()
            await loop_task

            return True

        return asyncio.run(test_facade())

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_composable_modes():
    """Test composable modes"""
    print("\n🧪 Testing Composable Modes...")

    try:
        modes_file = Path(__file__).parent / "composable_modes.el"
        if modes_file.exists():
            print(f"   ✅ Found: {modes_file}")
            print(f"   Size: {modes_file.stat().st_size} bytes")

            # Check for key components
            content = modes_file.read_text()
            if "define-redis-ai-mode" in content:
                print("   ✅ Mode definition framework found")
            if "redis-ai-natural-command" in content:
                print("   ✅ Natural command interface found")
            if "redis-ai-capture-keystroke" in content:
                print("   ✅ Keystroke capture found")

            return True
        else:
            print("   ❌ composable_modes.el not found")
            return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    print("🚀 Testing Revolutionary Reactive AI System")
    print("=" * 60)

    results = {
        "claude": test_claude_integration(),
        "facade": test_reactive_facade(),
        "modes": test_composable_modes(),
    }

    print("\n📊 Test Results:")
    print("=" * 30)
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {component.title()}: {status}")

    all_passed = all(results.values())
    print(
        f"\n🎯 Overall: {'✅ ALL SYSTEMS GO' if all_passed else '⚠️ SOME ISSUES FOUND'}"
    )

    if all_passed:
        print("\n🚀 Ready to launch production system!")
        print("   Run: python production_reactive_server.py")
        print("   Or:  python start_reactive_system.py")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
