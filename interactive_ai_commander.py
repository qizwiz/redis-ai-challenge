#!/usr/bin/env python3
"""
Interactive AI Commander - Your personal interface to the AI workforce

This is how you actually USE the system - a natural language interface
to command autonomous AI agents working on your codebase.
"""

import asyncio
import redis
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any
from ai_execution_engine import RealAIWorkforceEngine
from always_on_ai_workforce import AlwaysOnWorkforceManager, BackgroundTaskType


class AICommander:
    """Interactive commander for the AI workforce"""

    def __init__(self):
        self.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
        self.engine = RealAIWorkforceEngine(self.redis)
        self.workforce = AlwaysOnWorkforceManager(self.redis)
        self.session_history = []

        # Initialize system
        self.redis.set("ai_execution_engine_ready", "true")

    def start_interactive_session(self):
        """Start interactive command session"""

        print("🤖 AI WORKFORCE COMMANDER")
        print("=" * 40)
        print("Your natural language interface to autonomous AI agents")
        print("Type 'help' for commands, 'quit' to exit")
        print()

        # Deploy workforce if not already running
        print("🚀 Initializing AI workforce...")
        self.workforce.deploy_workforce()

        print("\n✅ Ready for commands!")
        print()

    def process_command(self, user_input: str) -> str:
        """Process natural language commands"""

        command = user_input.lower().strip()

        # Built-in commands
        if command == "help":
            return self._show_help()
        elif command == "status":
            return self._show_status()
        elif command == "notifications":
            return self._show_notifications()
        elif command.startswith("find work"):
            return self._find_work_command(user_input)
        elif command.startswith("analyze"):
            return self._analyze_command(user_input)
        elif command.startswith("test"):
            return self._test_command(user_input)
        elif command.startswith("document"):
            return self._document_command(user_input)
        elif command.startswith("improve"):
            return self._improve_command(user_input)
        elif command.startswith("review"):
            return self._review_command(user_input)
        elif "agents" in command and "working" in command:
            return self._agent_status_command()
        elif command == "history":
            return self._show_history()
        else:
            return self._intelligent_command_processing(user_input)

    def _show_help(self) -> str:
        """Show available commands"""

        return """📋 AVAILABLE COMMANDS:

🔍 DISCOVERY:
   • "find work" - Discover work opportunities in codebase
   • "analyze <file>" - Deep analysis of specific file
   • "status" - Show workforce status
   
📝 TASK ASSIGNMENT:
   • "test <file/function>" - Generate tests for file or function
   • "document <file/function>" - Add documentation  
   • "improve <file>" - General code quality improvements
   • "review <file>" - Code review and suggestions
   
📊 MONITORING:
   • "notifications" - Check completed work
   • "what are my agents working on?" - Agent status
   • "history" - Command history
   
💡 NATURAL LANGUAGE:
   You can also use natural language like:
   • "I need comprehensive tests for my payment module"
   • "The user authentication code needs better documentation"
   • "Can you review the recent changes in api.py?"
   • "Find performance issues in the database code"
   
✨ The system understands context and intent!"""

    def _show_notifications(self) -> str:
        """Show recent work notifications"""

        notifications = self.workforce.get_user_notifications()

        if not notifications:
            return "📬 No new notifications - agents are working in background"

        result = f"📬 {len(notifications)} NEW WORK NOTIFICATIONS:\n\n"

        for i, notification in enumerate(notifications[-10:], 1):  # Last 10
            result += f"{i}. ✅ {notification.get('description', 'Work completed')}\n"

            if notification.get("artifacts"):
                for artifact in notification["artifacts"]:
                    file_size = ""
                    if Path(artifact).exists():
                        size = Path(artifact).stat().st_size
                        file_size = f" ({size} bytes)"
                    result += f"   📁 {Path(artifact).name}{file_size}\n"

            if notification.get("value_added"):
                result += f"   💰 Value: ${notification['value_added']:.2f}\n"

            result += "\n"

        return result

    def _find_work_command(self, user_input: str) -> str:
        """Find work opportunities command"""

        opportunities = self.engine.find_autonomous_work_opportunities(os.getcwd())

        result = "🔍 WORK OPPORTUNITIES DISCOVERED:\n\n"

        total_work = 0
        for work_type, items in opportunities.items():
            if items:
                result += f"🎯 {work_type.replace('_', ' ').title()}: {len(items)} opportunities\n"
                total_work += len(items)

                for i, item in enumerate(items[:5], 1):  # Show top 5
                    if work_type == "test_generation":
                        result += f"   {i}. 📝 {item['function_name']} in {Path(item['file_path']).name}\n"
                        result += f"      Complexity: {item['complexity']}, Args: {item['args']}\n"
                    elif work_type == "documentation":
                        result += f"   {i}. 📚 {item['function_name']} (complexity: {item['complexity']})\n"
                        result += f"      File: {Path(item['file_path']).name}\n"
                    elif work_type == "code_quality":
                        result += f"   {i}. 🔧 {item['issue_type']} in {Path(item['file_path']).name}\n"
                        result += f"      Issue: {item['description']}\n"

                result += "\n"

        result += f"💡 Total: {total_work} work opportunities ready for assignment!"
        return result

    def _analyze_command(self, user_input: str) -> str:
        """Analyze file command"""

        # Extract filename from command
        parts = user_input.split()
        if len(parts) < 2:
            return "❌ Please specify a file: analyze <filename>"

        filename = parts[1]

        # Find matching files
        matching_files = list(Path(".").rglob(f"*{filename}*"))
        if not matching_files:
            return f"❌ No files found matching '{filename}'"

        target_file = str(matching_files[0])
        analysis = self.engine.code_analyzer.analyze_python_file(target_file)

        if "error" in analysis:
            return f"❌ Analysis failed: {analysis['error']}"

        result = f"🔍 DEEP ANALYSIS: {Path(target_file).name}\n\n"
        result += f"📊 METRICS:\n"
        result += f"   • Total Lines: {analysis['total_lines']}\n"
        result += f"   • Functions: {len(analysis['functions'])}\n"
        result += f"   • Classes: {len(analysis['classes'])}\n"
        result += f"   • Imports: {len(analysis['imports'])}\n"
        result += (
            f"   • Documentation Coverage: {analysis['documentation_coverage']:.1%}\n"
        )
        result += f"   • Has Tests: {'✅' if analysis['has_tests'] else '❌'}\n\n"

        result += f"🎯 FUNCTIONS:\n"
        for func in analysis["functions"][:5]:  # Top 5 functions
            result += f"   • {func.name}({', '.join(func.args)}) - Complexity: {func.complexity}\n"
            if func.docstring:
                result += f"     📝 Documented\n"
            else:
                result += f"     ❌ Needs documentation\n"

        return result

    def _test_command(self, user_input: str) -> str:
        """Generate tests command"""

        # Extract target from command
        parts = user_input.split(maxsplit=1)
        if len(parts) < 2:
            return "❌ Please specify what to test: test <file/function>"

        target = parts[1]

        # Find matching files
        matching_files = list(Path(".").rglob(f"*{target}*"))
        if not matching_files:
            return f"❌ No files found matching '{target}'"

        target_file = str(matching_files[0])

        # Assign work to test agent
        self.workforce.assign_work_to_agent(
            BackgroundTaskType.TEST_GENERATION,
            f"Generate comprehensive tests for {target}",
            [target_file],
            priority=4,
        )

        # Track command
        self.session_history.append(
            {
                "command": user_input,
                "timestamp": time.time(),
                "action": "test_generation_assigned",
                "target": target_file,
            }
        )

        return f"✅ Test generation assigned for {Path(target_file).name}\n   🤖 Agent working in background - check 'notifications' for results"

    def _document_command(self, user_input: str) -> str:
        """Generate documentation command"""

        parts = user_input.split(maxsplit=1)
        if len(parts) < 2:
            return "❌ Please specify what to document: document <file/function>"

        target = parts[1]

        # Find matching files
        matching_files = list(Path(".").rglob(f"*{target}*"))
        if not matching_files:
            return f"❌ No files found matching '{target}'"

        target_file = str(matching_files[0])

        # Assign work to documentation agent
        self.workforce.assign_work_to_agent(
            BackgroundTaskType.DOCUMENTATION,
            f"Add comprehensive documentation for {target}",
            [target_file],
            priority=3,
        )

        # Track command
        self.session_history.append(
            {
                "command": user_input,
                "timestamp": time.time(),
                "action": "documentation_assigned",
                "target": target_file,
            }
        )

        return f"✅ Documentation assigned for {Path(target_file).name}\n   🤖 Agent working in background - check 'notifications' for results"

    def _improve_command(self, user_input: str) -> str:
        """Code improvement command"""

        parts = user_input.split(maxsplit=1)
        if len(parts) < 2:
            return "❌ Please specify what to improve: improve <file>"

        target = parts[1]

        # Find matching files
        matching_files = list(Path(".").rglob(f"*{target}*"))
        if not matching_files:
            return f"❌ No files found matching '{target}'"

        target_file = str(matching_files[0])

        # Assign work to quality agent
        self.workforce.assign_work_to_agent(
            BackgroundTaskType.CODE_QUALITY,
            f"Improve code quality for {target}",
            [target_file],
            priority=2,
        )

        return f"✅ Code improvement assigned for {Path(target_file).name}\n   🤖 Agent working in background - check 'notifications' for results"

    def _review_command(self, user_input: str) -> str:
        """Code review command"""

        parts = user_input.split(maxsplit=1)
        if len(parts) < 2:
            return "❌ Please specify what to review: review <file>"

        target = parts[1]

        # Find matching files
        matching_files = list(Path(".").rglob(f"*{target}*"))
        if not matching_files:
            return f"❌ No files found matching '{target}'"

        target_file = str(matching_files[0])

        # Perform immediate review using LLM
        try:
            with open(target_file, "r") as f:
                content = f.read()

            review = self.engine.llm_executor.review_code_changes(
                target_file, content[:2000]
            )  # First 2000 chars

            result = f"🔍 CODE REVIEW: {Path(target_file).name}\n\n"
            result += f"📋 Summary: {review.get('summary', 'Review completed')}\n\n"

            if review.get("issues"):
                result += f"⚠️  Issues Found:\n"
                for i, issue in enumerate(review["issues"][:5], 1):
                    result += f"   {i}. {issue}\n"
                result += "\n"

            if review.get("suggestions"):
                result += f"💡 Suggestions:\n"
                for i, suggestion in enumerate(review["suggestions"][:5], 1):
                    result += f"   {i}. {suggestion}\n"
                result += "\n"

            approval = "✅ Approved" if review.get("approval") else "⚠️ Needs Attention"
            result += f"🎯 Overall: {approval}"

            return result

        except Exception as e:
            return f"❌ Review failed: {e}"

    def _agent_status_command(self) -> str:
        """Show what agents are working on"""

        status = self.workforce.get_workforce_status()

        result = "🤖 AGENT STATUS:\n\n"

        for agent_id, agent_status in status["agent_statuses"].items():
            result += f"🔧 {agent_id}:\n"
            result += f"   Specialty: {agent_status['specialty']}\n"
            result += f"   Status: {agent_status['status']}\n"
            result += f"   Queue Length: {agent_status['queue_length']}\n"
            result += f"   Completed: {agent_status['work_units_completed']}\n"
            result += f"   Failed: {agent_status['work_units_failed']}\n"
            result += f"   Uptime: {agent_status['uptime_hours']:.1f} hours\n"

            if agent_status.get("current_work"):
                result += (
                    f"   🔄 Currently: Working on task {agent_status['current_work']}\n"
                )
            else:
                result += f"   💤 Currently: Idle\n"

            result += "\n"

        return result

    def _intelligent_command_processing(self, user_input: str) -> str:
        """Process natural language commands intelligently"""

        input_lower = user_input.lower()

        # Intent detection based on keywords
        if any(word in input_lower for word in ["test", "testing", "unittest"]):
            # Extract likely filename
            words = user_input.split()
            for word in words:
                if "." in word or any(
                    word.endswith(ext) for ext in [".py", ".js", ".java"]
                ):
                    return self._test_command(f"test {word}")
            return "🤖 I understand you want testing. Please specify: test <filename>"

        elif any(word in input_lower for word in ["document", "docs", "docstring"]):
            words = user_input.split()
            for word in words:
                if "." in word or any(
                    word.endswith(ext) for ext in [".py", ".js", ".java"]
                ):
                    return self._document_command(f"document {word}")
            return "🤖 I understand you want documentation. Please specify: document <filename>"

        elif any(word in input_lower for word in ["review", "check", "look at"]):
            words = user_input.split()
            for word in words:
                if "." in word or any(
                    word.endswith(ext) for ext in [".py", ".js", ".java"]
                ):
                    return self._review_command(f"review {word}")
            return (
                "🤖 I understand you want a review. Please specify: review <filename>"
            )

        elif any(
            word in input_lower for word in ["improve", "fix", "quality", "clean"]
        ):
            words = user_input.split()
            for word in words:
                if "." in word or any(
                    word.endswith(ext) for ext in [".py", ".js", ".java"]
                ):
                    return self._improve_command(f"improve {word}")
            return "🤖 I understand you want improvements. Please specify: improve <filename>"

        elif any(
            word in input_lower
            for word in ["find", "discover", "what work", "opportunities"]
        ):
            return self._find_work_command("find work")

        elif any(word in input_lower for word in ["status", "how are", "what is"]):
            return self._show_status()

        else:
            return f"🤖 I didn't understand: '{user_input}'\n\nTry:\n• 'help' for commands\n• 'find work' to discover opportunities\n• 'test <filename>' to generate tests\n• Natural language like 'I need tests for my api.py file'"

    def cleanup(self):
        """Cleanup workforce"""
        self.workforce.shutdown_workforce()


async def interactive_session():
    """Run interactive AI commander session"""

    commander = AICommander()

    try:
        commander.start_interactive_session()

        while True:
            try:
                user_input = input("🤖 AI> ").strip()

                if user_input.lower() in ["quit", "exit", "bye"]:
                    print("👋 Goodbye! Your agents continue working in the background.")
                    break

                if not user_input:
                    continue

                response = commander.process_command(user_input)
                print(response)
                print()

            except KeyboardInterrupt:
                print("\n👋 Goodbye! Your agents continue working in the background.")
                break
            except EOFError:
                break

    finally:
        # In production, we wouldn't shut down - agents keep working
        print("🛑 Shutting down for demo...")
        commander.cleanup()


if __name__ == "__main__":
    asyncio.run(interactive_session())
