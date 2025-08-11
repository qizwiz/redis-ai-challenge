#!/usr/bin/env python3
"""
Quick test of reactive system components
"""

import json
import time
import redis
from reactive_facade import reactive_facade, IntentType


def test_basic_functionality():
    print("🧪 Quick Reactive System Test")
    print("=" * 40)

    # Test Redis connection
    print("📡 Testing Redis connection...")
    try:
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.ping()
        print("   ✅ Redis connected")
    except Exception as e:
        print(f"   ❌ Redis error: {e}")
        return False

    # Test intent capture (without running the loop)
    print("📝 Testing intent capture...")
    try:
        intent_id = reactive_facade.capture_intent(
            IntentType.QUERY,
            "Test query from quick test",
            {"test": True, "timestamp": time.time()},
            "quick_test",
        )
        print(f"   ✅ Intent captured: {intent_id}")

        # Check if it was added to Redis stream
        stream_entries = r.xread({"reactive:intents": "0"}, count=1)
        if stream_entries:
            print(f"   ✅ Intent found in Redis stream")
        else:
            print(f"   ⚠️ Intent not found in stream")

    except Exception as e:
        print(f"   ❌ Intent capture error: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test Claude integration
    print("🤖 Testing Claude integration...")
    try:
        from robust_claude_integration import claude_integration

        if claude_integration.is_available():
            response = claude_integration.execute_prompt("Say hello briefly", timeout=5)
            if response.success:
                print(f"   ✅ Claude response: {response.content[:50]}...")
            else:
                print(f"   ⚠️ Claude error: {response.error_message}")
        else:
            print("   ⚠️ Claude not available")

    except Exception as e:
        print(f"   ❌ Claude test error: {e}")
        return False

    print("\n🎯 Basic functionality test complete!")
    return True


def show_system_status():
    print("\n📊 System Status:")
    print("=" * 25)

    # Show Redis streams
    try:
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)

        # Check intent stream
        intent_info = r.xinfo_stream("reactive:intents")
        print(f"Intent stream: {intent_info.get('length', 0)} messages")

        # Check response stream
        try:
            response_info = r.xinfo_stream("reactive:responses")
            print(f"Response stream: {response_info.get('length', 0)} messages")
        except:
            print("Response stream: not created yet")

    except Exception as e:
        print(f"Redis stream info error: {e}")

    # Show Claude status
    try:
        from robust_claude_integration import get_claude_status

        claude_status = get_claude_status()
        print(
            f"Claude: {'Available' if claude_status['available'] else 'Not available'}"
        )
    except:
        print("Claude: Status unknown")


def main():
    success = test_basic_functionality()
    show_system_status()

    if success:
        print("\n✅ All core components working!")
        print("Ready to launch production system:")
        print("   python production_reactive_server.py")
    else:
        print("\n❌ Some components need attention")

    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
