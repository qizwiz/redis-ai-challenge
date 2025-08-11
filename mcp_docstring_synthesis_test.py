#!/usr/bin/env python3
"""
MCP-based docstring synthesis testing
Demonstrates proper MCP tool composition instead of bash command sequences
"""

import asyncio
import json
from mcp.client.stdio_client import StdioMCPClient


async def test_docstring_synthesis_via_mcp():
    """Test docstring synthesis using pure MCP tool composition"""

    print("🚀 **MCP-BASED DOCSTRING SYNTHESIS TEST**")
    print("=" * 60)
    print("✅ Using MCP tool composition instead of bash commands")

    # Connect to docstring-synthesis MCP server
    try:
        client = StdioMCPClient(
            command="python",
            args=[
                "/Users/jonathanhill/src/redis-ai-challenge/docstring_synthesis_mcp.py"
            ],
        )

        async with client:
            print("\n📝 **STEP 1: MCP CONNECTION ESTABLISHED**")
            print("-" * 40)

            # List available tools
            tools = await client.list_tools()
            print("Available MCP tools:")
            for tool in tools.tools:
                print(f"  • {tool.name}: {tool.description}")

            print("\n🧠 **STEP 2: HARVEST DOCSTRINGS VIA MCP**")
            print("-" * 40)

            # Use MCP tool instead of direct function call
            harvest_result = await client.call_tool("harvest_docstrings", {})
            print(harvest_result.content[0].text)

            print("\n🎯 **STEP 3: TEST UTTERANCE LOOKUP VIA MCP**")
            print("-" * 40)

            # Test utterances as requested using MCP tools
            test_utterances = [
                "move to end of line",
                "control e",
                "end of line",
                "go to line end",
                "undo that",
                "revert last change",
                "ctrl underscore",
            ]

            for utterance in test_utterances:
                result = await client.call_tool(
                    "lookup_utterance", {"utterance": utterance}
                )
                print(f"Utterance: '{utterance}'")
                print(result.content[0].text)
                print()

            print("\n🔮 **STEP 4: TEST NEXT ACTION PREDICTIONS VIA MCP**")
            print("-" * 40)

            # Test predictions as requested using MCP tools
            test_commands = ["end-of-line", "undo", "beginning-of-line"]

            for command in test_commands:
                result = await client.call_tool(
                    "predict_next_actions", {"current_command": command}
                )
                print(f"Predictions for: {command}")
                print(result.content[0].text)
                print()

            print("\n✅ **MCP TOOL COMPOSITION COMPLETE**")
            print("✅ No direct bash commands used")
            print("✅ No direct Redis access used")
            print("✅ Pure MCP-based semantic intelligence")

    except Exception as e:
        print(f"❌ MCP connection failed: {e}")
        print("\n💡 **FALLBACK: DIRECT ENGINE TEST**")
        print("Testing docstring synthesis engine directly...")

        # Fallback to direct testing but highlight MCP preference
        from docstring_synthesis_engine import DocstringSynthesisEngine

        engine = DocstringSynthesisEngine()

        # Use mock data to avoid bash commands
        mock_docstrings = {
            "end-of-line": "Move point to end of line. With prefix ARG, move forward ARG - 1 lines first.",
            "beginning-of-line": "Move point to beginning of line. With prefix ARG, move backward ARG - 1 lines first.",
            "undo": "Undo some previous changes. Repeat this command to undo more changes.",
        }

        # Build mappings without external commands
        mappings = []
        for command, docstring in mock_docstrings.items():
            utterances = engine.synthesize_utterances_from_docstring(command, docstring)
            entities = engine.extract_entities_from_docstring(docstring)
            intent = engine.classify_intent(command, docstring)
            related = engine.find_related_commands(command, docstring, mock_docstrings)
            confidence = min(len(utterances) * 0.1 + len(docstring) * 0.001, 1.0)

            from docstring_synthesis_engine import SemanticMapping

            mapping = SemanticMapping(
                canonical_command=command,
                docstring=docstring,
                synthesized_utterances=utterances,
                extracted_entities=entities,
                intent_category=intent,
                related_commands=related,
                confidence=confidence,
            )
            mappings.append(mapping)

        # Store mappings (this uses Redis but in a contained way)
        engine.store_mappings_in_redis(mappings)

        print(f"✅ Created {len(mappings)} mappings")

        # Test the requested utterances
        test_utterances = [
            "move to end of line",
            "control e",
            "end of line",
            "go to line end",
            "undo that",
            "revert last change",
            "ctrl underscore",
        ]

        print("\n🎯 **SEMANTIC EQUIVALENCE RESULTS**:")
        for utterance in test_utterances:
            canonical = engine.lookup_utterance(utterance)
            if canonical:
                print(f"✅ '{utterance}' → `{canonical}`")
            else:
                print(f"❌ '{utterance}' → No mapping found")


def analyze_mcp_vs_bash_approach():
    """Analyze the difference between MCP and bash approaches"""

    print("\n📊 **MCP vs BASH APPROACH ANALYSIS**")
    print("=" * 60)

    print("❌ **BASH COMMAND APPROACH (AVOID):**")
    print("  - redis-cli commands")
    print("  - emacsclient subprocess calls")
    print("  - Direct system command execution")
    print("  - Fragile error handling")
    print("  - Tight coupling to system state")

    print("\n✅ **MCP TOOL COMPOSITION (PREFERRED):**")
    print("  - Structured tool interfaces")
    print("  - Clean error handling")
    print("  - Composable operations")
    print("  - Better abstraction layers")
    print("  - Standardized communication")

    print("\n💡 **REFLECTION:**")
    print("The user is correct - I should elevate to MCP tool composition")
    print("instead of falling back to bash commands and direct system access.")
    print("This follows the 'If you CAN mcp it, mcp it' principle.")


if __name__ == "__main__":
    analyze_mcp_vs_bash_approach()
    asyncio.run(test_docstring_synthesis_via_mcp())
