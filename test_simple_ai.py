#!/usr/bin/env python3
"""
Simple test of Ollama AI integration
"""

import requests
import json


def test_simple_ollama():
    """Test basic Ollama connectivity"""

    print("🤖 Testing Simple Ollama Integration")
    print("=" * 40)

    # Simple prompt
    simple_prompt = (
        "Hello! Please respond with just 'AI is working' if you can understand this."
    )

    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.1:latest",
                "messages": [{"role": "user", "content": simple_prompt}],
                "stream": False,
            },
            timeout=60,
        )

        if response.status_code == 200:
            result = response.json()
            content = result.get("message", {}).get("content", "")
            print(f"✅ AI Response: {content}")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_structured_prompt():
    """Test with a structured prompt similar to our real use case"""

    print("\n🧠 Testing Structured Analysis")
    print("=" * 40)

    structured_prompt = """Analyze this Emacs tutorial text and return JSON:

TUTORIAL: "Use C-f to move forward one character."

Return this JSON format:
{
  "commands": [{"name": "C-f", "purpose": "move forward one character"}],
  "concepts": [{"name": "character_navigation", "definition": "moving cursor by single characters"}]
}"""

    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.1:latest",
                "messages": [{"role": "user", "content": structured_prompt}],
                "stream": False,
            },
            timeout=60,
        )

        if response.status_code == 200:
            result = response.json()
            content = result.get("message", {}).get("content", "")
            print(f"✅ Raw AI Response:\n{content}")

            # Try to parse as JSON
            try:
                # Extract JSON from markdown code blocks
                if "```json" in content:
                    json_content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_content = content.split("```")[1].split("```")[0].strip()
                else:
                    json_content = content.strip()

                parsed = json.loads(json_content)
                print(f"✅ Parsed JSON: {json.dumps(parsed, indent=2)}")
                return True
            except json.JSONDecodeError as e:
                print(f"⚠️  Could not parse as JSON: {e}")
                return False

        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


if __name__ == "__main__":
    print("🔧 OLLAMA AI INTEGRATION TEST")
    print("=" * 50)

    # Test 1: Basic connectivity
    basic_works = test_simple_ollama()

    # Test 2: Structured analysis (like our real system uses)
    if basic_works:
        structured_works = test_structured_prompt()

        if structured_works:
            print("\n🎉 SUCCESS: AI integration is working!")
            print("✅ Basic responses work")
            print("✅ Structured analysis works")
            print("✅ JSON parsing works")
        else:
            print("\n⚠️  PARTIAL: Basic AI works, but structured analysis needs work")
    else:
        print("\n❌ FAILED: Basic AI connectivity broken")
