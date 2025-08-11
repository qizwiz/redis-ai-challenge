#!/usr/bin/env python3
"""
Hybrid MCP Agent - Monkeypatch to handle both reactive calls AND autonomous behavior
"""

import threading
import time
import redis
import json
from typing import Dict, Any
import fastmcp


class HybridMCPAgent:
    """
    Monkeypatch MCP servers to run autonomous background threads
    while still handling reactive stdio calls
    """

    def __init__(self, server_name: str):
        self.server_name = server_name
        self.redis_client = redis.Redis(decode_responses=True)
        self.autonomous_thread = None
        self.running = False
        self.state = {}

        # Patch the FastMCP server
        self.mcp = fastmcp.FastMCP(server_name)
        self._patch_run_method()

    def start_autonomous_behavior(self):
        """Start autonomous background processing"""
        if self.autonomous_thread is None or not self.autonomous_thread.is_alive():
            self.running = True
            self.autonomous_thread = threading.Thread(
                target=self._autonomous_loop, daemon=True
            )
            self.autonomous_thread.start()
            print(f"🤖 {self.server_name}: Started autonomous behavior")

    def stop_autonomous_behavior(self):
        """Stop autonomous background processing"""
        self.running = False
        if self.autonomous_thread:
            self.autonomous_thread.join(timeout=1.0)
        print(f"🛑 {self.server_name}: Stopped autonomous behavior")

    def _check_redis_events(self):
        """Check for relevant Redis events - override in subclasses"""
        pass

    def _autonomous_task(self):
        """Perform autonomous tasks - override in subclasses"""
        pass

    def get_state(self) -> Dict[str, Any]:
        """Get current agent state"""
        return {
            "server_name": self.server_name,
            "running": self.running,
            "thread_alive": (
                self.autonomous_thread.is_alive() if self.autonomous_thread else False
            ),
            "state": self.state,
        }


class AutonomousWorkflowAgent(HybridMCPAgent):
    """Workflow learning agent with autonomous pattern monitoring"""

    def __init__(self):
        super().__init__("autonomous-workflow")
        self.patterns_discovered = 0
        self.last_event_id = "0"

    def _autonomous_task(self):
        """Autonomously discover workflow patterns"""
        # Check for new workflow events
        try:
            events = self.redis_client.xread(
                {"workflow:events": self.last_event_id},
                count=10,
                block=100,  # 100ms timeout
            )

            if events:
                for stream, messages in events:
                    for message_id, fields in messages:
                        self._process_workflow_event(message_id, fields)
                        self.last_event_id = message_id

        except Exception as e:
            pass  # Timeout is normal

    def _process_workflow_event(self, message_id: str, fields: Dict[str, str]):
        """Process workflow event autonomously"""
        event_type = fields.get("event_type", "")

        if event_type == "buffer_switch":
            # Autonomous learning: detect common buffer patterns
            context = json.loads(fields.get("context", "{}"))
            buffer = context.get("buffer", "")

            if buffer.endswith(".py"):
                # Predict user might want to run Python
                self._proactive_suggestion(
                    f"Python file detected: {buffer}. Consider running/testing?"
                )
            elif buffer == "*scratch*":
                # Predict user might want to experiment
                self._proactive_suggestion(
                    "Scratch buffer active. Experiment mode detected."
                )

        self.patterns_discovered += 1
        self.state["patterns_discovered"] = self.patterns_discovered


class AutonomousContextAgent(HybridMCPAgent):
    """Context manager with autonomous memory consolidation"""

    def __init__(self):
        super().__init__("autonomous-context")
        self.context_entries = 0


# Example of how to use hybrid agents
def create_hybrid_workflow_agent():
    """Create a hybrid workflow agent"""
    agent = AutonomousWorkflowAgent()

    # Add standard MCP tools
    @agent.mcp.tool()
    def get_workflow_status() -> str:
        """Get current workflow analysis status"""
        state = agent.get_state()
        return f"🔄 Autonomous Workflow Agent\\n\\nPatterns discovered: {state['state'].get('patterns_discovered', 0)}\\nRunning: {state['running']}"

    @agent.mcp.tool()
    def record_workflow_event(event_type: str, context: dict) -> str:
        """Record workflow event (reactive call)"""
        # This bridges reactive MCP calls to the autonomous system
        event_data = {
            "timestamp": str(time.time()),
            "event_type": event_type,
            "context": json.dumps(context),
            "session_id": "mcp_session",
            "sequence_id": str(int(time.time())),
        }

        agent.redis_client.xadd("workflow:events", event_data)
        return f"✅ Event recorded: {event_type}"

    return agent


def create_hybrid_context_agent():
    """Create a hybrid context agent"""
    agent = AutonomousContextAgent()

    @agent.mcp.tool()
    def get_context_status() -> str:
        """Get current context analysis status"""
        state = agent.get_state()
        return f"🧠 Autonomous Context Agent\\n\\nContext entries: {state['state'].get('context_entries', 0)}\\nRunning: {state['running']}"

    return agent


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "context":
        # Run as context agent
        agent = create_hybrid_context_agent()
        print("🧠 Starting Hybrid Context Agent")
    else:
        # Run as workflow agent
        agent = create_hybrid_workflow_agent()
        print("🔄 Starting Hybrid Workflow Agent")

    # This will start both autonomous behavior AND MCP stdio handling
    agent.mcp.run()
