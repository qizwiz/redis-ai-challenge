#!/usr/bin/env python3
"""
Intelligent AI Processor - Refactored with Provider Abstraction
This processor uses a provider model to allow for multiple AI backends (Claude, Gemini, etc.)
and to ensure robust fallback behavior.
"""

import asyncio
import json
import time
import logging
import re
from fixed_redis_coordinator import redis_coordinator
from robust_claude_integration import claude_integration

# --- Custom Debug Logging ---
# We will use a separate, clean log file for our debugging.
logging.basicConfig(
    filename="debug.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)

# --- AI Provider Abstraction ---


class AICompletionProvider:
    """Abstract base class for AI completion providers."""

    async def get_completion(self, line_content, word_before, major_mode):
        raise NotImplementedError


class ClaudeCompletionProvider(AICompletionProvider):
    """Provider for getting completions from Claude."""

    async def get_completion(self, line_content, word_before, major_mode):
        try:
            prompt = f"""You are an expert code completion AI.

Context:
- Language/mode: {major_mode}
- Current line: \"{line_content}\" 
- Object before dot: \"{word_before}\" 

Task: Suggest the most likely method/property that would come after the dot.
Respond with ONLY the method/property name, nothing else."""

            response = claude_integration.execute_prompt(prompt, timeout=8)

            if response.success and response.content.strip():
                suggestion = response.content.strip().split()[0]
                logging.info(f"🤖 Claude suggested: {suggestion}")
                return suggestion
            else:
                logging.warning(f"Claude completion failed: {response.error_message}")
                return None
        except Exception as e:
            logging.error(f"Claude completion error: {e}")
            return None


class GeminiCompletionProvider(AICompletionProvider):
    """Provider for getting completions from Gemini (Placeholder)."""

    async def get_completion(self, line_content, word_before, major_mode):
        logging.info("🤖 Using Gemini provider (placeholder)")
        await asyncio.sleep(0.1)  # Simulate network latency
        return "gemini_suggestion"


class FallbackCompletionProvider(AICompletionProvider):
    """Provider for reliable, hardcoded fallback completions."""

    async def get_completion(self, line_content, word_before, major_mode):
        logging.info("🤖 Using fallback provider")
        word_lower = word_before.lower() if word_before else ""
        contextual_completions = {
            "user": ["name", "email", "id"],
            "data": ["get", "set", "values"],
            "file": ["read", "write", "open"],
            "response": ["json", "text", "status"],
        }
        for key, completions in contextual_completions.items():
            if key in word_lower:
                return completions[0]
        return "name"


class SimpleTriggerCompletionProvider(AICompletionProvider):
    """Provider for our first new, verifiable feature."""

    async def get_completion(self, line_content, word_before, major_mode):
        if major_mode == "python-mode" and line_content.strip() == "def":
            logging.info("🤖 Triggered 'def' completion")
            return "function_name(self, arg1, arg2):"
        return None


# --- Provider Factory ---


def get_provider(provider_name="claude"):
    """Factory function to get an AI provider instance."""
    if provider_name == "claude":
        return ClaudeCompletionProvider()
    elif provider_name == "gemini":
        return GeminiCompletionProvider()
    elif provider_name == "simple_trigger":
        return SimpleTriggerCompletionProvider()
    else:
        return FallbackCompletionProvider()


# --- Refactored Intelligent AI Processor ---


class IntelligentAIProcessor:
    """AI processor using the provider model for completions."""

    def __init__(self, primary_provider_name="simple_trigger"):
        self.coordinator = redis_coordinator
        self.running = False
        self.responses_generated = 0
        self.primary_provider = get_provider(primary_provider_name)
        self.fallback_provider = FallbackCompletionProvider()
        self.start_time = time.time()
        logging.info(
            f"🧠 Intelligent AI Processor initialized with provider: {primary_provider_name}"
        )

    async def start_processing(self):
        """Start intelligent processing using the provider model."""
        self.running = True
        self.start_time = time.time()
        logging.info(
            f"🚀 Starting INTELLIGENT AI processor with provider: {self.primary_provider.__class__.__name__}"
        )

        while self.running:
            try:
                await self._process_completion_triggers()
                await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"Main loop error: {e}")
                await asyncio.sleep(2)

    def _decode_redis_value(self, value):
        """Safely decode a value from Redis, whether it's bytes or already a string."""
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return value

    async def _process_completion_triggers(self):
        """Process completion triggers using the provider model."""
        logging.info("--- Checking for completion triggers ---")
        try:
            entries = self.coordinator.redis.xrevrange("intents", count=1)
            if not entries:
                return

            entry_id_bytes, fields_bytes = entries[0]
            entry_id = self._decode_redis_value(entry_id_bytes)

            last_processed_id_bytes = self.coordinator.redis.get(
                "last_processed_intent_id"
            )
            last_processed_id = (
                self._decode_redis_value(last_processed_id_bytes)
                if last_processed_id_bytes
                else None
            )

            if entry_id == last_processed_id:
                return

            decoded_fields = {
                self._decode_redis_value(k): self._decode_redis_value(v)
                for k, v in fields_bytes.items()
            }

            if decoded_fields.get("type") == "completion_trigger":
                await self._handle_intelligent_completion(decoded_fields)
                self.coordinator.redis.set("last_processed_intent_id", entry_id)

        except Exception as e:
            logging.error(f"Completion processing error: {e}")

    async def _handle_intelligent_completion(self, fields):
        """Handle completion by trying the primary provider, then fallback."""
        line_content = fields.get("line_content", "")
        word_before = fields.get("word_before", "")
        major_mode = fields.get("major_mode", "")

        logging.info(f"--- Handling completion for: '{line_content}' ---")

        completion = await self.primary_provider.get_completion(
            line_content, word_before, major_mode
        )

        if not completion:
            main_provider = get_provider("claude")
            completion = await main_provider.get_completion(
                line_content, word_before, major_mode
            )

        if not completion:
            completion = await self.fallback_provider.get_completion(
                line_content, word_before, major_mode
            )

        if completion:
            logging.info(f"--- Sending command to Emacs: {completion} ---")
            response_data = {"action": "insert-text", "text": completion}
            self.coordinator.redis.xadd("emacs:commands", response_data)
            self.responses_generated += 1
            logging.info(f"✨ Sent command to Emacs: insert-text with '{completion}'")

    def stop(self):
        """Stop the intelligent processor."""
        self.running = False
        logging.info("🛑 Intelligent AI Processor stopped")


# --- Main Execution ---

intelligent_ai_processor = IntelligentAIProcessor(
    primary_provider_name="simple_trigger"
)


async def main():
    """Main function to run the processor."""
    print("🧠 REFACTORED INTELLIGENT AI PROCESSOR V5")
    print("=" * 60)

    processor_task = asyncio.create_task(intelligent_ai_processor.start_processing())

    print("✅ Intelligent AI processor started with the new provider model.")
    print("📝 Load working_emacs_redis.el in Emacs and run (working-redis-start).")
    print("🐍 In a Python buffer, type 'def ' to trigger the new completion.")
    print("🛑 Press Ctrl+C to stop.")

    try:
        await processor_task
    except KeyboardInterrupt:
        print("\n🛑 Stopping intelligent AI processor...")
        intelligent_ai_processor.stop()
        print("✅ Intelligent AI processor stopped")


if __name__ == "__main__":
    asyncio.run(main())
