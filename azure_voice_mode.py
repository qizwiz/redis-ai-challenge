#!/usr/bin/env python3
"""
Azure Speech Voice Mode for Claude Code
Uses Azure Speech Services instead of OpenAI Whisper
"""

import asyncio
import json
import os
import azure.cognitiveservices.speech as speechsdk
from typing import Any, Dict, List, Optional
from mcp.server import InitializationOptions, NotificationOptions, Server
from mcp import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)


class AzureVoiceMode:
    def __init__(self):
        # Azure Speech configuration
        self.speech_key = os.environ.get("SPEECH_KEY")
        self.service_region = os.environ.get("SPEECH_REGION", "eastus")

        if not self.speech_key:
            raise ValueError("SPEECH_KEY environment variable required")

        # Configure Azure Speech
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key, region=self.service_region
        )

        # Configure audio
        self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

        # Create speech recognizer
        self.speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config, audio_config=self.audio_config
        )

        # Configure TTS
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config
        )

    def listen_for_speech(self, timeout_seconds: int = 30) -> Optional[str]:
        """Listen for speech input using Azure Speech Services"""

        print("🎤 Listening with Azure Speech Services...")

        try:
            # Start continuous recognition
            result = self.speech_recognizer.recognize_once_async().get()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                print(f"📝 Recognized: {result.text}")
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                print("❌ No speech could be recognized")
                return None
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                print(f"❌ Speech recognition canceled: {cancellation_details.reason}")
                if cancellation_details.error_details:
                    print(f"Error details: {cancellation_details.error_details}")
                return None

        except Exception as e:
            print(f"💥 Speech recognition error: {e}")
            return None

    def speak_text(self, text: str) -> bool:
        """Convert text to speech using Azure Speech Services"""

        print(f"🔊 Speaking: {text[:50]}...")

        try:
            result = self.speech_synthesizer.speak_text_async(text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print("✅ Speech synthesis completed")
                return True
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                print(f"❌ Speech synthesis canceled: {cancellation_details.reason}")
                if cancellation_details.error_details:
                    print(f"Error details: {cancellation_details.error_details}")
                return False

        except Exception as e:
            print(f"💥 Speech synthesis error: {e}")
            return False

    def converse(self, initial_message: str = None) -> Dict[str, Any]:
        """Start a voice conversation"""

        if initial_message:
            print(f"💬 Initial message: {initial_message}")
            self.speak_text(initial_message)

        # Listen for user input
        user_speech = self.listen_for_speech()

        if user_speech:
            return {
                "success": True,
                "user_input": user_speech,
                "transcription_service": "Azure Speech Services",
            }
        else:
            return {"success": False, "error": "No speech recognized"}


# MCP Server Setup
server = Server("azure-voice-mode")
azure_voice = AzureVoiceMode()


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available voice tools"""
    return ListToolsResult(
        tools=[
            Tool(
                name="listen",
                description="Listen for speech input using Azure Speech Services",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "timeout": {
                            "type": "number",
                            "description": "Timeout in seconds (default: 30)",
                        }
                    },
                },
            ),
            Tool(
                name="speak",
                description="Convert text to speech using Azure Speech Services",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to convert to speech",
                        }
                    },
                    "required": ["text"],
                },
            ),
            Tool(
                name="converse",
                description="Start a voice conversation with Azure Speech Services",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "initial_message": {
                            "type": "string",
                            "description": "Optional initial message to speak",
                        }
                    },
                },
            ),
        ]
    )


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
    """Handle voice tool calls"""

    if name == "listen":
        timeout = arguments.get("timeout", 30)
        result = azure_voice.listen_for_speech(timeout)

        if result:
            return CallToolResult(
                content=[TextContent(type="text", text=f"🎤 Heard: {result}")]
            )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text="❌ No speech recognized")]
            )

    elif name == "speak":
        text = arguments.get("text", "")
        success = azure_voice.speak_text(text)

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"🔊 {'Spoke successfully' if success else 'Speech failed'}: {text[:50]}...",
                )
            ]
        )

    elif name == "converse":
        initial_message = arguments.get("initial_message")
        result = azure_voice.converse(initial_message)

        if result["success"]:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"💬 Voice conversation:\nUser said: {result['user_input']}\nUsing: {result['transcription_service']}",
                    )
                ]
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"❌ Conversation failed: {result['error']}"
                    )
                ]
            )

    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")]
        )


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="azure-voice-mode",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
