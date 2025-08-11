#!/usr/bin/env python3
"""
Proof of Concept: Autonomous AI Explorer
AI that learns by exploring Emacs packages and documenting discoveries
"""

import redis
import time
import json


class AutonomousExplorer:
    def __init__(self):
        self.redis = redis.Redis(decode_responses=True)
        self.session = f"explorer_{int(time.time())}"
        print(f"🤖 Autonomous Explorer started: {self.session}")

    def execute_emacs(self, command):
        """Execute Emacs command and get result"""
        self.redis.lpush("emacs:commands", command)
        for i in range(20):
            result = self.redis.get("emacs:last_command_result")
            if result and result != "nil":
                return result
            time.sleep(0.1)
        return "timeout"

    def explore_function(self, function_name):
        """Explore a function: get docs, source, experiment"""
        print(f"🔍 Exploring function: {function_name}")

        # Get documentation
        doc_cmd = f"(describe-function '{function_name})"
        self.execute_emacs(doc_cmd)

        # Get function definition location
        source_cmd = f"(symbol-file '{function_name} 'defun)"
        source_file = self.execute_emacs(source_cmd)

        # Try to get the actual source code
        if source_file and source_file != "nil":
            view_source_cmd = f"""(progn 
                                   (find-function \'{function_name})
                                   (buffer-substring-no-properties 
                                     (point) 
                                     (save-excursion (forward-sexp) (point))))"""
            source_code = self.execute_emacs(view_source_cmd)
        else:
            source_code = "Source not available"

        # Store discovery in Redis
        discovery = {
            "function": function_name,
            "source_file": source_file,
            "source_code": source_code[:500] if len(source_code) > 500 else source_code,
            "session": self.session,
            "timestamp": time.time(),
        }

        self.redis.hset(f"ai_discoveries:{function_name}", mapping=discovery)
        print(f"  📝 Documented: {function_name} from {source_file}")

        return discovery

    def discover_related_functions(self, base_function):
        """Find related functions by exploring source"""
        print(f"🕸️  Discovering functions related to: {base_function}")

        # Get all functions in same file
        related_cmd = f"""(progn
                           (find-function \'{base_function})
                           (let ((functions nil))
                             (save-excursion
                               (goto-char (point-min))
                               (while (re-search-forward "(defun \\\\([^ ]+\\\\)" nil t)
                                 (push (match-string 1) functions)))
                             functions))"""

        related_functions = self.execute_emacs(related_cmd)
        print(f"  🔗 Found related functions: {related_functions}")

        return related_functions

    def autonomous_exploration_session(self):
        """Run autonomous exploration of Emacs ecosystem"""
        print("🚀 AUTONOMOUS EXPLORATION SESSION")
        print("================================")

        # Start with basic functions and explore outward
        seed_functions = ["forward-char", "insert", "search-forward", "buffer-name"]

        explored = set()
        to_explore = seed_functions.copy()

        exploration_count = 0
        max_explorations = 10  # Limit for demo

        while to_explore and exploration_count < max_explorations:
            current_function = to_explore.pop(0)

            if current_function in explored:
                continue

            print(f"\n📍 Exploration #{exploration_count + 1}")

            # Explore the function
            discovery = self.explore_function(current_function)
            explored.add(current_function)
            exploration_count += 1

            # Find related functions to explore next
            related = self.discover_related_functions(current_function)
            if related and related != "nil":
                try:
                    # Parse the result (it's a Lisp list)
                    if isinstance(related, str) and "(" in related:
                        # Extract function names from Lisp list format
                        import re

                        new_functions = re.findall(r'"([^"]+)"', related)
                        for func in new_functions[:3]:  # Add up to 3 new functions
                            if func not in explored:
                                to_explore.append(func)
                                print(f"  ➕ Queued for exploration: {func}")
                except:
                    pass

            time.sleep(1)  # Prevent overwhelming

        print(f"\n🎉 Exploration session complete!")
        print(f"📊 Explored {len(explored)} functions")

        # Show what we learned
        print("\n📚 KNOWLEDGE ACQUIRED:")
        for func in explored:
            discovery_data = self.redis.hgetall(f"ai_discoveries:{func}")
            if discovery_data:
                print(f"  📖 {func}: {discovery_data.get('source_file', 'unknown')}")

        return explored

    def query_learned_knowledge(self, query):
        """Query what the AI has learned"""
        print(f"🧠 Querying learned knowledge: '{query}'")

        # Search through stored discoveries
        all_discoveries = []
        for key in self.redis.scan_iter("ai_discoveries:*"):
            discovery = self.redis.hgetall(key)
            if query.lower() in discovery.get("function", "").lower():
                all_discoveries.append(discovery)

        print(f"🔍 Found {len(all_discoveries)} relevant discoveries")
        for discovery in all_discoveries[:3]:  # Show top 3
            print(f"  💡 {discovery.get('function')}: {discovery.get('source_file')}")

        return all_discoveries


if __name__ == "__main__":
    explorer = AutonomousExplorer()

    print("🎯 PROOF OF CONCEPT: AI LEARNING BY EXPLORATION")
    print("=" * 50)

    # Run autonomous exploration
    learned_functions = explorer.autonomous_exploration_session()

    # Test knowledge querying
    print("\n" + "=" * 50)
    explorer.query_learned_knowledge("char")
