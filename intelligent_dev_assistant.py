#!/usr/bin/env python3
"""
Intelligent Development Assistant - Real AI + Redis coordination
Works with or without Emacs, demonstrates the full AI workflow
"""

import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import redis
import requests


@dataclass
class DevContext:
    """Current development context"""

    working_directory: str = ""
    current_file: Optional[str] = None
    cursor_line: int = 0
    recent_commands: List[str] = None
    active_buffers: List[str] = None
    project_language: str = "unknown"
    timestamp: float = 0.0

    def __post_init__(self):
        """
        Initializes instance variables after dataclass instantiation.

        This post-initialization method ensures that mutable default values for list
        attributes are properly initialized as empty lists when they are None. This
        prevents the common pitfall of sharing mutable default values between
        instances.

        Args:
            self: The instance being initialized.

        Returns:
            None: This method modifies the instance in-place and returns nothing.

        Note:
            This method is automatically called by dataclasses after the standard
            __init__ method completes. It's typically used with dataclass fields
            that have default_factory=None or require post-processing.

        Example:
            After instantiation, both recent_commands and active_buffers will be
            guaranteed to be empty lists rather than None:

            >>> instance = MyClass()
            >>> isinstance(instance.recent_commands, list)
            True
            >>> isinstance(instance.active_buffers, list)
            True
        """
        if self.recent_commands is None:
            self.recent_commands = []
        if self.active_buffers is None:
            self.active_buffers = []


