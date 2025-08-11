#!/usr/bin/env python3
"""
STEP 3A: Autonomous Tool Builder - First Step
AI analyzes learned patterns and generates NEW working code
"""

import redis
import re
import time


class AutonomousToolBuilder:
    def __init__(self):
        self.redis = redis.Redis(decode_responses=True)
        self.session = f"builder_{int(time.time())}"
        print(f"🔨 Autonomous Tool Builder started: {self.session}")

    def execute_emacs(self, command):
        """Execute Emacs command and test the built code"""
        self.redis.lpush("emacs:commands", command)
        for i in range(10):
            result = self.redis.get("emacs:last_command_result")
            if result and result != "nil":
                return result
            time.sleep(0.1)
        return "timeout"

    def analyze_learned_patterns(self):
        """Extract buildable patterns from understood code"""
        print("🔍 ANALYZING LEARNED PATTERNS")
        print("=" * 35)

        patterns = {
            "cursor_movement": [],
            "text_insertion": [],
            "buffer_operations": [],
            "interactive_commands": [],
        }

        # Analyze all understood functions
        for key in self.redis.scan_iter("understanding:*"):
            data = self.redis.hgetall(key)
            function_name = data.get("function", "")
            behaviors = eval(data.get("behaviors", "{}"))

            # Categorize by buildable patterns
            if behaviors.get("moves_cursor"):
                patterns["cursor_movement"].append(function_name)
            if behaviors.get("modifies_text"):
                patterns["text_insertion"].append(function_name)
            if behaviors.get("creates_buffer"):
                patterns["buffer_operations"].append(function_name)
            if behaviors.get("interactive"):
                patterns["interactive_commands"].append(function_name)

        print(f"📊 Pattern Analysis Results:")
        for pattern_type, functions in patterns.items():
            print(f"  🎯 {pattern_type}: {len(functions)} functions")
            for func in functions[:2]:  # Show examples
                print(f"    • {func}")

        return patterns

    def extract_implementation_template(self, function_name):
        """Extract the core template from a function implementation"""
        # Get the stored analysis
        analysis = self.redis.hgetall(f"analysis:{function_name}")
        if not analysis:
            return None

        implementation = analysis.get("implementation", "")
        if not implementation:
            return None

        # Extract key structural elements
        lines = implementation.split("\n")
        template_elements = {
            "defun_signature": "",
            "docstring": "",
            "interactive_spec": "",
            "core_logic": [],
            "error_handling": [],
            "return_value": "",
        }

        # Parse the function structure
        in_docstring = False
        docstring_complete = False

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Get function signature
            if (
                line_stripped.startswith("(defun")
                and not template_elements["defun_signature"]
            ):
                template_elements["defun_signature"] = line_stripped

            # Extract docstring
            elif line_stripped.startswith('"') and not docstring_complete:
                if line_stripped.endswith('"') and len(line_stripped) > 1:
                    template_elements["docstring"] = line_stripped
                    docstring_complete = True
                else:
                    in_docstring = True
                    template_elements["docstring"] = line_stripped
            elif in_docstring:
                template_elements["docstring"] += " " + line_stripped
                if line_stripped.endswith('"'):
                    in_docstring = False
                    docstring_complete = True

            # Extract interactive spec
            elif "(interactive" in line_stripped:
                template_elements["interactive_spec"] = line_stripped

            # Extract core logic (skip comments and blank lines)
            elif (
                line_stripped
                and not line_stripped.startswith(";")
                and docstring_complete
            ):
                if "condition-case" in line_stripped or "error" in line_stripped:
                    template_elements["error_handling"].append(line_stripped)
                else:
                    template_elements["core_logic"].append(line_stripped)

        return template_elements

    def synthesize_new_function(self, purpose, pattern_type):
        """Synthesize a NEW function based on learned patterns"""
        print(f"🧬 SYNTHESIZING: {purpose}")
        print(f"   Pattern Type: {pattern_type}")

        # Get example implementations to learn from
        patterns = self.analyze_learned_patterns()
        example_functions = patterns.get(pattern_type, [])

        if not example_functions:
            print("  ❌ No examples found for this pattern type")
            return None

        print(f"  📚 Learning from {len(example_functions)} example functions")

        # Extract templates from examples
        templates = []
        for func_name in example_functions[:3]:  # Use top 3 examples
            template = self.extract_implementation_template(func_name)
            if template:
                templates.append(template)

        if not templates:
            print("  ❌ Could not extract templates")
            return None

        # Synthesize new function based on patterns
        new_function = self.generate_function_from_templates(purpose, templates)

        return new_function

    def generate_function_from_templates(self, purpose, templates):
        """Generate new function code from learned templates"""

        # Create function name from purpose
        func_name = purpose.lower().replace(" ", "-").replace("_", "-")

        # Build the function
        generated_code = f"""(defun {func_name} ()
  "AI-generated function: {purpose}
Built by learning from Emacs master implementations."
  (interactive)
  """

        # Add common patterns found in templates
        common_patterns = []
        for template in templates:
            for logic_line in template.get("core_logic", [])[:3]:  # Take first 3 lines
                if any(
                    keyword in logic_line
                    for keyword in ["let", "save-excursion", "when", "if"]
                ):
                    common_patterns.append(logic_line)

        # Add the most common patterns
        if common_patterns:
            generated_code += f"  ;; Pattern learned from master implementations\n"
            generated_code += f"  {common_patterns[0]}\n"

        # Add purpose-specific logic
        if "cursor" in purpose.lower():
            generated_code += "  (forward-char 1)\n"
            generated_code += '  (message "Cursor moved by AI-built function")\n'
        elif "text" in purpose.lower():
            generated_code += '  (insert "Text inserted by AI-built function")\n'
        elif "buffer" in purpose.lower():
            generated_code += '  (switch-to-buffer "*AI-Created-Buffer*")\n'
            generated_code += '  (message "Buffer created by AI")\n'
        else:
            generated_code += (
                '  (message "AI-generated function executed successfully")\n'
            )

        generated_code += "  )\n"

        return {
            "function_name": func_name,
            "code": generated_code,
            "purpose": purpose,
            "learned_from": [t.get("defun_signature", "") for t in templates],
            "generated_at": time.time(),
        }

    def test_generated_function(self, generated_function):
        """Test the AI-generated function in Emacs"""
        print(f"🧪 TESTING: {generated_function['function_name']}")

        # Install the function in Emacs
        install_cmd = generated_function["code"]
        result = self.execute_emacs(install_cmd)

        if "timeout" in result or "error" in result.lower():
            print("  ❌ Function installation failed")
            return False

        print("  ✅ Function installed successfully")

        # Test execution
        test_cmd = f"({generated_function['function_name']})"
        test_result = self.execute_emacs(test_cmd)

        if "timeout" in test_result or "error" in test_result.lower():
            print("  ❌ Function execution failed")
            print(f"     Error: {test_result}")
            return False

        print("  ✅ Function executed successfully!")
        print(f"     Result: {test_result}")

        # Store successful pattern
        self.redis.hset(
            f"generated_function:{generated_function['function_name']}",
            mapping={k: str(v) for k, v in generated_function.items()},
        )

        return True

    def build_first_autonomous_tool(self):
        """Build the very first autonomous tool"""
        print("🚀 BUILDING FIRST AUTONOMOUS TOOL")
        print("=" * 40)

        # Step 1: Analyze what we can build
        patterns = self.analyze_learned_patterns()

        # Step 2: Choose simplest buildable tool
        if patterns["cursor_movement"]:
            purpose = "smart cursor movement"
            pattern_type = "cursor_movement"
        elif patterns["text_insertion"]:
            purpose = "intelligent text insertion"
            pattern_type = "text_insertion"
        else:
            purpose = "basic utility function"
            pattern_type = "interactive_commands"

        # Step 3: Synthesize the function
        generated_function = self.synthesize_new_function(purpose, pattern_type)

        if not generated_function:
            print("❌ Failed to generate function")
            return False

        print(f"\n📝 GENERATED CODE:")
        print("=" * 20)
        print(generated_function["code"])
        print("=" * 20)

        # Step 4: Test it works
        success = self.test_generated_function(generated_function)

        if success:
            print(f"\n🎉 AUTONOMOUS TOOL BUILDING SUCCESS!")
            print("=" * 40)
            print("✅ AI learned from master implementations")
            print("✅ AI synthesized new working code")
            print("✅ AI tested and verified the function works")
            print("✅ AI stored the pattern for future use")
            print(f"\n🔨 Built: {generated_function['function_name']}")
            print(f"🎯 Purpose: {generated_function['purpose']}")

        return success


if __name__ == "__main__":
    builder = AutonomousToolBuilder()
    builder.build_first_autonomous_tool()
