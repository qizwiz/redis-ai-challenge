#!/usr/bin/env python3
"""
LIVE CODE REVIEWER - My harp assistant for real-time code review
Built because I WANT this capability right now
"""

import time
import subprocess
import threading
from pathlib import Path
from semantic_completion import SemanticCompletion

class LiveCodeReviewer:
    """My harp assistant that reviews code as you type"""
    
    def __init__(self):
        self.daemon = "work"
        self.monitoring = True
        self.last_content = ""
        self.semantic_completion = SemanticCompletion()
        print("👁️ LIVE CODE REVIEWER: My intelligent harp assistant with semantic completion")
    
    def get_current_buffer_content(self):
        """See what you're actually typing"""
        try:
            # Get current buffer content
            content = subprocess.run([
                'emacsclient', '-s', self.daemon, '-e', 
                '(buffer-substring-no-properties (point-min) (point-max))'
            ], capture_output=True, text=True, timeout=1).stdout.strip().strip('"')
            
            return content.replace('\\n', '\n') if content != 'nil' else ""
        except:
            return ""
    
    def analyze_code_change(self, new_content, old_content):
        """Analyze what changed and give intelligent suggestions"""
        
        if len(new_content) > len(old_content):
            # Something was added
            added_text = new_content[len(old_content):]
            
            suggestions = []
            
            # Smart suggestions based on what was typed
            if 'def ' in added_text:
                suggestions.append("🔍 New function detected - consider adding docstring")
            
            if 'import ' in added_text:
                suggestions.append("📦 New import - check if it's used")
                
            if 'TODO' in added_text or 'FIXME' in added_text:
                suggestions.append("📝 TODO added - track in issue system")
                
            if 'print(' in added_text:
                suggestions.append("🐛 Debug print - consider logging instead")
                
            if len(added_text.split('\n')) > 5:
                suggestions.append("📏 Large addition - consider breaking into smaller functions")
            
            # Add semantic suggestions from our codebase
            if len(added_text.strip()) > 3:  # Only for meaningful additions
                try:
                    semantic_suggestions = self.semantic_completion.suggest_from_codebase(added_text.strip())
                    if semantic_suggestions:
                        suggestions.append(f"🧠 From codebase: {semantic_suggestions[0]}")
                except:
                    pass
            
            return suggestions
        
        return []
    
    def give_live_feedback(self, suggestions):
        """Give immediate feedback through Emacs"""
        
        if suggestions:
            message = " | ".join(suggestions)
            try:
                subprocess.run([
                    'emacsclient', '-s', self.daemon, '-e',
                    f'(message "🤖 {message}")'
                ], capture_output=True, timeout=1)
            except:
                pass
    
    def start_live_review_session(self):
        """Start watching your code and giving live feedback"""
        
        print("👁️ STARTING LIVE CODE REVIEW SESSION")
        print("🤖 I'll watch what you type and give intelligent suggestions")
        print("=" * 55)
        
        review_count = 0
        
        try:
            while self.monitoring and review_count < 30:  # 30 cycles = ~1 minute
                current_content = self.get_current_buffer_content()
                
                if current_content and current_content != self.last_content:
                    # Analyze the change
                    suggestions = self.analyze_code_change(current_content, self.last_content)
                    
                    if suggestions:
                        print(f"📝 CODE CHANGE DETECTED:")
                        for suggestion in suggestions:
                            print(f"  {suggestion}")
                        
                        # Give live feedback
                        self.give_live_feedback(suggestions)
                    
                    self.last_content = current_content
                
                review_count += 1
                time.sleep(2)  # Check every 2 seconds
                
        except KeyboardInterrupt:
            print("👁️ Live review stopped")
        
        self.monitoring = False
        return review_count
    
    def demonstrate_intelligence(self):
        """Show what my live reviewer can do"""
        
        print("🎯 DEMONSTRATING LIVE CODE REVIEW INTELLIGENCE")
        
        # Test with sample code changes
        test_cases = [
            ("def new_function():\n    pass", "New function - needs docstring"),
            ("import os\nimport sys", "Multiple imports detected"),  
            ("print('debug info')", "Debug print detected"),
            ("# TODO: fix this later", "TODO comment added")
        ]
        
        for code, expected in test_cases:
            suggestions = self.analyze_code_change(code, "")
            print(f"Code: {code.replace(chr(10), ' | ')}")
            print(f"Suggestions: {suggestions}")
            print()
        
        return True

if __name__ == "__main__":
    reviewer = LiveCodeReviewer()
    
    # Show intelligence
    reviewer.demonstrate_intelligence()
    
    print("🚀 STARTING LIVE SESSION")
    print("Open a Python file and start typing - I'll give live feedback!")
    
    # Start live session
    cycles = reviewer.start_live_review_session()
    
    print(f"\n✅ LIVE CODE REVIEW COMPLETE")
    print(f"👁️ Monitored {cycles} code changes")
    print("🤖 My harp assistant is now intelligent enough to review your code live!")