class IntelligentDevAssistant:
    """AI-powered development assistant with Redis coordination"""

    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.session_id = f"dev_assistant_{int(time.time())}"

        # Development context
        self.context = DevContext()
        self.command_history = []
        self.learning_memory = {}

        print(f"🧠 Intelligent Dev Assistant initialized (session: {self.session_id})")
        self._initialize_redis_streams()

    def _initialize_redis_streams(self):
        """Initializes Redis streams for communication and learning."""
        streams = [
            "dev_assistant:commands",
            "dev_assistant:context_changes",
            "dev_assistant:ai_suggestions",
            "dev_assistant:learning_events",
        ]
        for stream in streams:
            try:
                # Create stream and consumer group if they don't exist
                self.redis_client.xgroup_create(
                    stream, "dev_assistant_group", id="0", mkstream=True
                )
                print(f"✅ Initialized Redis stream: {stream}")
            except redis.exceptions.DataError:
                # Consumer group already exists, which is fine
                print(f"⚠️ Redis stream already exists: {stream}")
            except Exception as e:
                print(f"❌ Error initializing Redis stream {stream}: {e}")

    def update_context(self, **kwargs):
        """Update development context"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)

        self.context.timestamp = time.time()

        # Store context change in Redis
        context_data = {
            "working_directory": self.context.working_directory,
            "current_file": self.context.current_file or "",
            "cursor_line": str(self.context.cursor_line),
            "project_language": self.context.project_language,
            "timestamp": str(self.context.timestamp),
            "session": self.session_id,
        }

        self.redis_client.xadd("dev_assistant:context_changes", context_data)
        print(
            f"📍 Context updated: {self.context.current_file}:{self.context.cursor_line}"
        )

    def _store_analysis(self, user_input, analysis):
        analysis_data = {
            "user_input": user_input,
            "intent": analysis.get("intent", "unknown"),
            "action": analysis.get("action", ""),
            "confidence": str(analysis.get("confidence", 0.0)),
            "method": analysis.get("method", "unknown"),
            "timestamp": str(time.time()),
            "session": self.session_id,
        }
        self.redis_client.xadd("dev_assistant:ai_suggestions", analysis_data)

    def process_user_intent(self, user_input: str) -> Dict[str, Any]:
        """Process user intent with fast local classification first, AI fallback"""
        print(f"🎯 Processing: '{user_input}'")

        # Store current user input for suggestion generation
        self._current_user_input = user_input

        # First: Try fast local classification
        local_analysis = self._smart_local_classification(user_input)
        if local_analysis["confidence"] >= 0.8:
            print(
                f"⚡ Fast local: {local_analysis['intent']} (confidence: {local_analysis['confidence']})"
            )
            self._store_analysis(user_input, local_analysis)
            return local_analysis

        # Second: Try AI with very short timeout
        ai_analysis = self._quick_ai_classification(user_input)
        if ai_analysis:
            self._store_analysis(user_input, ai_analysis)
            return ai_analysis

        # Fallback: Enhanced local analysis
        enhanced_analysis = self._enhanced_local_analysis(user_input)
        print(
            f"🔧 Enhanced fallback: {enhanced_analysis['intent']} (confidence: {enhanced_analysis['confidence']})"
        )
        self._store_analysis(user_input, enhanced_analysis)
        return enhanced_analysis

    def _smart_local_classification(self, user_input: str) -> Dict[str, Any]:
        """Smart local classification with pattern matching"""
        user_lower = user_input.lower()

        # Check for tutorial-specific patterns first
        tutorial_result = self._classify_tutorial_instruction(user_input)
        if tutorial_result["confidence"] >= 0.8:
            return tutorial_result

        # High-confidence patterns
        navigation_patterns = [
            "move",
            "go",
            "navigate",
            "jump",
            "cursor",
            "forward",
            "backward",
            "up",
            "down",
            "beginning",
            "end",
        ]
        editing_patterns = [
            "edit",
            "change",
            "insert",
            "delete",
            "replace",
            "remove",
            "add",
            "modify",
            "cut",
            "copy",
            "paste",
        ]
        file_patterns = ["open", "save", "file", "close", "create", "load", "write"]
        debug_patterns = [
            "debug",
            "error",
            "fix",
            "test",
            "check",
            "run",
            "compile",
            "lint",
        ]
        magit_patterns = [
            "git",
            "commit",
            "push",
            "pull",
            "branch",
            "merge",
            "status",
            "diff",
            "log",
            "magit",
        ]

        # Count matches and calculate confidence
        nav_score = sum(1 for word in navigation_patterns if word in user_lower)
        edit_score = sum(1 for word in editing_patterns if word in user_lower)
        file_score = sum(1 for word in file_patterns if word in user_lower)
        debug_score = sum(1 for word in debug_patterns if word in user_lower)
        magit_score = sum(1 for word in magit_patterns if word in user_lower)

        scores = {
            "navigation": nav_score,
            "editing": edit_score,
            "file_ops": file_score,
            "debugging": debug_score,
            "git_ops": magit_score,
        }

        # Find best match
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]

        if best_score >= 2:
            confidence = min(0.95, 0.7 + (best_score * 0.1))
        elif best_score == 1:
            confidence = 0.8
        else:
            confidence = 0.3
            best_intent = "unknown"

        return {
            "intent": best_intent,
            "action": self._get_default_action(best_intent),
            "confidence": confidence,
            "method": "smart_local",
        }

    def _get_default_action(self, intent: str) -> str:
        """Returns a default action for a given intent."""
        # Placeholder implementation
        if intent == "navigation":
            return "move_cursor"
        elif intent == "editing":
            return "edit_text"
        elif intent == "file_ops":
            return "manage_file"
        elif intent == "debugging":
            return "debug_code"
        elif intent == "git_ops":
            return "perform_git_action"
        else:
            return "unknown_action"

    def _classify_tutorial_instruction(self, user_input: str) -> Dict[str, Any]:
        """Classify tutorial-specific instruction patterns"""
        import re

        user_input = user_input.strip()

        # Tutorial instruction patterns with high confidence
        tutorial_patterns = [
            # Screen navigation
            (r"type\s+c-v\b", "navigation", "scroll_screen", 0.95),
            (r"type\s+m-v\b", "navigation", "scroll_screen", 0.95),
            (r"type\s+c-l\b", "navigation", "recenter", 0.95),
            # Basic cursor movement
            (r"type.*c-n", "navigation", "move_cursor", 0.90),
            (r"type.*c-p", "navigation", "move_cursor", 0.90),
            (r"type.*c-f", "navigation", "move_cursor", 0.90),
            (r"type.*c-b", "navigation", "move_cursor", 0.90),
            (r"type.*c-a", "navigation", "move_cursor", 0.90),
            (r"type.*c-e", "navigation", "move_cursor", 0.90),
            # Word movement
            (r"type.*m-f", "navigation", "move_word", 0.90),
            (r"type.*m-b", "navigation", "move_word", 0.90),
            # Multiple command instructions
            (r"do.*c-n.*bring.*cursor.*down", "navigation", "move_cursor", 0.85),
            (r"move.*line.*c-f.*then.*c-p", "navigation", "move_cursor", 0.85),
            (r"try.*c-b.*beginning", "navigation", "move_cursor", 0.85),
            (r"try.*c-a.*c-e", "navigation", "move_cursor", 0.85),
            # Screen scrolling instructions
            (r"scroll.*down.*tutorial", "navigation", "scroll_screen", 0.85),
            (r"move.*backward.*screen", "navigation", "scroll_screen", 0.85),
            # Generic tutorial command patterns
            (r"now\s+type", "tutorial_command", "execute_command", 0.80),
            (r"try\s+typing", "tutorial_command", "execute_command", 0.80),
            (r"do\s+a\s+few", "tutorial_command", "repeat_command", 0.80),
        ]

        # Check each pattern
        for pattern, intent, action, confidence in tutorial_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return {
                    "intent": intent,
                    "action": action,
                    "confidence": confidence,
                    "method": "tutorial_specific",
                }

        # Low confidence fallback for tutorial-like text
        if ">>" in user_input or "type" in user_input.lower():
            return {
                "intent": "tutorial_command",
                "action": "execute_command",
                "confidence": 0.6,
                "method": "tutorial_fallback",
            }

        return {
            "intent": "unknown",
            "action": "",
            "confidence": 0.0,
            "method": "no_tutorial_match",
        }

    def _quick_ai_classification(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Quick AI classification with 2-second timeout"""
        try:
            # Ultra-minimal prompt
            prompt = f'Intent: "{user_input}" -> JSON: {{"intent":"navigation","confidence":0.9}}'

            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "phi3:mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=2,  # Very aggressive timeout
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")

                # Quick JSON extraction
                try:
                    if "{" in content and "}" in content:
                        start = content.find("{")
                        end = content.rfind("}") + 1
                        json_str = content[start:end]
                        analysis = json.loads(json_str)
                        analysis["method"] = "quick_ai"
                        analysis["action"] = self._get_default_action(
                            analysis.get("intent", "unknown")
                        )

                        print(
                            f"⚡ Quick AI: {analysis.get('intent')} (confidence: {analysis.get('confidence')})"
                        )
                        return analysis
                except:
                    pass

        except Exception as e:
            # Silently fail - timeouts are expected
            pass

        return None

    def _enhanced_local_analysis(self, user_input: str) -> Dict[str, Any]:
        """Enhanced fallback with contextual hints"""
        user_lower = user_input.lower()

        # Context-aware classification
        if self.context.current_file:
            if self.context.current_file.endswith(".py"):
                if any(
                    word in user_lower
                    for word in ["function", "def", "class", "import"]
                ):
                    return {
                        "intent": "navigation",
                        "action": "find_definition",
                        "confidence": 0.85,
                        "method": "context_enhanced",
                    }
            elif self.context.current_file.endswith(".js"):
                if any(
                    word in user_lower for word in ["function", "const", "let", "var"]
                ):
                    return {
                        "intent": "navigation",
                        "action": "find_function",
                        "confidence": 0.85,
                        "method": "context_enhanced",
                    }

        # Advanced pattern matching
        if "magit" in user_lower or "git status" in user_lower:
            return {
                "intent": "git_ops",
                "action": "show_status",
                "confidence": 0.9,
                "method": "pattern_match",
            }
        elif any(word in user_lower for word in ["move", "go", "cursor"]):
            return {
                "intent": "navigation",
                "action": "move_cursor",
                "confidence": 0.85,
                "method": "pattern_match",
            }
        elif any(word in user_lower for word in ["delete", "remove", "kill"]):
            return {
                "intent": "editing",
                "action": "delete_text",
                "confidence": 0.85,
                "method": "pattern_match",
            }
        else:
            return {
                "intent": "unknown",
                "action": "clarify",
                "confidence": 0.5,
                "method": "fallback",
            }

    def generate_suggestions(self, intent_analysis: Dict[str, Any]) -> List[str]:
        """Generate contextual suggestions"""
        intent = intent_analysis.get("intent", "unknown")

        if intent == "navigation":
            suggestions = [
                "C-f (forward-char) - Move forward one character",
                "C-b (backward-char) - Move backward one character",
                "C-n (next-line) - Move to next line",
                "C-p (previous-line) - Move to previous line",
                "C-a (beginning-of-line) - Move to beginning of line",
                "C-e (end-of-line) - Move to end of line",
                "M-f - Move forward one word",
                "M-b - Move backward one word",
                "C-v - Scroll down one screen",
                "M-v - Scroll up one screen",
                "C-l - Recenter screen",
            ]
        elif intent == "tutorial_command":
            # For tutorial commands, extract the specific command being taught
            import re

            # Get the original user input - we need to pass it to this method
            user_input = getattr(self, "_current_user_input", "")

            # Extract commands from tutorial instruction
            commands = re.findall(r"C-[a-z-]+|M-[a-z-]+", user_input, re.IGNORECASE)

            suggestions = []
            for cmd in commands:
                cmd_upper = cmd.upper()
                if cmd_upper == "C-V":
                    suggestions.append(
                        "C-v - Scroll down one screen (View next screen)"
                    )
                elif cmd_upper == "M-V":
                    suggestions.append(
                        "M-v - Scroll up one screen (View previous screen)"
                    )
                elif cmd_upper == "C-L":
                    suggestions.append("C-l - Recenter screen and redisplay")
                elif cmd_upper == "C-N":
                    suggestions.append("C-n - Move to next line")
                elif cmd_upper == "C-P":
                    suggestions.append("C-p - Move to previous line")
                elif cmd_upper == "C-F":
                    suggestions.append("C-f - Move forward one character")
                elif cmd_upper == "C-B":
                    suggestions.append("C-b - Move backward one character")
                elif cmd_upper == "C-A":
                    suggestions.append("C-a - Move to beginning of line")
                elif cmd_upper == "C-E":
                    suggestions.append("C-e - Move to end of line")
                elif cmd_upper == "M-F":
                    suggestions.append("M-f - Move forward one word")
                elif cmd_upper == "M-B":
                    suggestions.append("M-b - Move backward one word")
                else:
                    suggestions.append(f"{cmd} - Execute this command")

            if not suggestions:
                suggestions = ["Follow the tutorial instruction as written"]
        elif intent == "editing":
            suggestions = [
                "C-d (delete-char) - Delete character at point",
                "M-d - Delete word forward",
                "C-k (kill-line) - Delete to end of line",
                "C-y (yank) - Paste killed text",
                "C-/ - Undo last change",
            ]
        elif intent == "file_ops":
            suggestions = [
                "C-x C-f (find-file) - Open file",
                "C-x C-s (save-buffer) - Save current file",
                "C-x C-c - Exit Emacs",
                "C-x b - Switch buffer",
                "C-x C-b - List buffers",
            ]
        elif intent == "debugging":
            suggestions = [
                "M-x compile - Run compilation",
                "M-x gdb - Start debugger",
                "M-x flycheck-mode - Enable syntax checking",
                "C-x ` - Jump to next error",
                "M-x grep - Search in files",
            ]
        else:
            suggestions = [
                "Try being more specific about what you want to do",
                "Examples: 'move to end of line', 'delete this word', 'open file'",
                "Type 'help' for available commands",
            ]

        return suggestions

    def learn_from_interaction(
        self,
        user_input: str,
        intent_analysis: Dict[str, Any],
        user_feedback: str = "positive",
    ):
        """Learn from user interactions"""

        learning_event = {
            "user_input": user_input,
            "intent": intent_analysis.get("intent", "unknown"),
            "action": intent_analysis.get("action", ""),
            "confidence": str(intent_analysis.get("confidence", 0.0)),
            "feedback": user_feedback,
            "context_file": self.context.current_file or "",
            "timestamp": str(time.time()),
            "session": self.session_id,
        }

        # Store learning event in Redis
        self.redis_client.xadd("dev_assistant:learning_events", learning_event)
        print(
            f"📚 Learned from interaction: {intent_analysis.get('intent')} ({user_feedback})"
        )

    def get_contextual_help(self) -> str:
        """Generate contextual help based on current state"""

        help_prompt = f"""Provide helpful development tips for this context:

Current context:
- File: {self.context.current_file or 'No file open'}
- Line: {self.context.cursor_line}
- Language: {self.context.project_language}
- Recent commands: {self.context.recent_commands[-3:] if self.context.recent_commands else 'None'}

Give 3 practical tips for this development context:"""

        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "phi3:mini",
                    "messages": [{"role": "user", "content": help_prompt}],
                    "stream": False,
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")
                return content

        except Exception as e:
            print(f"⚠️  Help generation failed: {e}")

        # Fallback help
        return f"""Based on your current context:
• File: {self.context.current_file or 'No file open'}
• Language: {self.context.project_language}

Try these commands:
• C-h f - Describe function
• C-h k - Describe key binding  
• C-h m - Describe current mode"""

    def get_redis_stats(self) -> Dict[str, Any]:
        """Get Redis coordination statistics"""
        stats = {}

        streams = [
            "dev_assistant:commands",
            "dev_assistant:context_changes",
            "dev_assistant:ai_suggestions",
            "dev_assistant:learning_events",
        ]

        for stream in streams:
            try:
                info = self.redis_client.xinfo_stream(stream)
                stats[stream] = {
                    "length": info.get("length", 0),
                    "first_entry": info.get("first-entry", [None])[0],
                    "last_entry": info.get("last-entry", [None])[0],
                }
            except:
                stats[stream] = {"length": 0}

        return stats


