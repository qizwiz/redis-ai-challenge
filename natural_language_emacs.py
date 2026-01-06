#!/usr/bin/env python3
"""
Natural Language Emacs Interface
Talk to Emacs in plain English through Redis facade
"""

import redis
import json
import time
import subprocess
from typing import Dict, Any, Optional

class NaturalLanguageEmacs:
    """Natural language interface to Emacs via Redis facade"""

    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.session = f"nl_emacs_{int(time.time())}"

        # Initialize intent patterns (simple pattern matching for now)
        self.intents = {
            'insert': ['insert', 'type', 'write', 'add text'],
            'move': ['go to', 'move', 'jump', 'navigate'],
            'delete': ['delete', 'remove', 'erase', 'kill'],
            'save': ['save', 'write file'],
            'open': ['open', 'load', 'find file'],
            'search': ['search', 'find', 'look for'],
            'buffer': ['switch buffer', 'change buffer', 'show buffer'],
            'status': ['what', 'where', 'show me', 'status'],
        }

    def understand(self, natural_text: str) -> Dict[str, Any]:
        """Convert natural language to Emacs intent"""
        text_lower = natural_text.lower()

        # Detect intent
        detected_intent = 'unknown'
        for intent, patterns in self.intents.items():
            if any(pattern in text_lower for pattern in patterns):
                detected_intent = intent
                break

        # Extract parameters
        intent_data = {
            'raw_text': natural_text,
            'intent': detected_intent,
            'timestamp': time.time(),
        }

        # Intent-specific parsing
        if detected_intent == 'insert':
            # Extract text after insert trigger
            for trigger in self.intents['insert']:
                if trigger in text_lower:
                    idx = text_lower.index(trigger) + len(trigger)
                    intent_data['text'] = natural_text[idx:].strip(' "\'')
                    break

        elif detected_intent == 'move':
            if 'beginning' in text_lower or 'start' in text_lower:
                intent_data['position'] = 'beginning'
            elif 'end' in text_lower:
                intent_data['position'] = 'end'
            elif 'line' in text_lower:
                # Extract line number
                words = text_lower.split()
                for i, word in enumerate(words):
                    if word.isdigit():
                        intent_data['line'] = int(word)
                        break

        elif detected_intent == 'delete':
            if 'line' in text_lower:
                intent_data['what'] = 'line'
            elif 'word' in text_lower:
                intent_data['what'] = 'word'
            else:
                intent_data['what'] = 'char'

        # Log understanding to Redis
        self.redis.xadd(f'{self.session}:understanding', {
            'intent': detected_intent,
            'data': json.dumps(intent_data),
            'timestamp': time.time()
        })

        return intent_data

    def execute(self, intent_data: Dict[str, Any]) -> str:
        """Execute intent through Emacs facade"""
        intent = intent_data['intent']
        result = None

        if intent == 'insert':
            text = intent_data.get('text', '')
            result = self._emacs_eval(f'(insert "{text}")')

        elif intent == 'move':
            pos = intent_data.get('position')
            line = intent_data.get('line')
            if pos == 'beginning':
                result = self._emacs_eval('(goto-char (point-min))')
            elif pos == 'end':
                result = self._emacs_eval('(goto-char (point-max))')
            elif line:
                result = self._emacs_eval(f'(goto-line {line})')

        elif intent == 'delete':
            what = intent_data.get('what', 'char')
            if what == 'line':
                result = self._emacs_eval('(kill-line)')
            elif what == 'word':
                result = self._emacs_eval('(kill-word 1)')
            else:
                result = self._emacs_eval('(delete-char 1)')

        elif intent == 'status':
            result = self._get_status()

        else:
            result = f"I don't know how to: {intent_data['raw_text']}"

        # Log execution to Redis
        self.redis.xadd(f'{self.session}:execution', {
            'intent': intent,
            'result': str(result),
            'timestamp': time.time()
        })

        return result

    def _emacs_eval(self, elisp: str) -> str:
        """Evaluate Elisp through emacsclient"""
        try:
            result = subprocess.run(
                ['emacsclient', '--eval', elisp],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.stdout.strip() if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Error: {e}"

    def _get_status(self) -> str:
        """Get current Emacs status"""
        buffer = self._emacs_eval('(buffer-name)')
        point = self._emacs_eval('(point)')
        line = self._emacs_eval('(line-number-at-pos)')

        return f"Buffer: {buffer}, Point: {point}, Line: {line}"

    def talk(self, natural_text: str) -> str:
        """Main interface: talk to Emacs in natural language"""
        print(f"\n💬 You: {natural_text}")

        # Understand the intent
        intent = self.understand(natural_text)
        print(f"🧠 Understood: {intent['intent']}")

        # Execute through facade
        result = self.execute(intent)
        print(f"✅ Result: {result}")

        return result

    def conversation_loop(self):
        """Interactive conversation with Emacs"""
        print("🎯 Natural Language Emacs Interface")
        print("Talk to Emacs in plain English!")
        print("Examples:")
        print("  - 'insert hello world'")
        print("  - 'go to the beginning'")
        print("  - 'delete this line'")
        print("  - 'what's my status?'")
        print("Type 'quit' to exit.\n")

        while True:
            try:
                user_input = input("💬 You: ").strip()

                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break

                if not user_input:
                    continue

                # Process the command
                intent = self.understand(user_input)
                print(f"🧠 Understood: {intent['intent']}")

                result = self.execute(intent)
                print(f"✅ Emacs: {result}\n")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")

def demonstrate_natural_language():
    """Demonstrate natural language interface"""
    nl = NaturalLanguageEmacs()

    print("🎯 Demonstrating Natural Language Emacs Interface\n")

    # Test commands
    commands = [
        "insert Hello from natural language!",
        "go to the beginning",
        "what's my status?",
        "move to the end",
        "insert More text here.",
    ]

    for cmd in commands:
        nl.talk(cmd)
        time.sleep(0.5)

    print("\n✅ Demonstration complete!")
    print(f"\nCheck Redis streams:")
    print(f"  redis-cli XREAD STREAMS {nl.session}:understanding 0")
    print(f"  redis-cli XREAD STREAMS {nl.session}:execution 0")

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        demonstrate_natural_language()
    elif len(sys.argv) > 1 and sys.argv[1] == 'talk':
        # Single command mode
        nl = NaturalLanguageEmacs()
        command = ' '.join(sys.argv[2:])
        nl.talk(command)
    else:
        # Interactive mode
        nl = NaturalLanguageEmacs()
        nl.conversation_loop()
