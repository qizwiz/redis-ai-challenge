#!/usr/bin/env python3
"""
Intelligent Prompt Responder - AI responses to Emacs prompts via Redis
"""
import redis
import time
import re


class PromptResponder:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)

    def start_responding(self):
        """Start monitoring and responding to prompts"""
        print("🤖 AI Prompt Responder started")
        print("Monitoring Redis for Emacs prompts...")

        while True:
            try:
                prompt = self.redis_client.get("emacs:current-prompt")
                if prompt and prompt.strip():
                    response = self.generate_response(prompt)
                    if response:
                        self.redis_client.set("emacs:prompt-response", response)
                        print(f"📥 Prompt: {prompt[:50]}...")
                        print(f"📤 Response: {response}")
                        # Clear the prompt so we don't respond repeatedly
                        self.redis_client.delete("emacs:current-prompt")

                time.sleep(0.5)

            except KeyboardInterrupt:
                print("\n⏹️ Prompt responder stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(1)

    def generate_response(self, prompt):
        """Generate intelligent response based on prompt content"""
        prompt_lower = prompt.lower().strip()

        # Tutorial-related prompts
        if "tutorial" in prompt_lower or "help" in prompt_lower:
            if "kill" in prompt_lower or "delete" in prompt_lower:
                return "yes"
            if "save" in prompt_lower:
                return "no"
            if "continue" in prompt_lower:
                return "yes"

        # File operations
        if "save" in prompt_lower:
            return "no"  # Don't save tutorial changes

        if "kill" in prompt_lower or "delete" in prompt_lower:
            return "yes"  # OK to kill buffers

        # Yes/no questions - default to yes for demos
        if prompt_lower.endswith("? ") or "y/n" in prompt_lower:
            return "yes"

        # Single character responses
        if len(prompt_lower) < 10:
            return "y"

        # Default responses
        if "file" in prompt_lower:
            return ""  # Empty for file prompts

        return "yes"  # Conservative default


if __name__ == "__main__":
    responder = PromptResponder()
    responder.start_responding()
