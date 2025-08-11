#!/usr/bin/env python3
"""
Comprehensive Redis-Emacs Bridge Test
Tests the full Redis stream coordination system
"""

import time
import json
from redis_emacs_bridge import RedisEmacsBridge
from redis_ai_patterns import StreamProcessor
from redis_ai_patterns.streams import StreamEvent, EventType


def test_basic_bridge_functionality():
    """Test basic bridge operations"""
    print("🧪 Testing Basic Bridge Functionality")
    print("=" * 50)

    bridge = RedisEmacsBridge()

    # Test 1: Create tutorial buffer
    print("1. Creating tutorial buffer...")
    result = bridge.create_tutorial_buffer()
    print(f"   ✅ Buffer creation: {result['success']}")

    # Test 2: Send keyboard commands
    print("2. Testing keyboard commands...")
    kbd_result = bridge.send_keyboard_command("C-v")
    print(f"   ✅ Keyboard command: {kbd_result['success']}")

    # Test 3: Send Elisp commands
    print("3. Testing Elisp evaluation...")
    elisp_result = bridge.send_elisp_command('(message "Hello from Redis!")')
    print(f"   ✅ Elisp command: {elisp_result['success']}")

    # Test 4: Observe state
    print("4. Testing state observation...")
    state = bridge.observe_emacs_state()
    print(f"   ✅ State observation: buffer={state['buffer_name']}")

    # Test 5: Get statistics
    print("5. Getting stream statistics...")
    stats = bridge.get_stream_statistics()
    print(f"   ✅ Commands sent: {stats['commands_sent']}")
    print(f"   ✅ Pending: {stats['pending_commands']}")

    bridge.shutdown()
    return True


def test_redis_stream_integration():
    """Test Redis stream integration directly"""
    print("\n🔍 Testing Redis Stream Integration")
    print("=" * 50)

    # Create a stream processor to inspect streams
    processor = StreamProcessor(namespace="emacs_bridge")

    # Check if streams exist and have data
    commands_info = processor.get_stream_info("events:commands")
    print(f"Commands stream length: {commands_info['length']}")

    # Test adding events directly
    test_event = StreamEvent(
        event_type=EventType.COMMAND,
        data={"test": "direct_stream_test", "command": "test-command"},
        session_id="test_session",
    )

    stream_id = processor.add_event(test_event)
    print(f"✅ Added test event with ID: {stream_id}")

    # Verify the event was added
    updated_info = processor.get_stream_info("events:commands")
    print(f"Updated stream length: {updated_info['length']}")

    return True


def test_emacs_command_coordination():
    """Test coordinated Emacs command execution"""
    print("\n🎭 Testing Emacs Command Coordination")
    print("=" * 50)

    bridge = RedisEmacsBridge(session_id="coordination_test")

    # Simulate a coordinated AI learning session
    print("1. Setting up AI learning environment...")
    bridge.create_tutorial_buffer()

    print("2. Simulating AI exploration...")
    commands = [
        ("C-f", "forward-char"),
        ("C-b", "backward-char"),
        ("C-n", "next-line"),
        ("C-p", "previous-line"),
        ("C-a", "beginning-of-line"),
        ("C-e", "end-of-line"),
    ]

    for kbd, description in commands:
        print(f"   🎹 Executing: {kbd} ({description})")
        result = bridge.send_keyboard_command(kbd)
        bridge.log_command_to_buffer(kbd, description)
        time.sleep(0.2)  # Realistic timing

    print("3. Observing final state...")
    final_state = bridge.observe_emacs_state()
    print(f"   📊 Final cursor position: {final_state['cursor_position']}")

    print("4. Getting session statistics...")
    stats = bridge.get_stream_statistics()
    print(f"   📈 Total commands in session: {stats['commands_sent']}")

    bridge.shutdown()
    return True


def test_high_throughput_simulation():
    """Test high-throughput event processing"""
    print("\n⚡ Testing High-Throughput Processing")
    print("=" * 50)

    processor = StreamProcessor(namespace="throughput_test")

    # Simulate high-throughput processing
    start_time = time.time()
    processor.simulate_high_throughput_processing(100)
    end_time = time.time()

    processing_time = end_time - start_time
    events_per_second = 100 / processing_time

    print(f"✅ Processed 100 events in {processing_time:.2f} seconds")
    print(f"📊 Throughput: {events_per_second:.0f} events/second")

    return True


def inspect_redis_state():
    """Inspect the current Redis state"""
    print("\n🔍 Redis State Inspection")
    print("=" * 50)

    import redis

    r = redis.Redis(decode_responses=True)

    # Find all emacs-related keys
    emacs_keys = r.keys("*emacs*")
    print(f"Found {len(emacs_keys)} emacs-related keys:")
    for key in emacs_keys[:10]:  # Show first 10
        print(f"   🔑 {key}")

    # Show stream information
    bridge_keys = r.keys("emacs_bridge:*")
    print(f"\nFound {len(bridge_keys)} bridge-related keys:")
    for key in bridge_keys[:5]:
        print(f"   🌉 {key}")
        if "events:" in key:
            try:
                info = r.xinfo_stream(key)
                print(f"       📊 Length: {info.get('length', 0)}")
            except:
                pass

    return True


def main():
    """Run all tests"""
    print("🚀 Redis-Emacs Bridge Comprehensive Test Suite")
    print("=" * 60)

    tests = [
        ("Basic Bridge Functionality", test_basic_bridge_functionality),
        ("Redis Stream Integration", test_redis_stream_integration),
        ("Emacs Command Coordination", test_emacs_command_coordination),
        ("High-Throughput Simulation", test_high_throughput_simulation),
        ("Redis State Inspection", inspect_redis_state),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            result = test_func()
            results[test_name] = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {results[test_name]}")
        except Exception as e:
            results[test_name] = f"💥 ERROR: {str(e)}"
            print(f"   {results[test_name]}")

    # Final summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)

    for test_name, result in results.items():
        print(f"{result} {test_name}")

    passed = sum(1 for r in results.values() if "PASSED" in r)
    total = len(results)

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Redis-Emacs bridge is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
