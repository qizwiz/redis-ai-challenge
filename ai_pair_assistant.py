#!/usr/bin/env python3
"""
AI Pair Programming Assistant

This runs in the background, watching Redis streams for your coding activity
and providing helpful suggestions without being intrusive.
"""

import redis
import json
import subprocess
import time
import threading
from typing import Dict, List

class AIPairAssistant:
    """AI assistant that helps with real development work"""
    
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.session_id = None
        self.running = False
        self.context_history = []
        
    def start_assistant(self):
        """Start the AI pair programming assistant"""
        print("🤖 AI Pair Programming Assistant starting...")
        self.running = True
        
        # Start listening thread
        listener_thread = threading.Thread(target=self.listen_for_events)
        listener_thread.daemon = True
        listener_thread.start()
        
        print("✅ Assistant ready - use C-c a s in Emacs to start pairing")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_assistant()
    
    def listen_for_events(self):
        """Listen for events from Emacs"""
        print("👂 Listening for Emacs events...")
        
        while self.running:
            try:
                # Read from the pair programming stream
                events = self.redis.xread({'ai:pair_programming': '$'}, block=5000, count=1)
                
                for stream, messages in events:
                    for message_id, fields in messages:
                        self.process_event(message_id, fields)
                        
            except Exception as e:
                if self.running:  # Only print errors if we're supposed to be running
                    print(f"⚠️ Error listening for events: {e}")
                    time.sleep(1)
    
    def process_event(self, message_id: str, fields: Dict):
        """Process an event from Emacs"""
        event_type = fields.get('event', 'unknown')
        session = fields.get('session', 'unknown')
        
        if event_type == 'session_start':
            self.session_id = session
            data = json.loads(fields.get('data', '{}'))
            buffer_name = data.get('buffer', 'unknown')
            print(f"🚀 Started pair programming session: {session}")
            print(f"   Working on: {buffer_name}")
            
        elif event_type == 'context_update':
            self.handle_context_update(fields)
            
        elif event_type == 'file_saved':
            data = json.loads(fields.get('data', '{}'))
            file_name = data.get('file', 'unknown file')
            print(f"💾 Saved: {file_name}")
            self.suggest_next_steps(data)
            
        elif event_type == 'keystroke':
            self.handle_keystroke(fields)
            
        elif event_type == 'help_request':
            self.handle_help_request(fields)
            
        elif event_type == 'session_end':
            print(f"⏹️ Ended pair programming session: {session}")
            self.session_id = None
    
    def handle_context_update(self, fields: Dict):
        """Handle context updates from Emacs"""
        try:
            data = json.loads(fields.get('data', '{}'))
            
            # Store context for analysis
            self.context_history.append(data)
            if len(self.context_history) > 50:  # Keep last 50 contexts
                self.context_history.pop(0)
            
            # Only provide suggestions occasionally, not on every update
            if len(self.context_history) % 5 == 0:  # Every 5th update
                self.analyze_coding_pattern(data)
                
        except json.JSONDecodeError:
            pass  # Ignore malformed data
    
    def analyze_coding_pattern(self, context: Dict):
        """Analyze coding patterns and suggest improvements"""
        current_line = context.get('current-line', '').strip()
        command = context.get('command', '')
        
        # Simple pattern analysis
        suggestions = []
        
        if 'def ' in current_line and not current_line.endswith(':'):
            suggestions.append("💡 Consider adding docstring after function definition")
            
        if current_line.count('(') != current_line.count(')'):
            suggestions.append("⚠️ Unbalanced parentheses detected")
            
        if len(current_line) > 100:
            suggestions.append("📏 Line is quite long - consider breaking it up")
            
        # Store suggestions in Redis for Emacs to display
        if suggestions:
            for suggestion in suggestions[:1]:  # Only show one suggestion
                self.send_suggestion(suggestion, context)
    
    def suggest_next_steps(self, save_data: Dict):
        """Suggest next steps after saving a file"""
        file_name = save_data.get('file', '')
        
        if file_name.endswith('.py'):
            self.send_suggestion("🐍 Consider running tests or linting after saving Python file", save_data)
        elif file_name.endswith('.js'):
            self.send_suggestion("📦 Consider checking with npm test or eslint", save_data)
        elif file_name.endswith('.el'):
            self.send_suggestion("🔧 Consider byte-compiling or testing Elisp code", save_data)
    
    def handle_keystroke(self, fields: Dict):
        """Handle individual keystrokes from Emacs"""
        session = fields.get('session', 'unknown')
        command = fields.get('command', 'unknown')
        point = fields.get('point', '0')
        
        # Only respond to significant commands, not every character
        if command in ['newline', 'yank', 'kill-line', 'save-buffer']:
            print(f"⌨️ Keystroke: {command} at position {point}")
            
            # Provide contextual suggestions
            if command == 'newline':
                self.send_suggestion("💡 Consider adding comments for complex logic", {})
            elif command == 'save-buffer':
                self.send_suggestion("🔍 Run tests after saving?", {})
                
        # Store keystroke for pattern analysis
        self.context_history.append({
            'type': 'keystroke',
            'command': command,
            'position': point,
            'session': session
        })
    
    def handle_help_request(self, fields: Dict):
        """Handle specific help requests"""
        data = json.loads(fields.get('data', '{}'))
        prompt = data.get('prompt', '')
        context = data.get('context', '')
        
        print(f"❓ Help requested: {prompt}")
        
        # Provide contextual help based on the request
        help_response = self.generate_help_response(prompt, context)
        self.send_emacs_message(help_response)
    
    def generate_help_response(self, prompt: str, context: str) -> str:
        """Generate helpful response based on prompt and context"""
        prompt_lower = prompt.lower()
        
        if 'refactor' in prompt_lower:
            return "🔄 Refactoring suggestion: Extract common patterns into functions"
        elif 'test' in prompt_lower:
            return "🧪 Testing tip: Add tests for edge cases and error conditions"
        elif 'debug' in prompt_lower:
            return "🐛 Debugging: Add print statements or use debugger at key points"
        elif 'optimize' in prompt_lower:
            return "⚡ Optimization: Profile first to identify actual bottlenecks"
        else:
            return f"🤖 I see you're working on: {prompt}. Let me analyze the context..."
    
    def send_suggestion(self, suggestion: str, context: Dict):
        """Send suggestion back to Emacs"""
        suggestion_data = {
            'suggestion': suggestion,
            'context': context,
            'timestamp': time.time(),
            'session': self.session_id
        }
        
        self.redis.xadd('ai:suggestions', suggestion_data)
        # Also show in terminal for now
        print(f"💡 {suggestion}")
    
    def send_emacs_message(self, message: str):
        """Send message to Emacs minibuffer"""
        elisp_command = f'(message "{message}")'
        subprocess.run(['emacsclient', '--eval', elisp_command], 
                      capture_output=True, text=True)
    
    def stop_assistant(self):
        """Stop the assistant"""
        self.running = False
        print("\n🛑 AI Pair Programming Assistant stopped")

if __name__ == "__main__":
    assistant = AIPairAssistant()
    assistant.start_assistant()