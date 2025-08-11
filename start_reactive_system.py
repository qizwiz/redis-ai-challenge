#!/usr/bin/env python3
"""
Start the Complete Reactive AI Development System
Revolutionary AI development coordination system - production ready
"""

import os
import sys
import subprocess
import time
import redis
import signal
import threading
from pathlib import Path


def check_redis():
    """Check if Redis is running"""
    try:
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis is running")
        return True
    except:
        print("❌ Redis not running - starting it...")
        return False


def start_redis():
    """Start Redis if not running"""
    try:
        subprocess.run(
            ["brew", "services", "start", "redis"], check=True, capture_output=True
        )
        time.sleep(2)
        return check_redis()
    except subprocess.CalledProcessError:
        try:
            subprocess.Popen(
                ["redis-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(3)
            return check_redis()
        except:
            print("❌ Failed to start Redis")
            return False


def main():
    print("🚀 Starting Revolutionary Reactive AI Development System")
    print("=" * 70)
    print("Standing on Giants' Shoulders - Redis AI Challenge 2025")
    print()

    # Ensure log directory exists
    log_dir = Path("/Users/jonathanhill/.redis-ai-logs")
    log_dir.mkdir(exist_ok=True)

    # Check/start Redis
    if not check_redis():
        if not start_redis():
            print("❌ Cannot start system without Redis")
            sys.exit(1)

    # Show system status
    print("🔍 System Status:")
    print(f"   Redis: ✅ Running")

    # Check Claude Code integration
    try:
        from robust_claude_integration import get_claude_status

        claude_status = get_claude_status()
        status_icon = "✅" if claude_status["available"] else "⚠️"
        print(f"   Claude: {status_icon} {claude_status['status']}")
    except ImportError:
        print("   Claude: ⚠️ Integration module not found")

    print()
    print("🎭 Available Interfaces:")
    print("   🌐 Web Dashboard: http://localhost:8883")
    print("   🔌 SocketIO API: ws://localhost:8883")
    print("   📡 REST API: http://localhost:8883/api/")
    print("   🎼 Composable Modes: C-c C-a in Emacs")
    print()

    # Ask user what to start
    print("What would you like to launch?")
    print("1. Full Production Server (Web + API + Reactive Loop)")
    print("2. Test Reactive Facade Only")
    print("3. Test Composable Modes (Emacs)")
    print("4. Interactive Demo")

    choice = input("\nEnter choice (1-4) or press Enter for Full System: ").strip()

    if choice == "2":
        print("\n🧪 Testing Reactive Facade...")
        from reactive_facade import reactive_facade
        import asyncio

        async def test_facade():
            # Start reactive loop
            loop_task = asyncio.create_task(reactive_facade.start_reactive_loop())

            # Test intent capture
            print("📝 Capturing test intent...")
            intent_id = reactive_facade.capture_intent(
                reactive_facade.IntentType.QUERY,
                "How do I implement error handling in Python?",
                {"file": "test.py", "line": 42, "context": "production code"},
                "test",
            )
            print(f"✅ Intent captured: {intent_id}")

            # Let it process
            await asyncio.sleep(3)

            print("🛑 Stopping test...")
            reactive_facade.stop()
            await loop_task

        asyncio.run(test_facade())

    elif choice == "3":
        print("\n🎼 Testing Composable Modes...")
        emacs_file = Path(__file__).parent / "composable_modes.el"
        if emacs_file.exists():
            print(f"📄 Load this file in Emacs: {emacs_file}")
            print("Then run: M-x redis-ai-demo")
            print("Or use: C-c C-a for natural commands")
        else:
            print("❌ composable_modes.el not found")

    elif choice == "4":
        print("\n🎭 Interactive Demo...")
        print("Starting simplified demo server...")

        # Simple demo using just the reactive facade
        from reactive_facade import reactive_facade, IntentType
        import asyncio

        async def interactive_demo():
            print("🚀 Reactive facade started!")
            print("Type commands (or 'quit' to exit):")

            # Start reactive loop in background
            loop_task = asyncio.create_task(reactive_facade.start_reactive_loop())

            while True:
                try:
                    command = input("\n> ").strip()
                    if command.lower() in ["quit", "exit", "q"]:
                        break

                    if command:
                        intent_id = reactive_facade.capture_intent(
                            IntentType.COMMAND,
                            command,
                            {"source": "interactive", "timestamp": time.time()},
                            "demo",
                        )
                        print(f"📝 Captured intent: {intent_id}")

                except KeyboardInterrupt:
                    break

            print("\n🛑 Shutting down demo...")
            reactive_facade.stop()
            await loop_task

        asyncio.run(interactive_demo())

    else:
        # Default: Full production server
        print("\n🚀 Starting Full Production System...")
        print("   Web Dashboard: http://localhost:8883")
        print("   Press Ctrl+C to stop")
        print()

        try:
            from production_reactive_server import ProductionReactiveServer

            server = ProductionReactiveServer()
            server.start()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        except Exception as e:
            print(f"❌ Server error: {e}")
            return 1

    print("\n✅ System shutdown complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
