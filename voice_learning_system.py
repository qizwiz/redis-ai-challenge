#!/usr/bin/env python3
"""
Voice Learning System - Multi-model AI that learns from feedback
Uses: Local patterns → Ollama → Azure GPT-4.1 → Real execution
"""

import speech_recognition as sr
import pyttsx3
import subprocess
import json
import time
import requests
from typing import Dict, Any, Optional, List
from intelligent_dev_assistant import IntelligentDevAssistant
import redis
import os
from openai import AzureOpenAI


class VoiceLearningSystem:
    """Voice-controlled AI that learns from experience using multi-model approach"""

    def __init__(self):
        # Initialize components
        self.redis_client = redis.Redis(decode_responses=True)
        self.local_assistant = IntelligentDevAssistant()
        self.session_id = f"voice_learning_{int(time.time())}"

        # Voice components
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()

        # Azure OpenAI client
        self.azure_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )

        # Learning memory
        self.confidence_history = {}
        self.success_patterns = {}
        self.failure_corrections = {}

        # Check Emacs availability
        self.emacs_available = self._check_emacs()

        print("🎤 Voice Learning System initialized")
        self._calibrate_microphone()

    def speak(self, text: str):
        """Text-to-speech output"""
        print(f"🗣️  AI: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def listen(self) -> Optional[str]:
        """Speech-to-text input"""
        try:
            print("🎤 Listening...")
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=5)

            print("🧠 Processing speech...")
            # Use Google Speech Recognition (free)
            text = self.recognizer.recognize_google(audio)
            print(f"👤 You said: {text}")
            return text.lower().strip()

        except sr.WaitTimeoutError:
            print("⏰ No speech detected")
            return None
        except sr.UnknownValueError:
            print("❓ Could not understand speech")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            return None

    def process_command_hierarchy(self, command: str) -> Dict[str, Any]:
        """Process command through the model hierarchy"""

        print(f"🧠 Processing through model hierarchy: '{command}'")

        # Level 1: Local fast patterns (instant)
        start_time = time.time()
        local_result = self.local_assistant.process_user_intent(command)
        local_time = time.time() - start_time

        print(
            f"⚡ Local analysis: {local_result['intent']} (confidence: {local_result['confidence']:.2f}, {local_time:.4f}s)"
        )

        # Level 2: Ollama context reasoning (if confidence < 0.9)
        ollama_result = None
        if local_result["confidence"] < 0.9:
            ollama_result = self._ollama_reasoning(command, local_result)

        # Level 3: Azure GPT-4.1 learning (for complex cases or learning updates)
        learning_needed = (
            local_result["confidence"] < 0.8
            or command in self.failure_corrections
            or len(self.confidence_history.get(local_result["intent"], [])) > 3
        )

        azure_result = None
        if learning_needed:
            azure_result = self._azure_learning(command, local_result, ollama_result)

        return {
            "command": command,
            "local": local_result,
            "ollama": ollama_result,
            "azure": azure_result,
            "final_decision": self._make_final_decision(
                local_result, ollama_result, azure_result
            ),
        }

    def _ollama_reasoning(self, command: str, local_result: Dict) -> Optional[Dict]:
        """Use Ollama for contextual reasoning"""
        print("🤖 Consulting Ollama for context...")

        # Get current context
        context = {
            "current_file": self.local_assistant.context.current_file,
            "line": self.local_assistant.context.cursor_line,
            "recent_commands": getattr(
                self.local_assistant.context, "recent_commands", []
            )[-3:],
        }

        prompt = f"""
        Analyze this command in context:
        Command: "{command}"
        Local classification: {local_result['intent']} (confidence: {local_result['confidence']})
        Context: {json.dumps(context)}
        
        Provide JSON response:
        {{
            "refined_intent": "navigation/editing/file_ops/git_ops/debugging",
            "confidence_adjustment": 0.1,
            "reasoning": "why this makes sense in context",
            "key_binding": "suggested emacs command"
        }}
        """

        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "llama3.1:latest",
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=2,
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")

                # Extract JSON
                try:
                    if "{" in content and "}" in content:
                        start = content.find("{")
                        end = content.rfind("}") + 1
                        json_str = content[start:end]
                        ollama_analysis = json.loads(json_str)

                        print(
                            f"🤖 Ollama reasoning: {ollama_analysis.get('reasoning', 'N/A')}"
                        )
                        return ollama_analysis
                except json.JSONDecodeError:
                    print("⚠️  Ollama returned invalid JSON")

        except Exception as e:
            print(f"⚠️  Ollama timeout/error: {e}")

        return None

    def _azure_learning(
        self, command: str, local_result: Dict, ollama_result: Optional[Dict]
    ) -> Optional[Dict]:
        """Use Azure GPT-4.1 for learning and adaptation"""
        print("☁️  Consulting Azure GPT-4.1 for learning...")

        # Build learning context
        learning_context = {
            "command": command,
            "local_analysis": local_result,
            "ollama_analysis": ollama_result,
            "past_failures": self.failure_corrections.get(command, []),
            "confidence_history": self.confidence_history.get(
                local_result["intent"], []
            ),
            "session_patterns": self._get_session_patterns(),
        }

        prompt = f"""
        As an AI learning system, analyze this command and update learning patterns:
        
        Context: {json.dumps(learning_context, indent=2)}
        
        Tasks:
        1. Determine the best action for this specific command
        2. Update confidence based on historical patterns
        3. Identify learning opportunities
        4. Suggest pattern improvements
        
        Return JSON:
        {{
            "recommended_action": "specific key binding or command",
            "adjusted_confidence": 0.95,
            "learning_updates": ["pattern to strengthen", "pattern to weaken"],
            "reasoning": "detailed explanation of decision",
            "should_remember": true
        }}
        """

        try:
            response = self.azure_client.chat.completions.create(
                model="gpt-4",  # Adjust model name as needed
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )

            content = response.choices[0].message.content

            # Extract JSON from response
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                azure_analysis = json.loads(json_str)

                print(f"☁️  Azure learning: {azure_analysis.get('reasoning', 'N/A')}")
                return azure_analysis

        except Exception as e:
            print(f"⚠️  Azure error: {e}")

        return None

    def _make_final_decision(
        self, local: Dict, ollama: Optional[Dict], azure: Optional[Dict]
    ) -> Dict:
        """Make final decision based on all model inputs"""

        # Start with local decision
        decision = {
            "intent": local["intent"],
            "action": local["action"],
            "confidence": local["confidence"],
            "key_binding": None,
            "reasoning": "local pattern matching",
        }

        # Apply Ollama refinements
        if ollama:
            if ollama.get("confidence_adjustment"):
                decision["confidence"] = min(
                    0.95, decision["confidence"] + ollama["confidence_adjustment"]
                )
            if ollama.get("key_binding"):
                decision["key_binding"] = ollama["key_binding"]
            if ollama.get("refined_intent"):
                decision["intent"] = ollama["refined_intent"]
            decision["reasoning"] += f" + ollama context"

        # Apply Azure learning
        if azure:
            if azure.get("adjusted_confidence"):
                decision["confidence"] = azure["adjusted_confidence"]
            if azure.get("recommended_action"):
                decision["key_binding"] = azure["recommended_action"]
            decision["reasoning"] += f" + azure learning"

        # Map intent to key binding if not set
        if not decision["key_binding"]:
            decision["key_binding"] = self._intent_to_keybinding(
                decision["intent"], local.get("action")
            )

        return decision

    def execute_decision(self, decision: Dict) -> Dict[str, Any]:
        """Execute the final decision and get feedback"""

        key_binding = decision["key_binding"]
        if not key_binding:
            return {"success": False, "error": "No key binding determined"}

        print(f"⚡ Executing: {key_binding}")
        self.speak(f"Executing {key_binding}")

        if self.emacs_available:
            try:
                # Execute in real Emacs
                if key_binding.startswith("M-x"):
                    cmd = key_binding.replace("M-x ", "")
                    elisp = f'(call-interactively (intern "{cmd}"))'
                else:
                    elisp = f'(call-interactively (key-binding "{key_binding}"))'

                result = subprocess.run(
                    ["emacsclient", "--eval", elisp],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    self.speak("Command executed successfully")
                    return {"success": True, "output": result.stdout}
                else:
                    self.speak("Command failed")
                    return {"success": False, "error": result.stderr}

            except Exception as e:
                self.speak("Execution error")
                return {"success": False, "error": str(e)}
        else:
            # Simulate execution
            self.speak(f"Would execute {key_binding}")
            return {"success": True, "simulated": True}

    def learn_from_feedback(self, command: str, decision: Dict, execution_result: Dict):
        """Learn from execution results and user feedback"""

        # Record the experience
        experience = {
            "command": command,
            "decision": decision,
            "execution": execution_result,
            "timestamp": time.time(),
            "session": self.session_id,
        }

        # Store in Redis
        self.redis_client.xadd(
            "voice_learning:experiences", {"data": json.dumps(experience)}
        )

        # Update confidence tracking
        intent = decision["intent"]
        if intent not in self.confidence_history:
            self.confidence_history[intent] = []

        self.confidence_history[intent].append(
            {
                "confidence": decision["confidence"],
                "success": execution_result["success"],
                "timestamp": time.time(),
            }
        )

        # Ask for feedback
        self.speak("Was that correct?")
        feedback = self.listen()

        if feedback and ("no" in feedback or "wrong" in feedback):
            self.speak("What should I have done instead?")
            correction = self.listen()

            if correction:
                # Store correction
                if command not in self.failure_corrections:
                    self.failure_corrections[command] = []
                self.failure_corrections[command].append(
                    {
                        "attempted": decision["key_binding"],
                        "should_be": correction,
                        "timestamp": time.time(),
                    }
                )

                self.speak("Thank you, I'll remember that")
                print(
                    f"📚 Learned correction: '{command}' should be '{correction}' not '{decision['key_binding']}'"
                )

    def run_voice_session(self):
        """Run interactive voice learning session"""

        self.speak("Voice learning system ready. Say a command or 'quit' to exit.")

        if self.emacs_available:
            self.speak("Emacs is connected. I can execute real commands.")
        else:
            self.speak("Emacs not available. I'll show you what I would do.")

        while True:
            try:
                # Listen for command
                command = self.listen()

                if not command:
                    continue

                if "quit" in command or "exit" in command:
                    self.speak("Goodbye!")
                    break

                if "status" in command:
                    patterns_learned = len(self.failure_corrections)
                    self.speak(f"I have learned {patterns_learned} corrections so far")
                    continue

                # Process through model hierarchy
                result = self.process_command_hierarchy(command)

                # Execute the decision
                execution_result = self.execute_decision(result["final_decision"])

                # Learn from the result
                self.learn_from_feedback(
                    command, result["final_decision"], execution_result
                )

            except KeyboardInterrupt:
                self.speak("Voice session ended")
                break

        # Session summary
        total_experiences = self.redis_client.xlen("voice_learning:experiences")
        corrections_learned = len(self.failure_corrections)

        print(f"\n📊 Session Summary:")
        print(f"   Total experiences: {total_experiences}")
        print(f"   Corrections learned: {corrections_learned}")
        print(f"   Session ID: {self.session_id}")


def main():
    """Run the voice learning system"""

    # Check dependencies
    try:
        import speech_recognition
        import pyttsx3
    except ImportError:
        print("❌ Missing dependencies. Install with:")
        print("pip install SpeechRecognition pyttsx3 pyaudio")
        return

    if not os.getenv("AZURE_OPENAI_API_KEY"):
        print("❌ Set AZURE_OPENAI_API_KEY environment variable")
        return

    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        print("❌ Set AZURE_OPENAI_ENDPOINT environment variable")
        return

    # Initialize and run
    system = VoiceLearningSystem()
    system.run_voice_session()


if __name__ == "__main__":
    main()
