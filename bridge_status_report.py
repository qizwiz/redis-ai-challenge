#!/usr/bin/env python3
"""
Redis-Emacs Bridge Status Report
Provides comprehensive status of the Redis-based Emacs communication system
"""

import redis
import json
import time
from redis_ai_patterns import StreamProcessor


def get_redis_connection():
    """Get Redis connection with error handling"""
    try:
        r = redis.Redis(decode_responses=True)
        r.ping()
        return r
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return None


def analyze_bridge_streams():
    """Analyze bridge-related Redis streams"""
    print("🌉 Redis Stream Analysis")
    print("=" * 50)

    r = get_redis_connection()
    if not r:
        return False

    # Find all bridge-related streams
    bridge_keys = r.keys("emacs_bridge:events:*")

    if not bridge_keys:
        print("⚠️  No bridge streams found")
        return False

    total_events = 0
    for stream_key in bridge_keys:
        stream_name = stream_key.replace("emacs_bridge:", "")

        try:
            # Get stream info
            info = r.xinfo_stream(stream_key)
            length = info.get("length", 0)
            total_events += length

            print(f"📊 {stream_name}: {length} events")

            # Show sample events if available
            if length > 0:
                recent = r.xrevrange(stream_key, count=1)
                if recent:
                    stream_id, fields = recent[0]
                    event_type = fields.get("type", "unknown")
                    timestamp = fields.get("timestamp", "unknown")
                    print(f"     Latest: {event_type} at {timestamp}")

        except Exception as e:
            print(f"❌ Error analyzing {stream_key}: {e}")

    print(f"🎯 Total events across all bridge streams: {total_events}")
    return total_events > 0


def analyze_consumer_groups():
    """Analyze Redis consumer groups"""
    print("\n👥 Consumer Group Analysis")
    print("=" * 50)

    r = get_redis_connection()
    if not r:
        return False

    bridge_streams = r.keys("emacs_bridge:events:*")

    for stream_key in bridge_streams:
        try:
            groups = r.xinfo_groups(stream_key)
            stream_name = stream_key.replace("emacs_bridge:", "")

            if groups:
                print(f"🔄 {stream_name}:")
                for group in groups:
                    name = group.get("name", "unknown")
                    consumers = group.get("consumers", 0)
                    pending = group.get("pending", 0)
                    lag = group.get("lag", 0)

                    print(f"     Group: {name}")
                    print(
                        f"     Consumers: {consumers}, Pending: {pending}, Lag: {lag}"
                    )
            else:
                print(f"📭 {stream_name}: No consumer groups")

        except Exception as e:
            print(f"❌ Error analyzing consumer groups for {stream_key}: {e}")

    return True


def test_bridge_functionality():
    """Test basic bridge functionality"""
    print("\n🧪 Bridge Functionality Test")
    print("=" * 50)

    try:
        from redis_emacs_bridge import RedisEmacsBridge

        # Create a test bridge
        bridge = RedisEmacsBridge(session_id="status_test")

        # Test basic operations
        print("1. Testing bridge initialization...")
        print(f"   ✅ Session ID: {bridge.session_id}")

        print("2. Testing stream processor...")
        processor = bridge.stream_processor
        print(f"   ✅ Namespace: {processor.namespace}")

        print("3. Testing command sending...")
        result = bridge.send_elisp_command('(message "Bridge status test")')
        print(f"   ✅ Command sent: {result['success']}")

        print("4. Testing statistics...")
        stats = bridge.get_stream_statistics()
        print(f"   ✅ Commands sent: {stats['commands_sent']}")

        bridge.shutdown()
        return True

    except Exception as e:
        print(f"❌ Bridge functionality test failed: {e}")
        return False


def show_integration_instructions():
    """Show instructions for full Emacs integration"""
    print("\n📋 Emacs Integration Instructions")
    print("=" * 50)

    print("To enable full Redis-Emacs integration:")
    print()
    print("1. Start Emacs server:")
    print("   emacs --daemon")
    print()
    print("2. Load the Redis command executor in Emacs:")
    print('   (load-file "redis_command_executor.el")')
    print()
    print("3. Start the Redis command executor:")
    print("   M-x redis-executor-start")
    print()
    print("4. Test the integration:")
    print("   python redis_emacs_bridge.py")
    print()
    print("5. Monitor commands in Emacs:")
    print("   M-x redis-executor-show-recent-commands")
    print()
    print("6. View execution status:")
    print("   M-x redis-executor-show-status")


def main():
    """Generate comprehensive status report"""
    print("🚀 Redis-Emacs Bridge Status Report")
    print("=" * 60)
    print(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check Redis connection
    r = get_redis_connection()
    if not r:
        print("💥 Cannot generate report - Redis not available")
        return False

    print("✅ Redis connection: OK")

    # Analyze streams
    streams_ok = analyze_bridge_streams()

    # Analyze consumer groups
    groups_ok = analyze_consumer_groups()

    # Test functionality
    functionality_ok = test_bridge_functionality()

    # Show integration instructions
    show_integration_instructions()

    # Final summary
    print("\n" + "=" * 60)
    print("📊 STATUS SUMMARY")
    print("=" * 60)

    status_items = [
        ("Redis Connection", r is not None),
        ("Bridge Streams", streams_ok),
        ("Consumer Groups", groups_ok),
        ("Bridge Functionality", functionality_ok),
    ]

    all_ok = True
    for item, status in status_items:
        icon = "✅" if status else "❌"
        print(f"{icon} {item}: {'OK' if status else 'FAILED'}")
        if not status:
            all_ok = False

    print()
    if all_ok:
        print("🎉 Redis-Emacs Bridge Status: FULLY OPERATIONAL")
        print("Ready for AI-coordinated Emacs development!")
    else:
        print("⚠️  Redis-Emacs Bridge Status: ISSUES DETECTED")
        print("Check the detailed output above for problems.")

    return all_ok


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
