#!/usr/bin/env python3
"""
Simplified AI Learner - Real AI analysis with shorter prompts
"""

import requests
import json
import time


class SimplifiedAILearner:
    """AI learner with simplified, faster prompts"""

    def __init__(self):
        self.ai_client = self._setup_ollama()
        self.learned_commands = {}
        self.learned_concepts = {}

    def learn_from_tutorial(self, tutorial_text):
        """Learn from tutorial with simplified AI analysis"""

        if not self.ai_client:
            print("⚠️  No AI available, using basic parsing")
            return self._basic_parse(tutorial_text)

        # Much simpler prompt
        prompt = f"""Extract Emacs commands from this text. Return JSON:

TEXT: {tutorial_text[:200]}...

Return:
{{"commands": [{{"name": "C-f", "purpose": "what it does"}}]}}"""

        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": self.ai_client["model"],
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")

                # Extract JSON
                if "```json" in content:
                    json_content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_content = content.split("```")[1].split("```")[0].strip()
                else:
                    json_content = content.strip()

                parsed = json.loads(json_content)

                # Store learned commands
                for cmd in parsed.get("commands", []):
                    self.learned_commands[cmd["name"]] = cmd

                print(f"🧠 AI learned {len(parsed.get('commands', []))} commands")
                return True

        except Exception as e:
            print(f"❌ AI analysis failed: {e}")

        return self._basic_parse(tutorial_text)

    def respond_to_question(self, question):
        """Generate response to question"""

        if not self.ai_client:
            return self._basic_response(question)

        # Simple prompt for faster response
        prompt = f"""You learned these Emacs commands: {list(self.learned_commands.keys())}

Question: {question}

Answer briefly:"""

        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": self.ai_client["model"],
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=45,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get(
                    "content", "I need to think more about this."
                )

        except Exception as e:
            print(f"❌ Response generation failed: {e}")

        return self._basic_response(question)


def main():
    """Test the simplified AI learner"""

    print("🚀 SIMPLIFIED AI LEARNER TEST")
    print("=" * 40)

    learner = SimplifiedAILearner()

    # Simple tutorial text
    tutorial = """
    Use the commands C-p, C-b, C-f, and C-n to move around.
    C-p moves to previous line, C-n moves to next line.
    C-b moves backward, C-f moves forward.
    """

    print("📚 Learning from tutorial...")
    success = learner.learn_from_tutorial(tutorial)

    if success:
        print(f"✅ Learned commands: {list(learner.learned_commands.keys())}")

        # Test understanding
        print("\n🧪 Testing understanding...")
        question = "How do I move forward?"
        response = learner.respond_to_question(question)
        print(f"❓ {question}")
        print(f"🤖 {response}")

        print("\n🎯 AI LEARNING SUCCESSFUL!")
    else:
        print("❌ Learning failed")


if __name__ == "__main__":
    main()