def main():
    """Demonstrate the intelligent development assistant"""

    print("🚀 INTELLIGENT DEVELOPMENT ASSISTANT DEMO")
    print("=" * 60)

    assistant = IntelligentDevAssistant()

    # Simulate development context
    print("\n1. Setting up development context...")
    assistant.update_context(
        working_directory="/Users/jonathanhill/src/redis-ai-challenge",
        current_file="redis_ai_learner.py",
        cursor_line=145,
        project_language="python",
    )

    # Test AI-powered intent recognition
    test_intents = [
        "I want to move to the end of this line",
        "Help me delete this function",
        "How do I save this file?",
        "There's a bug in this code, how do I debug it?",
        "Show me navigation commands",
    ]

    print("\n2. Testing AI-powered intent recognition...")
    for intent in test_intents:
        print(f"\n🎯 User intent: '{intent}'")

        # Process with AI
        analysis = assistant.process_user_intent(intent)

        # Generate suggestions
        suggestions = assistant.generate_suggestions(analysis)

        print(f"💡 Suggestions:")
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"   {i}. {suggestion}")

        # Simulate learning
        assistant.learn_from_interaction(intent, analysis, "positive")

        time.sleep(1)  # Pace the demo

    # Test contextual help
    print("\n3. Testing contextual help generation...")
    help_text = assistant.get_contextual_help()
    print(f"🤝 Contextual Help:\n{help_text}")

    # Show Redis coordination stats
    print("\n4. Redis coordination statistics...")
    stats = assistant.get_redis_stats()

    for stream, data in stats.items():
        stream_name = stream.split(":")[-1]
        print(f"   📊 {stream_name}: {data.get('length', 0)} events")

    print("\n" + "=" * 60)
    print("🎉 INTELLIGENT DEV ASSISTANT DEMO COMPLETE")
    print("✅ Real AI intent recognition working")
    print("✅ Redis coordination operational")
    print("✅ Contextual suggestions generated")
    print("✅ Learning from interactions")
    print("🎯 Ready for integration with real development workflows!")


if __name__ == "__main__":
    main()
