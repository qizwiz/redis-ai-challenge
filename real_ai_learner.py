#!/usr/bin/env python3
"""
Real AI Learner - Genuine AI learning using Azure OpenAI + Redis coordination
No templates, no theater - actual AI understanding and response generation
"""

import os
import json
import time
import asyncio
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from redis_ai_patterns import HomoiconicRedis, SemanticExtractor
from redis_emacs_bridge import RedisEmacsBridge


@dataclass
class LearningMemory:
    """Dynamic learning memory built through AI analysis"""

    concepts_understood: Dict[str, Any] = field(default_factory=dict)
    command_knowledge: Dict[str, Any] = field(default_factory=dict)
    patterns_discovered: List[str] = field(default_factory=list)
    hypotheses_tested: List[Dict[str, Any]] = field(default_factory=list)
    confidence_levels: Dict[str, float] = field(default_factory=dict)


class RealAILearner:
    """AI learner using actual Azure OpenAI for genuine understanding"""

    def __init__(self):
        # Set up AI client
        self.ai_client = self._setup_ollama()

        # Redis coordination
        self.memory = HomoiconicRedis(namespace="real_ai_learner")
        self.emacs_bridge = RedisEmacsBridge(session_id="real_ai_demo")

        # Learning state
        self.learning_memory = LearningMemory()
        self.session_id = f"learning_{int(time.time())}"

        # Gather real environmental knowledge
        self.environment_context = self._gather_environment_context()

        print("🧠 Real AI Learner initialized with Ollama!")
        print(f"🌍 Environment context: {len(self.environment_context)} data points")

    def _setup_ollama(self) -> Dict[str, Any]:
        """Set up Ollama client"""

        ollama_base_url = "http://localhost:11434"

        try:
            # Test if Ollama is running
            response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)

            if response.status_code == 200:
                models = response.json().get("models", [])

                if models:
                    # Prefer llama3.1:latest if available, otherwise use first model
                    model_names = [m["name"] for m in models]
                    if "llama3.1:latest" in model_names:
                        model_name = "llama3.1:latest"
                    else:
                        model_name = model_names[0]
                    print(f"✅ Connected to Ollama with model: {model_name}")
                    return {
                        "base_url": ollama_base_url,
                        "model": model_name,
                        "available": True,
                    }
                else:
                    print("⚠️  Ollama running but no models found")
                    return None
            else:
                print("⚠️  Ollama not responding")
                return None

        except Exception as e:
            print(f"⚠️  Failed to connect to Ollama: {e}")
            print("   Make sure Ollama is running: ollama serve")
            return None

    def _gather_environment_context(self) -> Dict[str, Any]:
        """Gather real environmental knowledge about the system"""

        import subprocess
        import platform
        import os

        context = {}

        # Operating System
        context["os"] = {
            "system": platform.system(),
            "version": platform.version(),
            "machine": platform.machine(),
            "platform": platform.platform(),
        }

        # Emacs information
        try:
            # Get Emacs version
            emacs_version = subprocess.run(
                ["emacs", "--version"], capture_output=True, text=True, timeout=5
            )
            if emacs_version.returncode == 0:
                context["emacs"] = {
                    "version_info": emacs_version.stdout.split("\n")[0],
                    "available": True,
                }
            else:
                context["emacs"] = {"available": False}
        except:
            context["emacs"] = {
                "available": False,
                "error": "Not found or not responding",
            }

        # Check for Spacemacs
        spacemacs_dir = os.path.expanduser("~/.spacemacs.d")
        spacemacs_file = os.path.expanduser("~/.spacemacs")
        context["spacemacs"] = {
            "config_dir_exists": os.path.exists(spacemacs_dir),
            "config_file_exists": os.path.exists(spacemacs_file),
            "detected": os.path.exists(spacemacs_dir) or os.path.exists(spacemacs_file),
        }

        # Package directories (common locations)
        package_dirs = [
            "~/.emacs.d/elpa",
            "~/.emacs.d/straight",
            "~/.emacs.d/packages",
            "/usr/share/emacs",
            "/usr/local/share/emacs",
        ]

        context["packages"] = {}
        for pkg_dir in package_dirs:
            expanded_dir = os.path.expanduser(pkg_dir)
            if os.path.exists(expanded_dir):
                try:
                    contents = os.listdir(expanded_dir)
                    context["packages"][pkg_dir] = {
                        "exists": True,
                        "count": len(contents),
                        "sample_contents": contents[:10],  # First 10 items
                    }
                except:
                    context["packages"][pkg_dir] = {"exists": True, "readable": False}
            else:
                context["packages"][pkg_dir] = {"exists": False}

        # Documentation locations
        doc_locations = [
            "/usr/share/info",
            "/usr/local/share/info",
            "~/.emacs.d/doc",
            "/Applications/Emacs.app/Contents/Resources/info",  # macOS
        ]

        context["documentation"] = {}
        for doc_loc in doc_locations:
            expanded_loc = os.path.expanduser(doc_loc)
            if os.path.exists(expanded_loc):
                try:
                    info_files = [
                        f for f in os.listdir(expanded_loc) if f.endswith(".info")
                    ]
                    context["documentation"][doc_loc] = {
                        "exists": True,
                        "info_files": len(info_files),
                        "sample_files": info_files[:5],
                    }
                except:
                    context["documentation"][doc_loc] = {
                        "exists": True,
                        "readable": False,
                    }
            else:
                context["documentation"][doc_loc] = {"exists": False}

        # System libraries
        try:
            # Check for development tools
            which_gcc = subprocess.run(["which", "gcc"], capture_output=True, text=True)
            which_make = subprocess.run(
                ["which", "make"], capture_output=True, text=True
            )

            context["development"] = {
                "gcc_available": which_gcc.returncode == 0,
                "make_available": which_make.returncode == 0,
                "can_compile": which_gcc.returncode == 0 and which_make.returncode == 0,
            }
        except:
            context["development"] = {"detection_failed": True}

        # Environment variables relevant to Emacs
        emacs_env_vars = ["EDITOR", "EMACS", "EMACSDATA", "EMACSDOC", "EMACSLOADPATH"]
        context["environment_vars"] = {}
        for var in emacs_env_vars:
            value = os.getenv(var)
            context["environment_vars"][var] = value if value else "not_set"

        return context

    def learn_from_tutorial_section(self, tutorial_text: str) -> None:
        """Learn from tutorial text using real AI analysis"""

        print("🧠 Analyzing tutorial with real AI...")

        # Use AI to understand the tutorial content
        understanding = self._ai_analyze_tutorial(tutorial_text)

        if understanding:
            # Store learned concepts
            for concept in understanding.get("concepts", []):
                self.learning_memory.concepts_understood[concept["name"]] = concept

            # Store command knowledge
            for command in understanding.get("commands", []):
                self.learning_memory.command_knowledge[command["name"]] = command

            # Store discovered patterns
            self.learning_memory.patterns_discovered.extend(
                understanding.get("patterns", [])
            )

            # Save to Redis
            self.memory.store_code(
                f"learning_session_{self.session_id}",
                {
                    "concepts": self.learning_memory.concepts_understood,
                    "commands": self.learning_memory.command_knowledge,
                    "patterns": self.learning_memory.patterns_discovered,
                    "timestamp": time.time(),
                },
            )

            print(
                f"📚 Learned {len(understanding.get('concepts', []))} concepts and {len(understanding.get('commands', []))} commands"
            )
        else:
            print("⚠️  Failed to analyze tutorial - using basic parsing")
            self._fallback_analysis(tutorial_text)

    def _ai_analyze_tutorial(self, tutorial_text: str) -> Optional[Dict[str, Any]]:
        """Use Ollama to analyze tutorial content"""

        if not self.ai_client or not self.ai_client.get("available"):
            return None

        analysis_prompt = f"""You are an AI learning Emacs on this specific system. Analyze this tutorial section with full environmental context.

SYSTEM ENVIRONMENT:
{json.dumps(self.environment_context, indent=2)}

TUTORIAL TEXT:
{tutorial_text}

Given your environment context, analyze:
1. Key concepts being taught (with definitions)
2. Commands mentioned (with purposes relevant to this system)
3. Underlying patterns or principles 
4. Learning objectives
5. How this relates to the detected Emacs configuration

Consider:
- Your OS: {self.environment_context.get('os', {}).get('system', 'unknown')}
- Emacs availability: {self.environment_context.get('emacs', {}).get('available', False)}
- Spacemacs detected: {self.environment_context.get('spacemacs', {}).get('detected', False)}
- Available packages: {len([k for k, v in self.environment_context.get('packages', {}).items() if v.get('exists')])} directories found

Return as JSON:
{{
    "concepts": [{{"name": "concept_name", "definition": "what it means", "importance": "why it matters", "system_relevance": "how it applies to this environment"}}],
    "commands": [{{"name": "C-f", "purpose": "what it does", "rationale": "why it works this way", "availability": "confirmed/likely/unknown on this system"}}],
    "patterns": ["pattern descriptions considering this environment"],
    "learning_objectives": ["what student should understand given this setup"],
    "environment_notes": ["observations about how tutorial relates to detected system"]
}}"""

        try:
            # Call Ollama API using chat endpoint
            response = requests.post(
                f"{self.ai_client['base_url']}/api/chat",
                json={
                    "model": self.ai_client["model"],
                    "messages": [{"role": "user", "content": analysis_prompt}],
                    "stream": False,
                },
                timeout=120,
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")

                # Try to parse JSON response
                if "```json" in content:
                    json_content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_content = content.split("```")[1].split("```")[0].strip()
                else:
                    json_content = content.strip()

                return json.loads(json_content)
            else:
                print(f"❌ Ollama API error: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            return None

    def respond_to_question(self, question: str) -> str:
        """Generate response using real AI understanding"""

        print(f"🤔 Thinking about: {question}")

        if self.ai_client:
            return self._ai_generate_response(question)
        else:
            return self._fallback_response(question)

    def _ai_generate_response(self, question: str) -> str:
        """Generate response using Ollama"""

        # Build context from learned knowledge
        context = {
            "concepts_learned": list(self.learning_memory.concepts_understood.keys()),
            "commands_known": list(self.learning_memory.command_knowledge.keys()),
            "patterns_discovered": self.learning_memory.patterns_discovered,
            "detailed_knowledge": {
                "concepts": self.learning_memory.concepts_understood,
                "commands": self.learning_memory.command_knowledge,
            },
        }

        response_prompt = f"""You are an AI learning Emacs on a specific system. Answer this question using your learned knowledge and environmental context.

SYSTEM ENVIRONMENT:
{json.dumps(self.environment_context, indent=2)}

YOUR LEARNED KNOWLEDGE:
{json.dumps(context, indent=2)}

QUESTION: {question}

Rules:
1. Use your learned knowledge AND environmental context
2. Consider how your specific system setup affects the answer
3. Show reasoning process considering both knowledge and environment
4. Admit uncertainty and distinguish knowledge vs. inference
5. Reference specific system capabilities when relevant

Your OS: {self.environment_context.get('os', {}).get('system', 'unknown')}
Emacs available: {self.environment_context.get('emacs', {}).get('available', False)}
Spacemacs: {self.environment_context.get('spacemacs', {}).get('detected', False)}

Respond as an AI learning on THIS specific system."""

        try:
            # Call Ollama API using chat endpoint
            response = requests.post(
                f"{self.ai_client['base_url']}/api/chat",
                json={
                    "model": self.ai_client["model"],
                    "messages": [{"role": "user", "content": response_prompt}],
                    "stream": False,
                },
                timeout=120,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get(
                    "content", "I need to think more about this."
                )
            else:
                print(f"❌ Ollama API error: {response.status_code}")
                return self._fallback_response(question)

        except Exception as e:
            print(f"❌ AI response generation failed: {e}")
            return self._fallback_response(question)

    def test_understanding(self, test_question: str) -> Dict[str, Any]:
        """Test understanding and return analysis"""

        response = self.respond_to_question(test_question)

        # Analyze response quality
        analysis = {
            "question": test_question,
            "response": response,
            "timestamp": time.time(),
            "knowledge_used": [],
            "reasoning_shown": "because" in response.lower()
            or "since" in response.lower(),
            "confidence": 0.7,  # Basic assessment
        }

        # Track what knowledge was referenced
        for concept in self.learning_memory.concepts_understood:
            if concept.lower() in response.lower():
                analysis["knowledge_used"].append(concept)

        for command in self.learning_memory.command_knowledge:
            if command.lower() in response.lower():
                analysis["knowledge_used"].append(command)

        # Store test result
        self.learning_memory.hypotheses_tested.append(analysis)

        return analysis

    def demonstrate_understanding(self) -> Dict[str, Any]:
        """Show current understanding state"""

        return {
            "concepts_learned": len(self.learning_memory.concepts_understood),
            "commands_understood": len(self.learning_memory.command_knowledge),
            "patterns_discovered": len(self.learning_memory.patterns_discovered),
            "tests_taken": len(self.learning_memory.hypotheses_tested),
            "session_id": self.session_id,
            "using_real_ai": self.ai_client is not None,
            "knowledge_summary": {
                "concepts": list(self.learning_memory.concepts_understood.keys()),
                "commands": list(self.learning_memory.command_knowledge.keys()),
            },
        }


def main():
    """Test the real AI learner"""

    print("🚀 Testing Real AI Learner")
    print("=" * 40)

    learner = RealAILearner()

    # Learn from tutorial
    tutorial_text = """
    Moving from screenful to screenful is useful, but how do you
    move to a specific place within the text on the screen?

    There are several ways you can do this. You can use the arrow keys,
    but it's more efficient to keep your hands in the standard position
    and use the commands C-p, C-b, C-f, and C-n. These characters
    are equivalent to the four arrow keys, like this:

                      Previous line, C-p
                          :
                          :
       Backward, C-b .... Current cursor position .... Forward, C-f
                          :
                          :
                        Next line, C-n

    You'll find it easy to remember these letters by words they stand for:
    P for previous, N for next, B for backward and F for forward.
    """

    learner.learn_from_tutorial_section(tutorial_text)

    # Test understanding with a genuinely novel question
    print("\n🧪 Testing Understanding...")

    # Ask something that wasn't programmed
    test_question = "If I'm at the beginning of a line and want to get to the middle, what would you do?"
    print(f"\n❓ Novel question: {test_question}")
    response = learner.respond_to_question(test_question)
    print(f"🤖 {response}")

    # Show what was actually learned vs what's needed
    print(f"\n🔍 Raw Analysis Results:")
    print(
        f"   Commands found: {list(learner.learning_memory.command_knowledge.keys())}"
    )
    print(
        f"   Concepts learned: {list(learner.learning_memory.concepts_understood.keys())}"
    )
    print(f"   AI available: {learner.ai_client is not None}")

    if not learner.ai_client:
        print("   💡 Install a working Ollama model to see real AI learning!")

    # Show final state
    print("\n📊 Final Understanding State:")
    state = learner.demonstrate_understanding()
    for key, value in state.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    main()
