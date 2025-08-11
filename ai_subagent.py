#!/usr/bin/env python3
"""
AI Subagent - Use the learning AI through Claude's Task tool
"""

import json
import sys
from genuine_ai_learning import RealLearner
import subprocess


class AISubagent:
    """Subagent that can be called through Claude's Task tool"""

    def __init__(self):
        self.learner = RealLearner()
        self.emacs_available = self._check_emacs()

    def execute_command(self, command: str) -> dict:
        """Execute a command and return structured result"""
        result = self.learner.attempt_command(command)

        response = {
            "success": result["execution"]["outcome"] == "success",
            "command": command,
            "intent": result["analysis"]["intent"],
            "confidence": result["adjusted_confidence"],
            "method": result["analysis"]["method"],
            "key_binding": result["execution"].get("key_used"),
            "learning": (
                result["learning"]["insight"] if result["learning"]["learned"] else None
            ),
            "emacs_available": self.emacs_available,
            "knowledge_count": len(self.learner.knowledge),
        }

        # Try real execution
        if response["success"] and self.emacs_available and response["key_binding"]:
            try:
                key_binding = response["key_binding"]
                if key_binding.startswith("M-x"):
                    cmd = key_binding.replace("M-x ", "")
                    elisp = f'(call-interactively (intern "{cmd}"))'
                else:
                    elisp = f'(call-interactively (key-binding "{key_binding}"))'

                exec_result = subprocess.run(
                    ["emacsclient", "--eval", elisp],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                response["executed_in_emacs"] = exec_result.returncode == 0
                response["emacs_output"] = (
                    exec_result.stdout
                    if exec_result.returncode == 0
                    else exec_result.stderr
                )

            except Exception as e:
                response["executed_in_emacs"] = False
                response["emacs_error"] = str(e)

        return response

    def get_knowledge(self) -> dict:
        """Get current AI knowledge"""
        return {
            "patterns_learned": len(self.learner.knowledge),
            "knowledge_base": self.learner.knowledge,
            "confidence_stats": self.learner.confidence_adjustments,
            "total_experiences": self.learner.memory.redis_client.xlen(
                "ai_experiences"
            ),
            "emacs_available": self.emacs_available,
        }

    def teach_pattern(self, command: str, key_binding: str, intent: str) -> dict:
        """Teach the AI a specific pattern"""
        pattern_key = f"{intent}:{command.lower()}"
        self.learner.knowledge[pattern_key] = {
            "key_binding": key_binding,
            "action": f"execute_{intent}",
            "times_successful": 1,
            "manually_taught": True,
        }

        return {
            "taught": True,
            "pattern": pattern_key,
            "mapping": f"{command} → {key_binding}",
            "total_patterns": len(self.learner.knowledge),
        }


def main():
    """Handle subagent commands"""
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "error": "No command provided",
                    "usage": {
                        "execute": "python ai_subagent.py execute 'move cursor forward'",
                        "knowledge": "python ai_subagent.py knowledge",
                        "teach": "python ai_subagent.py teach 'go left' 'C-b' navigation",
                    },
                }
            )
        )
        return

    agent = AISubagent()
    action = sys.argv[1]

    if action == "execute":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "No command provided"}))
            return
        command = " ".join(sys.argv[2:])
        result = agent.execute_command(command)
        print(json.dumps(result, indent=2))

    elif action == "knowledge":
        knowledge = agent.get_knowledge()
        print(json.dumps(knowledge, indent=2))

    elif action == "teach":
        if len(sys.argv) < 5:
            print(json.dumps({"error": "Usage: teach 'command' 'key_binding' intent"}))
            return
        command = sys.argv[2]
        key_binding = sys.argv[3]
        intent = sys.argv[4]
        result = agent.teach_pattern(command, key_binding, intent)
        print(json.dumps(result, indent=2))

    elif action == "status":
        status = {
            "ai_ready": True,
            "emacs_available": agent.emacs_available,
            "knowledge_patterns": len(agent.learner.knowledge),
            "total_experiences": agent.learner.memory.redis_client.xlen(
                "ai_experiences"
            ),
        }
        print(json.dumps(status, indent=2))

    else:
        print(json.dumps({"error": f"Unknown action: {action}"}))


if __name__ == "__main__":
    main()
