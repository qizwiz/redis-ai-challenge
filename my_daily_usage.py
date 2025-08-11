#!/usr/bin/env python3
"""
How I Actually Use the AI Workforce System

This is my real daily workflow - not a demo, but how I'd actually use this.
"""

import asyncio
import redis
import os
from pathlib import Path
from always_on_ai_workforce import AlwaysOnWorkforceManager, BackgroundTaskType


async def my_daily_workflow():
    """How I use the AI workforce in my actual development workflow"""

    print("🤖 MY DAILY AI WORKFORCE USAGE")
    print("=" * 50)
    print("Starting my development session...")
    print()

    # Initialize the system (this would be automatic in production)
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    workforce = AlwaysOnWorkforceManager(redis_client)

    # Deploy the workforce
    print("🚀 Deploying my AI workforce...")
    workforce.deploy_workforce()

    # Check what my agents have been working on while I was away
    print("\n📬 Checking what my agents did while I was away...")
    notifications = workforce.get_user_notifications()

    if notifications:
        print("✅ Work completed while I was away:")
        for notification in notifications:
            print(f"   • {notification['description']}")
            if notification.get("artifacts"):
                for artifact in notification["artifacts"]:
                    print(f"     📁 {artifact}")
    else:
        print("📬 No new work completed (agents just started)")

    print("\n📊 Current workforce status:")
    status = workforce.get_workforce_status()
    overview = status["workforce_overview"]
    print(f"   Active agents: {overview['active_agents']}")
    print(f"   Work completed today: {overview['total_work_completed']}")
    print(f"   Value generated: ${overview['total_value_added']:.2f}")

    # Now I'm going to assign some specific work I actually want done
    print("\n📋 Assigning work I actually want done:")

    # 1. I want tests for the MCP server functions - this is important for reliability
    print("1. Generating tests for MCP server functions...")
    workforce.assign_work_to_agent(
        BackgroundTaskType.TEST_GENERATION,
        "Generate comprehensive tests for MCP server endpoints",
        ["/Users/jonathanhill/src/redis-ai-challenge/claude_repl_mcp_server.py"],
        priority=5,  # High priority
    )

    # 2. I want documentation for the complex test functions
    print("2. Documenting complex test functions...")
    workforce.assign_work_to_agent(
        BackgroundTaskType.DOCUMENTATION,
        "Document the complex test_docstring_synthesis_with_mock function",
        ["/Users/jonathanhill/src/redis-ai-challenge/test_docstring_synthesis_mock.py"],
        priority=3,
    )

    # 3. I want the execution engine itself to be tested
    print("3. Creating tests for the AI execution engine...")
    workforce.assign_work_to_agent(
        BackgroundTaskType.TEST_GENERATION,
        "Generate tests for AI execution engine core functionality",
        ["/Users/jonathanhill/src/redis-ai-challenge/ai_execution_engine.py"],
        priority=4,
    )

    print("\n⏰ Letting agents work while I do other things...")
    print("   (In real usage, I'd go write code or have meetings)")
    print("   (Agents work in background - I check back later)")

    # In real usage, I'd do other work here. For demo, we'll wait a bit.
    await asyncio.sleep(30)  # Wait 30 seconds

    # Check progress
    print("\n📊 Checking progress after 30 seconds...")
    notifications = workforce.get_user_notifications()

    if notifications:
        print("✅ New work completed:")
        for notification in notifications:
            print(f"   📝 {notification['description']}")
            if notification.get("artifacts"):
                for artifact in notification["artifacts"]:
                    print(f"      📁 Created: {Path(artifact).name}")

                    # Show me what was actually created
                    if Path(artifact).exists():
                        size = Path(artifact).stat().st_size
                        print(f"         Size: {size} bytes")

                        # If it's a test file, show me the structure
                        if "test_" in artifact.lower():
                            try:
                                with open(artifact, "r") as f:
                                    content = f.read()
                                test_methods = [
                                    line.strip()
                                    for line in content.split("\n")
                                    if line.strip().startswith("def test_")
                                ]
                                if test_methods:
                                    print(f"         Test methods: {len(test_methods)}")
                                    for method in test_methods[:3]:
                                        print(
                                            f"           • {method.replace('def ', '').replace('(', '').replace(':', '')}"
                                        )
                            except:
                                pass
    else:
        print("⏳ Agents still working... (check back later)")

    # Show current status
    print("\n📊 Final status check:")
    status = workforce.get_workforce_status()
    overview = status["workforce_overview"]

    print(f"   Total value generated today: ${overview['total_value_added']:.2f}")
    print(f"   Agents still active: {overview['active_agents']}")

    for agent_id, agent_status in status["agent_statuses"].items():
        if agent_status.get("queue_length", 0) > 0:
            print(f"   🔄 {agent_id}: {agent_status['queue_length']} queued tasks")

    print("\n🎯 How this changes my workflow:")
    print("   ✅ I assign high-level work and forget about it")
    print("   ✅ Agents work while I focus on architecture/features")
    print("   ✅ I get notifications when important work is done")
    print("   ✅ Code quality improves without my constant attention")
    print("   ✅ Test coverage grows automatically")
    print("   ✅ Documentation stays up to date")

    print("\n💭 Real usage patterns:")
    print("   • Morning: Check what agents did overnight")
    print("   • Before big features: Assign comprehensive testing")
    print("   • During code review: Assign documentation for complex functions")
    print("   • End of day: Assign cleanup and quality improvements")
    print("   • Vacation: Come back to significantly improved codebase")

    print("\n🚀 This is how I work with AI: Maximum leverage, minimum micromanagement")

    # In production, I would NOT shut down the workforce - they keep working
    print("\n🔄 In real usage, agents would continue working 24/7...")
    print("   For demo, shutting down...")
    workforce.shutdown_workforce()


if __name__ == "__main__":
    asyncio.run(my_daily_workflow())
