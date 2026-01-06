#!/usr/bin/env python3
"""
The Missing Categorical Morphism: RedisStream -> ClaudeResponse
Following Claude Code's interface patterns for type safety
"""

import redis
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import anthropic
import os

@dataclass
class EmacsContext:
    """Claude Code-style interface for Emacs state"""
    buffer_name: str
    cursor_line: int
    cursor_col: int
    buffer_content: str
    selected_text: Optional[str]
    file_path: Optional[str]

@dataclass
class RedisCommand:
    """Claude Code-style interface for Redis commands"""
    command_type: str
    context: EmacsContext
    user_input: str
    timestamp: float
    stream_id: str

@dataclass
class ClaudeResponse:
    """Claude Code-style interface for Claude responses"""
    response_text: str
    elisp_commands: List[str]
    confidence: float
    timestamp: float
    reasoning: str

class ClaudeApiMorphism:
    """The missing categorical morphism: RedisStream -> ClaudeResponse"""
    
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        print("🔗 Categorical morphism RedisStream -> ClaudeResponse initialized")
    
    def parse_redis_command(self, redis_data: Dict[str, Any]) -> RedisCommand:
        """Parse Redis stream data into structured command (Category Theory: JSON -> Command)"""
        
        try:
            # Extract structured data following Claude Code's pattern
            fields = redis_data.get('fields', {})
            
            context = EmacsContext(
                buffer_name=fields.get('buffer_name', '*unknown*'),
                cursor_line=int(fields.get('cursor_line', 1)),
                cursor_col=int(fields.get('cursor_col', 1)),
                buffer_content=fields.get('buffer_content', ''),
                selected_text=fields.get('selected_text'),
                file_path=fields.get('file_path')
            )
            
            return RedisCommand(
                command_type=fields.get('command_type', 'unknown'),
                context=context,
                user_input=fields.get('user_input', ''),
                timestamp=float(fields.get('timestamp', time.time())),
                stream_id=redis_data.get('id', '')
            )
        except Exception as e:
            print(f"❌ Parse error: {e}")
            # Fallback command for robustness
            return RedisCommand(
                command_type='error',
                context=EmacsContext('*error*', 1, 1, '', None, None),
                user_input='Parse error',
                timestamp=time.time(),
                stream_id='error'
            )
    
    def generate_claude_prompt(self, command: RedisCommand) -> str:
        """Generate Claude API prompt from structured command"""
        
        if command.command_type == 'keystroke':
            return f"""You are an Emacs AI assistant. The user just typed in Emacs.

Context:
- Buffer: {command.context.buffer_name}
- File: {command.context.file_path or 'unsaved'}
- Cursor: line {command.context.cursor_line}, col {command.context.cursor_col}
- Recent input: {command.user_input}

Buffer content around cursor:
```
{command.context.buffer_content[-200:] if command.context.buffer_content else '(empty buffer)'}
```

Based on this context, provide:
1. A helpful response (1-2 sentences)
2. Any Elisp commands to execute (if needed)

Respond in JSON format:
{{
  "response": "your response text",
  "elisp_commands": ["(command1)", "(command2)"],
  "confidence": 0.95,
  "reasoning": "why you chose this response"
}}"""
        
        elif command.command_type == 'natural_language':
            return f"""You are an Emacs AI assistant. The user asked: "{command.user_input}"

Current Emacs context:
- Buffer: {command.context.buffer_name}
- File: {command.context.file_path or 'unsaved'}
- Cursor: line {command.context.cursor_line}, col {command.context.cursor_col}

Selected text: {command.context.selected_text or 'none'}

Buffer content:
```
{command.context.buffer_content[:500] if command.context.buffer_content else '(empty)'}
```

Respond with helpful Emacs actions in JSON format:
{{
  "response": "explanation of what you'll do",
  "elisp_commands": ["(elisp-command1)", "(elisp-command2)"],
  "confidence": 0.9,
  "reasoning": "step-by-step reasoning"
}}"""
        
        else:
            return f"Unknown command type: {command.command_type}. Please clarify what you need help with in Emacs."
    
    def call_claude_api(self, prompt: str) -> ClaudeResponse:
        """The core morphism: Prompt -> ClaudeResponse"""
        
        try:
            print(f"🤖 Calling Claude API...")
            
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.1,
                messages=[{
                    "role": "user", 
                    "content": prompt
                }]
            )
            
            response_text = response.content[0].text
            
            # Try to parse JSON response
            try:
                parsed = json.loads(response_text)
                return ClaudeResponse(
                    response_text=parsed.get('response', response_text),
                    elisp_commands=parsed.get('elisp_commands', []),
                    confidence=float(parsed.get('confidence', 0.8)),
                    timestamp=time.time(),
                    reasoning=parsed.get('reasoning', 'Claude AI reasoning')
                )
            except json.JSONDecodeError:
                # Fallback for non-JSON responses
                return ClaudeResponse(
                    response_text=response_text,
                    elisp_commands=[],
                    confidence=0.7,
                    timestamp=time.time(),
                    reasoning='Plain text response'
                )
                
        except Exception as e:
            print(f"❌ Claude API error: {e}")
            return ClaudeResponse(
                response_text=f"AI Error: {str(e)}",
                elisp_commands=[],
                confidence=0.1,
                timestamp=time.time(),
                reasoning=f"API error: {str(e)}"
            )
    
    def write_response_to_redis(self, response: ClaudeResponse, original_command: RedisCommand):
        """Write Claude response back to Redis stream"""
        
        response_data = {
            'response_text': response.response_text,
            'elisp_commands': json.dumps(response.elisp_commands),
            'confidence': str(response.confidence),
            'timestamp': str(response.timestamp),
            'reasoning': response.reasoning,
            'original_command_id': original_command.stream_id
        }
        
        try:
            result = self.redis_client.xadd("emacs:responses", response_data)
            print(f"✅ Response written to Redis: {result}")
            return result
        except Exception as e:
            print(f"❌ Redis write error: {e}")
            return None
    
    def execute_morphism(self, redis_stream_data: Dict[str, Any]) -> bool:
        """Execute the complete morphism: RedisStream -> ClaudeResponse"""
        
        print(f"\n🔗 Executing categorical morphism...")
        print(f"   RedisStream -> Command -> Prompt -> ClaudeAPI -> Response -> Redis")
        
        try:
            # Step 1: Parse Redis data into structured command
            command = self.parse_redis_command(redis_stream_data)
            print(f"   ✅ Parsed command: {command.command_type}")
            
            # Step 2: Generate Claude prompt
            prompt = self.generate_claude_prompt(command)
            print(f"   ✅ Generated prompt ({len(prompt)} chars)")
            
            # Step 3: Call Claude API (the core morphism!)
            claude_response = self.call_claude_api(prompt)
            print(f"   ✅ Claude response: confidence {claude_response.confidence}")
            
            # Step 4: Write response back to Redis
            redis_result = self.write_response_to_redis(claude_response, command)
            print(f"   ✅ Redis write: {redis_result}")
            
            print(f"🎯 Morphism completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Morphism failed: {e}")
            return False
    
    def monitor_redis_stream(self, stream_name: str = "emacs:commands"):
        """Monitor Redis stream and execute morphism for each message"""
        
        print(f"🔄 Monitoring Redis stream: {stream_name}")
        print(f"🎯 Ready to execute RedisStream -> ClaudeResponse morphism")
        print("-" * 50)
        
        last_id = "$"  # Start from newest messages
        
        while True:
            try:
                # Listen for new messages
                streams = self.redis_client.xread(
                    {stream_name: last_id},
                    count=1,
                    block=1000  # Block for 1 second
                )
                
                if streams:
                    for stream, messages in streams:
                        for message_id, fields in messages:
                            print(f"\n📨 New message: {message_id}")
                            
                            # Execute the morphism!
                            redis_data = {
                                'id': message_id,
                                'fields': fields
                            }
                            
                            success = self.execute_morphism(redis_data)
                            
                            if success:
                                print(f"✅ Morphism executed successfully for {message_id}")
                            else:
                                print(f"❌ Morphism failed for {message_id}")
                            
                            last_id = message_id
                            
            except KeyboardInterrupt:
                print(f"\n🛑 Stopping Redis stream monitor")
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(1)  # Brief pause before retry


def main():
    """Run the categorical morphism system"""
    
    print("🚀 CATEGORICAL MORPHISM: RedisStream -> ClaudeResponse")
    print("=" * 60)
    print("Following Claude Code's interface patterns for type safety")
    print()
    
    # Initialize the morphism
    morphism = ClaudeApiMorphism()
    
    # Test with sample data
    print("🧪 Testing morphism with sample data...")
    sample_data = {
        'id': 'test-1234',
        'fields': {
            'command_type': 'natural_language',
            'user_input': 'help me write a Python function',
            'buffer_name': 'test.py',
            'cursor_line': '10',
            'cursor_col': '5',
            'buffer_content': 'def hello():\n    print("hello")\n\n',
            'timestamp': str(time.time())
        }
    }
    
    test_success = morphism.execute_morphism(sample_data)
    
    if test_success:
        print(f"\n✅ Test morphism successful!")
        print(f"🔄 Starting live Redis stream monitoring...")
        
        # Start monitoring Redis streams
        morphism.monitor_redis_stream()
    else:
        print(f"\n❌ Test morphism failed - check configuration")


if __name__ == "__main__":
    main()