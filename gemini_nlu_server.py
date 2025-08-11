#!/usr/bin/env python3
"""
Gemini NLU Server - The Brain of the Operation

This script runs as an MCP server, exposing Gemini's native NLU capabilities
to other local processes, like the autonomous AI performer.
"""

import asyncio
import json
import logging
import re  # Import re module

from mcp.server import InitializationOptions, NotificationOptions, Server
from mcp import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsResult,
    Tool,
    TextContent,
)

from robust_claude_integration import claude_integration  # Import Claude integration

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class GeminiNLUServer:
    def __init__(self):
        self.server = Server("gemini-nlu-server")
        logging.info("Gemini NLU Server: Initializing tools...")
        self.setup_tools()
        logging.info("Gemini NLU Server: Tools initialized.")

    def setup_tools(self):
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            logging.info("Gemini NLU Server: handle_list_tools called.")
            return ListToolsResult(
                tools=[
                    Tool(
                        name="parse_instruction",
                        description="Parses a natural language instruction from the Emacs tutorial into a structured JSON object.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "instruction_text": {
                                    "type": "string",
                                    "description": "The line of text from the tutorial to be parsed.",
                                }
                            },
                            "required": ["instruction_text"],
                        },
                    )
                ]
            )

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
            if name == "parse_instruction":
                instruction = arguments.get("instruction_text", "")
                logging.info(
                    f"Gemini NLU Server: parse_instruction called with: {instruction}"
                )

                # Attempt to use Claude for NLU
                if claude_integration.is_available():
                    try:
                        prompt = f"""
You are an expert Emacs user and a parsing specialist. Your task is to read the following Emacs tutorial instruction and convert it into a structured JSON object.

For this step, provide the following fields:
- "step_number": An integer (placeholder, client will fill this).
- "instruction_text": The exact, complete instruction from the tutorial.
- "keystrokes": A list of the precise keystrokes to be executed. For example, ["C-f"], ["C-x", "C-s"], ["M-x", "auto-fill-mode"].
- "expected_behavior": A clear and concise description of what should happen when the keystrokes are executed.
- "section": The name of the tutorial section the instruction belongs to (placeholder, client will fill this).
- "is_exercise": A boolean that is true if the instruction is a hands-on exercise (usually marked with ">>").

Here is the tutorial instruction:

{instruction}
"""
                        response = claude_integration.execute_prompt(prompt, timeout=15)
                        if response.success:
                            parsed_data = json.loads(response.content)
                            logging.info("Gemini NLU Server: Parsed with Claude NLU.")
                            return CallToolResult(
                                content=[
                                    TextContent(
                                        type="text", text=json.dumps(parsed_data)
                                    )
                                ]
                            )
                        else:
                            logging.warning(
                                f"Gemini NLU Server: Claude NLU failed: {response.error_message}. Falling back to mock."
                            )
                    except Exception as e:
                        logging.error(
                            f"Gemini NLU Server: Error with Claude NLU: {e}. Falling back to mock."
                        )

                # Fallback to mock NLU
                parsed_data = self.mock_gemini_nlu(instruction)
                logging.info("Gemini NLU Server: Parsed with mock NLU.")
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(parsed_data))]
                )
            else:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps({"error": f"Unknown tool: {name}"}),
                        )
                    ]
                )

    def mock_gemini_nlu(self, instruction: str) -> dict:
        # A sophisticated mock that simulates real NLU.
        # It uses regex as a fallback, similar to how a real model might use patterns.
        keystrokes = []
        expected_behavior = ""
        is_exercise = instruction.startswith(">>")

        # Extract keystrokes
        # This regex is more robust than the previous one.
        keystroke_patterns = re.findall(
            r"([CM]-\S+|\b[a-zA-Z0-9]+(?:\s+[a-zA-Z0-9]+)*\b(?=\s*<Return>)|<[a-zA-Z]+>)",
            instruction,
        )
        if keystroke_patterns:
            keystrokes = [k.strip() for k in keystroke_patterns]

        # A simple heuristic for expected behavior
        # Corrected regex: removed 's* and added proper escaping
        parts = re.split(
            r"\s*([CM]-\S+|\b[a-zA-Z0-9]+(?:\s+[a-zA-Z0-9]+)*\b(?=\s*<Return>)|<[a-zA-Z]+>)\s*",
            instruction,
        )
        if len(parts) > 1:
            # The split will include the matched delimiters, so we need to filter them out
            # and join the remaining parts.
            expected_behavior = "".join(
                [p for p in parts if p not in keystrokes and p.strip() != ""]
            ).strip()
        else:
            expected_behavior = "Execute the command."

        return {
            "step_number": 0,  # The client will fill this in
            "instruction_text": instruction,
            "keystrokes": keystrokes,
            "expected_behavior": expected_behavior,
            "section": "Unknown",  # The client can manage this
            "is_exercise": is_exercise,
        }

    async def run(self):
        logging.info("Gemini NLU Server: Entering stdio_server context...")
        async with stdio_server() as (read_stream, write_stream):
            logging.info(
                "Gemini NLU Server: stdio_server context entered. Running server..."
            )
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="gemini-nlu-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
            logging.info("Gemini NLU Server: self.server.run completed.")


async def main():
    nlu_server = GeminiNLUServer()
    await nlu_server.run()


if __name__ == "__main__":
    asyncio.run(main())
