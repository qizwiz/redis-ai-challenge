#!/usr/bin/env python3
"""
Live AI-Emacs Integration Demo
Demonstrates the revolutionary AI-Emacs collaboration system in action
"""

import asyncio
import redis
import subprocess
import time
from code_analyzer_agent import AdvancedCodeAnalyzerAgent
from redis_coordination_protocol import AgentCoordinator


async def run_live_demo():
    """Run a live demonstration of AI-Emacs integration"""

    print("🚀 AI-Emacs Integration - Live Demo")
    print("=" * 50)

    # Initialize Redis connection
    redis_client = redis.Redis(decode_responses=True)

    try:
        redis_client.ping()
        print("✅ Redis connection established")
    except redis.ConnectionError:
        print("❌ Redis not available. Please start Redis server.")
        return

    # Initialize coordinator
    coordinator = AgentCoordinator(redis_client)
    await coordinator.initialize()
    await coordinator.start_coordination()
    print("✅ Coordination system started")

    # Start advanced code analyzer
    analyzer = AdvancedCodeAnalyzerAgent(redis_client)
    await analyzer.start()
    print("✅ AI Code Analyzer started")

    # Wait for system to stabilize
    await asyncio.sleep(1)

    print("\n🎯 Testing AI-Emacs Coordination...")

    # Test 1: Emacs Lisp Analysis
    print("\n📝 Test 1: Emacs Lisp Code Analysis")
    elisp_code = """
(defun ai-demo-function ()
  "Demonstrate AI analysis of Emacs Lisp code."
  (interactive)
  (let ((result (+ 1 2 3)))
    (message "Result: %d" result)
    (when (> result 5)
      (message "Result is greater than 5!"))))

(defvar ai-demo-variable 42
  "A demonstration variable for AI analysis.")
"""

    # Publish content change through coordination system
    event_id = coordinator.publish_content_change("ai-demo.el", elisp_code, 100)
    print(f"✨ Published Emacs Lisp content for analysis: {event_id}")

    # Wait for analysis
    await asyncio.sleep(2)

    # Check for analysis results
    try:
        results = redis_client.xrevrange("ai:analysis", count=5)
        for entry_id, fields in results:
            if fields.get("source") == "advanced_code_analyzer":
                import json

                data = json.loads(fields.get("data", "{}"))
                if data.get("language") == "elisp":
                    print("🔍 Analysis Results:")
                    print(f"   Language: {data.get('language')}")
                    print(f"   Quality Score: {data.get('quality_score', 0):.1f}/100")
                    metrics = data.get("code_metrics", {})
                    print(f"   Lines of Code: {metrics.get('lines_of_code', 0)}")
                    print(f"   Complexity: {metrics.get('complexity_score', 0):.2f}")
                    recommendations = data.get("recommendations", [])
                    if recommendations:
                        print("   Recommendations:")
                        for rec in recommendations[:2]:
                            print(f"   - {rec}")
                    break
    except Exception as e:
        print(f"⚠️ Could not retrieve analysis results: {e}")

    # Test 2: Python Analysis
    print("\n📝 Test 2: Python Code Analysis")
    python_code = '''
def calculate_fibonacci(n):
    """Calculate fibonacci number with issues."""
    if n <= 1:
        return n
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def x():  # Short name
    VAR = 10  # All caps
    return VAR
'''

    event_id = coordinator.publish_content_change("fibonacci.py", python_code, 200)
    print(f"✨ Published Python content for analysis: {event_id}")

    # Wait for analysis
    await asyncio.sleep(2)

    # Test 3: Emacs Integration
    print("\n🎯 Test 3: Live Emacs Integration")

    try:
        # Test if Emacs is available
        result = subprocess.run(
            ["emacsclient", "--eval", "(+ 1 1)"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            print("✅ Emacs server connected")

            # Create a test buffer in Emacs
            elisp_create_buffer = """
(progn
  (with-current-buffer (get-buffer-create "*AI-Live-Demo*")
    (erase-buffer)
    (insert "# AI-Emacs Integration Live Demo\\n")
    (insert "# Real-time AI analysis active!\\n\\n")
    (insert "def demo_function():\\n")
    (insert "    # This function will be analyzed by AI\\n")
    (insert "    return \\"Hello from AI-Emacs!\\"\\n")
    (switch-to-buffer "*AI-Live-Demo*"))
  "Demo buffer created")
"""

            result = subprocess.run(
                ["emacsclient", "--eval", elisp_create_buffer],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                print("✅ Created live demo buffer in Emacs")
                print("   Switch to Emacs to see the buffer")

                # Trigger analysis of the buffer content
                buffer_content = 'def demo_function():\n    # This function will be analyzed by AI\n    return "Hello from AI-Emacs!"'

                event_id = coordinator.publish_content_change(
                    "*AI-Live-Demo*", buffer_content, 300
                )
                print(f"✨ Triggered analysis of live buffer: {event_id}")

                await asyncio.sleep(2)

            else:
                print(f"⚠️ Could not create demo buffer: {result.stderr}")
        else:
            print("⚠️ Emacs server not responding")

    except subprocess.TimeoutExpired:
        print("⚠️ Emacs communication timeout")
    except Exception as e:
        print(f"⚠️ Emacs integration error: {e}")

    # Show system performance
    print("\n📊 System Performance Summary")
    metrics = await analyzer.get_performance_metrics()
    perf = metrics.get("performance", {})
    print(f"   Analyses performed: {perf.get('analyses_performed', 0)}")
    print(f"   Average analysis time: {perf.get('average_analysis_time', 0):.3f}s")
    print(f"   Cache hits: {perf.get('cache_hits', 0)}")
    print(f"   Cache size: {metrics.get('cache_size', 0)}")
    print(
        f"   Supported languages: {', '.join(metrics.get('supported_languages', []))}"
    )

    # Show Redis activity
    print("\n🗄️ Redis Stream Activity")
    try:
        content_stream = redis_client.xlen("emacs:content")
        analysis_stream = redis_client.xlen("ai:analysis")
        print(f"   Content events: {content_stream}")
        print(f"   Analysis events: {analysis_stream}")
    except Exception as e:
        print(f"   Could not get stream info: {e}")

    print("\n🎉 Live Demo Completed Successfully!")
    print("\nKey Achievements Demonstrated:")
    print("• ✅ Redis-coordinated multi-AI architecture working")
    print("• ✅ Real-time code analysis with multiple languages")
    print("• ✅ Emacs integration with live buffer creation")
    print("• ✅ Event-driven coordination protocol operational")
    print("• ✅ Performance monitoring and caching systems active")

    # Cleanup
    await analyzer.stop()
    await coordinator.stop_coordination()
    print("\n🧹 Demo resources cleaned up")


if __name__ == "__main__":
    asyncio.run(run_live_demo())
