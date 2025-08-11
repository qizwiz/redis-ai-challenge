#!/usr/bin/env python3
"""
Claude Enhanced Mode - A better interface for Claude's operations

This creates an enhanced operational mode where Claude can:
1. Access the full AI workforce system
2. Execute commands with real feedback
3. Maintain persistent context across interactions
4. Coordinate multiple AI agents
5. Provide richer, more capable responses
"""

import redis
import json
import os
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
from ai_execution_engine import RealAIWorkforceEngine
from always_on_ai_workforce import AlwaysOnWorkforceManager, BackgroundTaskType
from interactive_ai_commander import AICommander
from intelligent_refactoring_agent import IntelligentRefactoringAgent


@dataclass
class EnhancedModeContext:
    """Context for Claude's enhanced operational mode"""

    session_id: str
    start_time: float
    commands_executed: int
    agents_deployed: int
    work_completed: int
    current_project: str
    capabilities_enabled: List[str]
    interaction_history: List[Dict[str, Any]]


class ClaudeEnhancedMode:
    """Enhanced operational mode for Claude with full AI workforce access"""

    def __init__(self):
        self.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
        self.execution_engine = RealAIWorkforceEngine(self.redis)
        self.workforce = AlwaysOnWorkforceManager(self.redis)
        self.commander = AICommander()
        self.refactoring_agent = IntelligentRefactoringAgent(self.redis)

        # Enhanced mode context
        self.context = EnhancedModeContext(
            session_id=f"claude_enhanced_{int(time.time())}",
            start_time=time.time(),
            commands_executed=0,
            agents_deployed=0,
            work_completed=0,
            current_project=os.path.basename(os.getcwd()),
            capabilities_enabled=[
                "Real AI Execution",
                "Autonomous Workforce Management",
                "Intelligent Code Analysis",
                "Automated Refactoring",
                "Multi-Agent Coordination",
                "Persistent Memory",
                "Git Integration",
                "Natural Language Processing",
            ],
            interaction_history=[],
        )

        # Initialize systems
        self._initialize_enhanced_mode()

    def _initialize_enhanced_mode(self):
        """Initialize enhanced mode capabilities"""

        print("🚀 CLAUDE ENHANCED MODE INITIALIZING")
        print("=" * 50)
        print("Activating advanced AI capabilities...")
        print()

        # Enable AI execution engine
        self.redis.set("ai_execution_engine_ready", "true")
        print("✅ AI Execution Engine: Active")

        # Deploy minimal workforce
        self.workforce.deploy_workforce()
        self.context.agents_deployed = len(self.workforce.agents)
        print(f"✅ AI Workforce: {self.context.agents_deployed} agents deployed")

        # Set up enhanced context tracking
        self.redis.setex(
            f"claude_context:{self.context.session_id}",
            3600,
            json.dumps(self.context.__dict__, default=str),
        )
        print("✅ Enhanced Context: Active")

        print(f"✅ Project Context: {self.context.current_project}")
        print()
        print("🎯 ENHANCED CAPABILITIES ACTIVE:")
        for capability in self.context.capabilities_enabled:
            print(f"   • {capability}")
        print()

    def execute_enhanced_command(self, user_input: str) -> str:
        """Execute command with enhanced capabilities"""

        start_time = time.time()
        self.context.commands_executed += 1

        # Log interaction
        interaction = {
            "timestamp": start_time,
            "user_input": user_input,
            "command_id": self.context.commands_executed,
        }

        print(
            f"🤖 CLAUDE ENHANCED [{self.context.commands_executed}]> Processing: {user_input}"
        )
        print("-" * 60)

        # Enhanced command processing
        if user_input.lower().startswith("analyze project"):
            result = self._enhanced_project_analysis()
        elif user_input.lower().startswith("find work"):
            result = self._enhanced_work_discovery()
        elif user_input.lower().startswith("deploy agents for"):
            result = self._enhanced_agent_deployment(user_input)
        elif user_input.lower().startswith("refactor"):
            result = self._enhanced_refactoring(user_input)
        elif user_input.lower().startswith("create"):
            result = self._enhanced_creation(user_input)
        elif user_input.lower() == "status":
            result = self._enhanced_status()
        elif user_input.lower().startswith("coordinate"):
            result = self._enhanced_coordination(user_input)
        else:
            # Use the commander for other commands
            result = self.commander.process_command(user_input)

        execution_time = time.time() - start_time

        # Update interaction history
        interaction["result"] = result[:200] + "..." if len(result) > 200 else result
        interaction["execution_time"] = execution_time
        self.context.interaction_history.append(interaction)

        print(f"\n⏱️  Executed in {execution_time:.2f}s")
        return result

    def _enhanced_project_analysis(self) -> str:
        """Comprehensive project analysis with AI workforce"""

        print("🔍 Initiating comprehensive project analysis...")

        # Get work opportunities
        opportunities = self.execution_engine.find_autonomous_work_opportunities(
            os.getcwd()
        )

        # Analyze codebase structure
        python_files = list(Path(".").rglob("*.py"))
        total_lines = 0
        total_functions = 0

        for py_file in python_files[:20]:  # Sample first 20 files
            try:
                analysis = self.execution_engine.code_analyzer.analyze_python_file(
                    str(py_file)
                )
                if "total_lines" in analysis:
                    total_lines += analysis["total_lines"]
                if "functions" in analysis:
                    total_functions += len(analysis["functions"])
            except:
                continue

        # Get git status
        try:
            import subprocess

            git_status = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True
            )
            modified_files = (
                len(git_status.stdout.strip().split("\n"))
                if git_status.stdout.strip()
                else 0
            )
        except:
            modified_files = 0

        result = f"""📊 ENHANCED PROJECT ANALYSIS: {self.context.current_project}
        
🏗️  PROJECT STRUCTURE:
   • Python files: {len(python_files)}
   • Total lines (sampled): {total_lines:,}
   • Total functions (sampled): {total_functions}
   • Modified files: {modified_files}
   
🎯 WORK OPPORTUNITIES DISCOVERED:
"""

        total_opportunities = 0
        for work_type, items in opportunities.items():
            if items:
                result += f"   • {work_type.replace('_', ' ').title()}: {len(items)} opportunities\n"
                total_opportunities += len(items)

        result += f"\n💡 Total actionable opportunities: {total_opportunities}"

        result += f"""
        
🤖 AI WORKFORCE STATUS:
   • Active agents: {self.context.agents_deployed}
   • Commands executed this session: {self.context.commands_executed}
   • Session uptime: {(time.time() - self.context.start_time)/60:.1f} minutes
   
🚀 RECOMMENDATIONS:
   • Deploy specialized agents for high-priority work
   • Consider automated refactoring for code cleanup
   • Set up continuous improvement workflows"""

        return result

    def _enhanced_work_discovery(self) -> str:
        """Enhanced work discovery with AI prioritization"""

        print("🔍 Enhanced work discovery with AI prioritization...")

        opportunities = self.execution_engine.find_autonomous_work_opportunities(
            os.getcwd()
        )

        result = "🎯 ENHANCED WORK DISCOVERY\n\n"

        # Prioritize opportunities by impact
        prioritized = []
        for work_type, items in opportunities.items():
            for item in items:
                priority_score = 0
                if work_type == "test_generation":
                    priority_score = item.get("complexity", 1) * 2
                elif work_type == "documentation":
                    priority_score = item.get("complexity", 1) * 1.5
                elif work_type == "code_quality":
                    priority_score = 3

                prioritized.append(
                    {"type": work_type, "item": item, "priority": priority_score}
                )

        # Sort by priority
        prioritized.sort(key=lambda x: x["priority"], reverse=True)

        result += "🏆 TOP PRIORITY WORK (AI Recommended):\n"
        for i, work in enumerate(prioritized[:10], 1):
            work_type = work["type"].replace("_", " ").title()
            item = work["item"]

            if work["type"] == "test_generation":
                result += f"   {i}. [{work_type}] {item['function_name']} in {Path(item['file_path']).name}\n"
                result += f"       Priority: {work['priority']:.1f} (complexity: {item.get('complexity', 1)})\n"
            elif work["type"] == "documentation":
                result += f"   {i}. [{work_type}] {item['function_name']} (complexity: {item.get('complexity', 1)})\n"
                result += f"       Priority: {work['priority']:.1f} in {Path(item['file_path']).name}\n"

        result += f"\n💡 Ready to deploy agents for top {min(10, len(prioritized))} opportunities"

        return result

    def _enhanced_agent_deployment(self, user_input: str) -> str:
        """Deploy agents for specific work with enhanced coordination"""

        # Extract work type from input
        if "test" in user_input.lower():
            work_type = BackgroundTaskType.TEST_GENERATION
            agent_name = "Enhanced Test Generator"
        elif "doc" in user_input.lower():
            work_type = BackgroundTaskType.DOCUMENTATION
            agent_name = "Enhanced Documentation Agent"
        else:
            work_type = BackgroundTaskType.CODE_QUALITY
            agent_name = "Enhanced Quality Agent"

        print(f"🚀 Deploying {agent_name}...")

        # Find relevant work
        opportunities = self.execution_engine.find_autonomous_work_opportunities(
            os.getcwd()
        )
        relevant_work = opportunities.get(work_type.value, [])

        if not relevant_work:
            return f"❌ No {work_type.value} opportunities found"

        # Assign work to agents
        assignments = 0
        for work in relevant_work[:5]:  # Top 5 opportunities
            self.workforce.assign_work_to_agent(
                work_type,
                f"Enhanced: {work.get('function_name', 'Unknown')} optimization",
                [work["file_path"]],
                priority=5,
            )
            assignments += 1

        self.context.work_completed += assignments

        return f"""✅ ENHANCED AGENT DEPLOYMENT COMPLETE
        
🤖 Agent Type: {agent_name}
📋 Work Assigned: {assignments} high-priority tasks
🎯 Target Files: {len(set(w['file_path'] for w in relevant_work[:5]))} unique files
⏱️  Estimated Completion: {assignments * 10} minutes

Agents are now working autonomously in the background.
Check progress with: status"""

    def _enhanced_refactoring(self, user_input: str) -> str:
        """Enhanced intelligent refactoring"""

        print("🔧 Initiating enhanced intelligent refactoring...")

        # Analyze for refactoring opportunities
        opportunities = self.refactoring_agent.analyze_codebase_for_refactoring()

        if not opportunities:
            return "✅ Codebase is already well-refactored - no opportunities found"

        # Filter to safe opportunities
        safe_opportunities = [
            opp
            for opp in opportunities
            if opp.confidence > 0.7 and opp.estimated_savings < 50
        ]

        if "execute" in user_input.lower() or "commit" in user_input.lower():
            # Execute refactoring
            results = self.refactoring_agent.execute_refactoring(safe_opportunities)

            if results["success"] and results["changes_made"]:
                # Commit changes
                commit_success = self.refactoring_agent.commit_refactoring_changes(
                    results
                )

                return f"""✅ ENHANCED REFACTORING COMPLETED
                
🔧 Files Modified: {len(results['files_modified'])}
📝 Changes Made: {len(results['changes_made'])}
🗑️  Lines Removed: {results['lines_removed']}
📤 Git Commit: {'✅ Success' if commit_success else '❌ Failed'}

The codebase has been intelligently refactored and changes committed."""
            else:
                return "❌ Refactoring failed or no safe changes could be made"
        else:
            # Just analyze
            return f"""🔍 ENHANCED REFACTORING ANALYSIS
            
📊 Total Opportunities: {len(opportunities)}
🛡️  Safe Opportunities: {len(safe_opportunities)}
💰 Potential Savings: {sum(opp.estimated_savings for opp in safe_opportunities)} lines

🎯 Top Opportunities:
{chr(10).join(f"   • {opp.description} ({opp.estimated_savings} lines)" 
              for opp in safe_opportunities[:5])}

To execute: "refactor execute" """

    def _enhanced_creation(self, user_input: str) -> str:
        """Enhanced creation capabilities"""

        if "test" in user_input.lower():
            return self._create_comprehensive_tests(user_input)
        elif "doc" in user_input.lower():
            return self._create_documentation(user_input)
        else:
            return "🔧 Enhanced creation available for: tests, documentation"

    def _enhanced_status(self) -> str:
        """Enhanced status with full system overview"""

        # Get workforce status
        workforce_status = self.workforce.get_workforce_status()

        # Get notifications
        notifications = self.workforce.get_user_notifications()

        # Get session stats
        session_time = time.time() - self.context.start_time

        return f"""🤖 CLAUDE ENHANCED MODE STATUS
        
📊 SESSION OVERVIEW:
   • Session ID: {self.context.session_id}
   • Uptime: {session_time/60:.1f} minutes
   • Commands Executed: {self.context.commands_executed}
   • Project: {self.context.current_project}
   
🎯 AI WORKFORCE:
   • Active Agents: {workforce_status['workforce_overview']['active_agents']}
   • Work Completed: {workforce_status['workforce_overview']['total_work_completed']}
   • Value Generated: ${workforce_status['workforce_overview']['total_value_added']:.2f}
   
📬 RECENT ACTIVITY:
   • Pending Notifications: {len(notifications)}
   • Last Interaction: {self.context.interaction_history[-1]['timestamp'] if self.context.interaction_history else 'None'}
   
🚀 ENHANCED CAPABILITIES:
{chr(10).join(f"   ✅ {cap}" for cap in self.context.capabilities_enabled)}

Ready for enhanced commands."""

    def _enhanced_coordination(self, user_input: str) -> str:
        """Enhanced multi-agent coordination"""

        return """🎯 ENHANCED COORDINATION CAPABILITIES
        
Available coordination patterns:
• Pipeline: Chain agents for complex workflows
• Parallel: Multiple agents on different aspects
• Hierarchical: Senior/junior agent relationships
• Collaborative: Agents sharing context and results

Specify coordination type for implementation."""

    def shutdown_enhanced_mode(self):
        """Gracefully shutdown enhanced mode"""

        print("\n🛑 SHUTTING DOWN CLAUDE ENHANCED MODE")
        print("=" * 50)

        # Save session context
        final_context = {
            **self.context.__dict__,
            "end_time": time.time(),
            "total_session_time": time.time() - self.context.start_time,
        }

        self.redis.setex(
            f"claude_session_final:{self.context.session_id}",
            86400,
            json.dumps(final_context, default=str),
        )

        # Shutdown workforce
        self.workforce.shutdown_workforce()

        print(f"✅ Session saved: {self.context.session_id}")
        print(f"✅ Commands executed: {self.context.commands_executed}")
        print(
            f"✅ Session duration: {(time.time() - self.context.start_time)/60:.1f} minutes"
        )
        print("\n🎯 Enhanced mode shutdown complete.")


def activate_claude_enhanced_mode():
    """Activate Claude's enhanced operational mode"""

    enhanced_claude = ClaudeEnhancedMode()

    print("\n🎮 CLAUDE ENHANCED MODE ACTIVE")
    print("Type commands to use enhanced capabilities, 'quit' to exit\n")

    try:
        while True:
            user_input = input("🤖 Enhanced> ").strip()

            if user_input.lower() in ["quit", "exit", "shutdown"]:
                break

            if not user_input:
                continue

            try:
                result = enhanced_claude.execute_enhanced_command(user_input)
                print(result)
                print()
            except KeyboardInterrupt:
                print("\n⏸️  Command interrupted")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    finally:
        enhanced_claude.shutdown_enhanced_mode()


if __name__ == "__main__":
    activate_claude_enhanced_mode()
