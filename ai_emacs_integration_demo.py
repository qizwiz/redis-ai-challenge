#!/usr/bin/env python3
"""
AI-Emacs Integration System Demo
Comprehensive demonstration of the Redis-coordinated multi-AI development environment
"""

import asyncio
import json
import redis
import time
import subprocess
import sys
from typing import Dict, List, Any
from redis_coordination_protocol import AgentCoordinator, EventType, CoordinationEvent
from code_analyzer_agent import AdvancedCodeAnalyzerAgent


class LiveDemo:
    """Interactive demo of the AI-Emacs integration system"""

    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.coordinator = None
        self.agents = {}
        self.demo_buffers = {
            "elisp_example": """
;; AI-Emacs Integration Example
(defun ai-workspace-demo ()
  "Demonstrate AI workspace functionality."
  (interactive)
  (let ((buffer (get-buffer-create "*AI-Demo*")))
    (with-current-buffer buffer
      (erase-buffer)
      (insert "AI-Emacs Integration Demo\n")
      (insert "==========================\n\n")
      (insert "This demonstrates real-time AI collaboration!\n")
      (ai-workspace-mode))
    (switch-to-buffer buffer)))

(defvar ai-demo-variable 42
  "Demo variable for AI analysis.")
""",
            "python_example": '''
# AI-Emacs Integration Python Example
import asyncio
import redis

class AIAssistant:
    """AI assistant for development tasks"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.analysis_cache = {}
    
    async def analyze_code(self, content):
        """Analyze code with AI assistance"""
        if len(content) < 10:
            return {"error": "Content too short"}
        
        # Simulate AI analysis
        analysis = {
            "complexity": len(content) / 100,
            "suggestions": ["Add type hints", "Consider async/await"],
            "quality_score": 85.5
        }
        
        return analysis

def demo_function():
    # This function has some complexity
    for i in range(10):
        if i % 2 == 0:
            print(f"Even number: {i}")
        else:
            print(f"Odd number: {i}")
''',
        }

    async def initialize(self):
        """Initialize the demo system"""
        print("🚀 Initializing AI-Emacs Integration Demo...")

        # Test Redis connection
        try:
            self.redis_client.ping()
            print("✅ Redis connection established")
        except redis.ConnectionError:
            print("❌ Could not connect to Redis. Please start Redis server:")
            print("   brew services start redis  (macOS)")
            print("   sudo systemctl start redis (Linux)")
            return False

        # Initialize coordinator
        self.coordinator = AgentCoordinator(self.redis_client)
        await self.coordinator.initialize()
        print("✅ Redis coordination protocol initialized")

        # Start coordination
        await self.coordinator.start_coordination()
        print("✅ Agent coordination started")

        return True

    async def start_agents(self):
        """Start AI agents"""
        print("\n🤖 Starting AI Agents...")

        # Start code analyzer agent
        code_analyzer = AdvancedCodeAnalyzerAgent(self.redis_client)
        await code_analyzer.start()
        self.agents["code_analyzer"] = code_analyzer
        print("✅ Advanced Code Analyzer Agent started")

        # Wait for agents to register
        await asyncio.sleep(1)

        # Show agent status
        status = self.coordinator.get_agent_status()
        print(f"📊 Active agents: {len(status['active_agents'])}")

    async def demo_content_analysis(self):
        """Demonstrate real-time content analysis"""
        print("\n📝 Demonstrating Real-time Content Analysis...")

        for buffer_name, content in self.demo_buffers.items():
            print(f"\n📄 Analyzing {buffer_name}...")

            # Publish content change
            event_id = self.coordinator.publish_content_change(
                buffer_name, content, 100
            )
            print(f"✨ Published content change event: {event_id}")

            # Wait for analysis
            await asyncio.sleep(5)  # Increased sleep duration

            # Check for analysis results
            await self._check_analysis_results(buffer_name)

    async def _check_analysis_results(self, buffer_name: str):
        """Check for analysis results in Redis streams"""
        try:
            # Read recent analysis results
            analysis_stream = "ai:analysis"
            entries = self.redis_client.xrevrange(analysis_stream, count=5)

            for entry_id, fields in entries:
                if fields.get("source") == "advanced_code_analyzer":
                    data = json.loads(fields.get("data", "{}"))
                    if data.get("buffer_name") == buffer_name:
                        print(f"🔍 Analysis completed for {buffer_name}:")

                        # Show analysis results
                        if "syntax_issues" in data:
                            issues = data["syntax_issues"]
                            print(f"   Syntax issues found: {len(issues)}")
                            for issue in issues[:3]:  # Show first 3 issues
                                print(f"   - Line {issue['line']}: {issue['message']}")

                        if "code_metrics" in data:
                            metrics = data["code_metrics"]
                            print(f"   Code quality metrics:")
                            print(f"   - Lines of code: {metrics['lines_of_code']}")
                            print(
                                f"   - Complexity score: {metrics['complexity_score']:.2f}"
                            )
                            print(
                                f"   - Maintainability: {metrics['maintainability_index']:.1f}/100"
                            )

                        if "quality_score" in data:
                            print(
                                f"   Overall quality score: {data['quality_score']:.1f}/100"
                            )

                        if "recommendations" in data:
                            print(f"   AI recommendations:")
                            for rec in data["recommendations"][:2]:
                                print(f"   - {rec}")

                        return

            print(f"⏳ Analysis in progress for {buffer_name}...")

        except Exception as e:
            print(f"⚠️  Could not retrieve analysis results: {e}")

    async def demo_emacs_integration(self):
        """Demonstrate Emacs integration (if available)"""
        print("\n🎯 Demonstrating Emacs Integration...")

        try:
            # Check if emacsclient is available
            result = subprocess.run(
                ["which", "emacsclient"], capture_output=True, text=True
            )

            if result.returncode != 0:
                print("⚠️  emacsclient not found. Emacs integration demo skipped.")
                print("   To test Emacs integration:")
                print("   1. Start Emacs with server: emacs --daemon")
                print("   2. Load ai-workspace.el in Emacs")
                print("   3. Run: M-x ai-workspace-create")
                return

            print("✅ emacsclient found - testing Emacs integration")

            # Test basic Emacs communication
            test_elisp = """
(progn
  (message "AI-Emacs Integration Demo: Connection established!")
  (get-buffer-create "*AI-Integration-Test*")
  "success")
"""

            result = subprocess.run(
                ["emacsclient", "--eval", test_elisp],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                print("✅ Emacs communication successful")
                print(f"   Result: {result.stdout.strip()}")

                # Demonstrate AI workspace creation
                await self._demo_ai_workspace()
            else:
                print(f"⚠️  Emacs communication failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("⚠️  Emacs communication timeout")
        except Exception as e:
            print(f"⚠️  Emacs integration error: {e}")

    async def _demo_ai_workspace(self):
        """Demonstrate AI workspace functionality"""
        print("\n🏗️  Creating AI Workspace in Emacs...")

        workspace_elisp = """
(progn
  ;; Load ai-workspace if available
  (when (file-exists-p "ai-workspace.el")
    (load-file "ai-workspace.el"))
  
  ;; Create workspace buffer
  (let ((buffer (get-buffer-create "*AI-Workspace-Demo*")))
    (with-current-buffer buffer
      (erase-buffer)
      (insert "AI-Emacs Integration Workspace\n")
      (insert "==============================\n\n")
      (insert "🤖 AI agents are now monitoring this workspace!\n\n")
      (insert "Real-time capabilities:\n")
      (insert "• Syntax analysis as you type\n")
      (insert "• Code quality metrics\n")
      (insert "• Intelligent suggestions\n")
      (insert "• Multi-language support\n\n")
      (insert "Try editing this buffer to see AI analysis!\n"))
    (switch-to-buffer buffer)
    "AI Workspace created")
"""

        try:
            result = subprocess.run(
                ["emacsclient", "--eval", workspace_elisp],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                print("✅ AI Workspace created in Emacs")
                print("   Switch to Emacs to see the workspace buffer")

                # Simulate workspace activity
                await self._simulate_workspace_activity()
            else:
                print(f"⚠️  Workspace creation failed: {result.stderr}")

        except Exception as e:
            print(f"⚠️  Workspace demo error: {e}")

    async def _simulate_workspace_activity(self):
        """Simulate workspace activity for demo"""
        print("\n⚡ Simulating workspace activity...")

        # Simulate typing in workspace
        activities = [
            ("User types in buffer", "*AI-Workspace-Demo*", "New content added"),
            ("Buffer switch event", "*scratch*", "Switched to scratch buffer"),
            ("Code completion request", "*AI-Workspace-Demo*", "def analyze_"),
        ]

        for activity_desc, buffer_name, content in activities:
            print(f"   📝 {activity_desc}")

            # Publish activity
            self.coordinator.publish_content_change(
                buffer_name, content, int(time.time())
            )

            await asyncio.sleep(5)  # Increased sleep duration

    async def demo_redis_streams(self):
        """Demonstrate Redis streams inspection"""
        print("\n🔍 Redis Streams Activity Summary...")

        for stream_name in ["emacs:content", "ai:analysis", "system:status"]:
            try:
                entries = self.redis_client.xrevrange(stream_name, count=3)
                print(f"\n📊 Stream: {stream_name}")
                print(f"   Recent entries: {len(entries)}")

                for entry_id, fields in entries:
                    timestamp = float(fields.get("timestamp", 0))
                    time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
                    source = fields.get("source", "unknown")
                    print(f"   - {time_str} from {source}")

            except Exception as e:
                print(f"   ⚠️  Could not read {stream_name}: {e}")

    async def show_performance_metrics(self):
        """Show system performance metrics"""
        print("\n📈 System Performance Metrics...")

        # Agent performance
        for agent_name, agent in self.agents.items():
            if hasattr(agent, "get_performance_metrics"):
                metrics = await agent.get_performance_metrics()
                print(f"\n🤖 {agent_name}:")
                perf = metrics.get("performance", {})
                print(f"   Analyses performed: {perf.get('analyses_performed', 0)}")
                print(
                    f"   Average analysis time: {perf.get('average_analysis_time', 0):.3f}s"
                )
                print(f"   Cache hits: {perf.get('cache_hits', 0)}")
                print(f"   Cache size: {metrics.get('cache_size', 0)}")

        # Redis metrics
        try:
            info = self.redis_client.info()
            print(f"\n🗄️  Redis:")
            print(f"   Connected clients: {info.get('connected_clients', 0)}")
            print(f"   Used memory: {info.get('used_memory_human', 'unknown')}")
            print(
                f"   Total commands processed: {info.get('total_commands_processed', 0)}"
            )
        except Exception as e:
            print(f"   ⚠️  Could not get Redis info: {e}")

    async def cleanup(self):
        """Cleanup demo resources"""
        print("\n🧹 Cleaning up demo resources...")

        # Stop agents
        for agent_name, agent in self.agents.items():
            await agent.stop()
            print(f"✅ Stopped {agent_name}")

        # Stop coordinator
        if self.coordinator:
            await self.coordinator.stop_coordination()
            print("✅ Stopped coordination system")

    async def run_interactive_demo(self):
        """Run interactive demo with user prompts"""
        print("\n🎮 Interactive Demo Mode")
        print("Press Enter to continue through each demo section...")

        sections = [
            ("Content Analysis", self.demo_content_analysis),
            ("Emacs Integration", self.demo_emacs_integration),
            ("Redis Streams", self.demo_redis_streams),
            ("Performance Metrics", self.show_performance_metrics),
        ]

        for section_name, section_func in sections:
            input(f"\n▶️  Press Enter to run: {section_name}")
            await section_func()

    async def run_full_demo(self):
        """Run complete demo sequence"""
        print("🎬 AI-Emacs Integration System - Full Demo")
        print("=" * 50)

        # Initialize
        if not await self.initialize():
            return

        try:
            # Start agents
            await self.start_agents()

            # Run demo sections
            await self.demo_content_analysis()
            await self.demo_emacs_integration()
            await self.demo_redis_streams()
            await self.show_performance_metrics()

            await asyncio.sleep(10)  # Added final sleep to keep agents alive

        finally:
            await self.cleanup()


async def main():
    """Main demo entry point"""
    demo = LiveDemo()

    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        await demo.initialize()
        await demo.start_agents()
        try:
            await demo.run_interactive_demo()
        finally:
            await demo.cleanup()
    else:
        await demo.run_full_demo()


if __name__ == "__main__":
    print(
        """
╔══════════════════════════════════════════════════════════════╗
║                   AI-Emacs Integration Demo                  ║
║              Redis-Coordinated Multi-AI System              ║
╚══════════════════════════════════════════════════════════════╝

This demo showcases:
• Real-time AI code analysis
• Redis coordination protocol  
• Multi-agent AI system
• Emacs workspace integration
• Living documentation system

Usage:
  python3 ai_emacs_integration_demo.py           # Full auto demo
  python3 ai_emacs_integration_demo.py --interactive  # Step-by-step

Prerequisites:
• Redis server running
• Python packages: redis, asyncio
• Optional: Emacs with ai-workspace.el loaded
"""
    )

    asyncio.run(main())
