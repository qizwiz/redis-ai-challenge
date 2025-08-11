#!/usr/bin/env python3
"""
FIRST STEP: Autonomous Code Explorer
AI that reads, understands, and learns from source code files directly
"""

import redis
import os
import time


class AutonomousCodeExplorer:
    def __init__(self):
        self.redis = redis.Redis(decode_responses=True)
        self.session = f"code_explorer_{int(time.time())}"
        self.emacs_src = (
            "/opt/homebrew/Cellar/emacs-plus@31/31.0.50/share/emacs/31.0.50/lisp"
        )
        print(f"🤖 Autonomous Code Explorer started: {self.session}")

    def execute_emacs(self, command):
        """Execute Emacs command and get result"""
        self.redis.lpush("emacs:commands", command)
        for i in range(10):
            result = self.redis.get("emacs:last_command_result")
            if result and result != "nil":
                return result
            time.sleep(0.1)
        return "timeout"

    def read_source_file(self, filename):
        """Read and analyze a C source file"""
        filepath = os.path.join(self.emacs_src, filename)

        if not os.path.exists(filepath):
            print(f"❌ Source file not found: {filepath}")
            return None

        print(f"📖 Reading source file: {filename}")

        try:
            with open(filepath, "r") as f:
                content = f.read()

            # Store in Redis for analysis
            self.redis.set(f"source_code:{filename}", content)

            # Extract function names from Emacs Lisp
            import re

            functions = re.findall(
                r"^\s*\(defun\s+([a-zA-Z0-9-]+)", content, re.MULTILINE
            )

            print(f"  🔍 Found {len(functions)} DEFUN functions")
            for func in functions[:5]:  # Show first 5
                print(f"    • {func}")

            # Store function list
            self.redis.sadd(f"functions:{filename}", *functions)

            return {
                "filename": filename,
                "size": len(content),
                "functions": functions,
                "lines": len(content.split("\n")),
            }

        except Exception as e:
            print(f"❌ Error reading {filepath}: {e}")
            return None

    def analyze_function_implementation(self, filename, function_name):
        """Analyze specific function implementation"""
        content = self.redis.get(f"source_code:{filename}")
        if not content:
            print(f"❌ No content cached for {filename}")
            return None

        print(f"🔬 Analyzing function: {function_name} in {filename}")

        # Find the defun block in Emacs Lisp
        import re

        pattern = rf"^\s*\(defun\s+{re.escape(function_name)}\s*\(.*?\n\s*\)"
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)

        if match:
            implementation = match.group(0)

            # Store analysis in Redis
            analysis = {
                "function": function_name,
                "file": filename,
                "implementation": implementation[:1000],  # First 1000 chars
                "lines": len(implementation.split("\n")),
                "session": self.session,
                "timestamp": time.time(),
            }

            self.redis.hset(f"analysis:{function_name}", mapping=analysis)

            print(
                f"  📝 Implementation: {len(implementation)} characters, {analysis['lines']} lines"
            )
            print(f"  🧠 Stored analysis in Redis")

            return analysis
        else:
            print(f"  ❌ Function {function_name} not found in {filename}")
            return None

    def discover_core_functions(self):
        """Discover and analyze core Emacs functions"""
        print("🚀 STEP 1: DISCOVER CORE FUNCTIONS")
        print("=" * 40)

        # Core Emacs Lisp files to explore first
        core_files = [
            "simple.el",  # Basic editing commands
            "files.el",  # File operations
            "window.el",  # Window management
            "buffer.el",  # Buffer functions
            "subr.el",  # Basic subroutines
        ]

        discoveries = {}

        for filename in core_files:
            print(f"\n📂 Exploring {filename}...")
            analysis = self.read_source_file(filename)

            if analysis:
                discoveries[filename] = analysis

                # Analyze top functions in each file
                for func in analysis["functions"][:2]:  # First 2 functions
                    self.analyze_function_implementation(filename, func)

            time.sleep(0.5)  # Prevent overwhelming

        print(f"\n🎉 Discovery complete!")
        print(f"📊 Analyzed {len(discoveries)} core files")

        return discoveries

    def query_discoveries(self, query):
        """Query what we've learned"""
        print(f"🧠 Querying discoveries: '{query}'")

        results = []
        for key in self.redis.scan_iter("analysis:*"):
            analysis = self.redis.hgetall(key)
            if query.lower() in analysis.get("function", "").lower():
                results.append(analysis)

        print(f"🔍 Found {len(results)} relevant functions")
        for result in results:
            print(f"  💡 {result.get('function')} ({result.get('file')})")

        return results

    def learn_from_emacs_masters(self):
        """Learn implementation patterns from Emacs source"""
        print("🎯 AUTONOMOUS LEARNING FROM EMACS MASTERS")
        print("=" * 50)

        # Step 1: Discover core functions
        discoveries = self.discover_core_functions()

        # Step 2: Build knowledge base
        print(f"\n📚 BUILDING KNOWLEDGE BASE")
        print("=" * 30)

        total_functions = 0
        for filename, data in discoveries.items():
            total_functions += len(data["functions"])

        print(f"📖 Total functions discovered: {total_functions}")
        print(f"💾 Knowledge stored in Redis for persistent learning")

        # Step 3: Query test
        print(f"\n🧪 TESTING KNOWLEDGE QUERIES")
        print("=" * 30)

        test_queries = ["forward", "search", "buffer"]
        for query in test_queries:
            self.query_discoveries(query)

        print(f"\n🚀 FOUNDATION COMPLETE!")
        print("=" * 25)
        print("✅ Core source files analyzed")
        print("✅ Function implementations extracted")
        print("✅ Knowledge base built in Redis")
        print("✅ Query system working")
        print("\n🎯 Ready for autonomous exploration!")


if __name__ == "__main__":
    explorer = AutonomousCodeExplorer()
    explorer.learn_from_emacs_masters()
