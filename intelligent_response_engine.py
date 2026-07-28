#!/usr/bin/env python3
"""
Intelligent Response Engine - Real LLM integration for the emergent system

This replaces simple pattern matching with actual AI intelligence using
Claude, GPT-4, and other models for truly intelligent development assistance.
"""

import redis
import json
import time
import os
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from datetime import datetime
import subprocess
import tempfile

# Model providers
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

@dataclass
class DevelopmentContext:
    """Rich context about current development state"""
    current_buffer: str
    buffer_type: str
    project_root: Optional[str]
    git_branch: Optional[str]
    recent_files: List[str]
    cursor_context: str  # Text around cursor
    recent_commands: List[str]
    active_modes: List[str]
    project_files: List[str]
    error_messages: List[str]
    test_status: Optional[str]
    build_status: Optional[str]

@dataclass
class IntelligentResponse:
    """An intelligent response from the AI"""
    response_type: str  # message, elisp_command, file_edit, suggestion
    content: str
    confidence: float
    reasoning: str
    suggested_actions: List[str]
    context_used: List[str]
    model_used: str
    processing_time: float

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    async def generate_response(self, context: DevelopmentContext, 
                              user_intent: str, patterns: List[Dict]) -> IntelligentResponse:
        pass
        
    @abstractmethod
    def get_model_name(self) -> str:
        pass

class ClaudeProvider(AIProvider):
    """Claude (Anthropic) AI provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key and ANTHROPIC_AVAILABLE:
            print("⚠️ ANTHROPIC_API_KEY not set - Claude provider disabled")
            
        self.client = None
        if self.api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            
    async def generate_response(self, context: DevelopmentContext, 
                              user_intent: str, patterns: List[Dict]) -> IntelligentResponse:
        if not self.client:
            return self._fallback_response(context, user_intent)
            
        start_time = time.time()
        
        # Build rich prompt with development context
        prompt = self._build_development_prompt(context, user_intent, patterns)
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            )
            
            content = response.content[0].text
            processing_time = time.time() - start_time
            
            # Parse response into structured format
            return self._parse_claude_response(content, context, processing_time)
            
        except Exception as e:
            print(f"🚨 Claude API error: {e}")
            return self._fallback_response(context, user_intent)
            
    def _build_development_prompt(self, context: DevelopmentContext, 
                                user_intent: str, patterns: List[Dict]) -> str:
        """Build rich development context prompt"""
        
        prompt = f"""You are an intelligent development assistant integrated into Emacs. You have deep visibility into the user's development workflow and can provide context-aware assistance.

CURRENT DEVELOPMENT CONTEXT:
- Buffer: {context.current_buffer} ({context.buffer_type})
- Project: {context.project_root or 'Unknown'}
- Git branch: {context.git_branch or 'Unknown'}
- Recent files: {', '.join(context.recent_files[:5])}
- Cursor context: {context.cursor_context[:200]}...
- Recent commands: {', '.join(context.recent_commands[-5:])}
- Active modes: {', '.join(context.active_modes[:10])}

USER INTENT: {user_intent}

LEARNED PATTERNS (from usage):
"""
        
        for pattern in patterns[:3]:  # Include top 3 patterns
            prompt += f"- {pattern.get('description', 'Unknown pattern')} (confidence: {pattern.get('confidence', 0):.2f})\n"
            
        if context.error_messages:
            prompt += f"\nRECENT ERRORS:\n"
            for error in context.error_messages[-2:]:
                prompt += f"- {error}\n"
                
        prompt += f"""
INSTRUCTIONS:
1. Provide intelligent, context-aware development assistance
2. Consider the user's patterns and current workflow
3. Suggest specific, actionable next steps
4. If you see errors, provide solutions
5. Be concise but helpful
6. Consider the project context and file types

RESPONSE FORMAT:
Type: [message|elisp_command|file_edit|suggestion]
Content: [Your response]
Reasoning: [Why this response is appropriate]
Actions: [Suggested next steps, comma-separated]

Focus on being genuinely helpful for {context.buffer_type} development in {context.current_buffer}.
"""
        
        return prompt
        
    def _parse_claude_response(self, content: str, context: DevelopmentContext, 
                             processing_time: float) -> IntelligentResponse:
        """Parse Claude's response into structured format"""
        
        lines = content.strip().split('\n')
        response_type = "message"
        response_content = content
        reasoning = "General development assistance"
        actions = []
        
        # Parse structured response if provided
        for line in lines:
            if line.startswith("Type:"):
                response_type = line.split(":", 1)[1].strip().lower()
            elif line.startswith("Content:"):
                response_content = line.split(":", 1)[1].strip()
            elif line.startswith("Reasoning:"):
                reasoning = line.split(":", 1)[1].strip()
            elif line.startswith("Actions:"):
                actions = [a.strip() for a in line.split(":", 1)[1].split(",")]
                
        return IntelligentResponse(
            response_type=response_type,
            content=response_content,
            confidence=0.85,  # Claude is generally high confidence
            reasoning=reasoning,
            suggested_actions=actions,
            context_used=[context.current_buffer, context.buffer_type],
            model_used="claude-3.5-sonnet",
            processing_time=processing_time
        )
        
    def _fallback_response(self, context: DevelopmentContext, 
                         user_intent: str) -> IntelligentResponse:
        """Fallback response when Claude is unavailable"""
        return IntelligentResponse(
            response_type="message",
            content=f"I see you're working in {context.current_buffer}. Claude API unavailable - using fallback intelligence.",
            confidence=0.3,
            reasoning="Fallback due to API unavailability",
            suggested_actions=["Check API key", "Continue development"],
            context_used=[context.current_buffer],
            model_used="fallback",
            processing_time=0.001
        )
        
    def get_model_name(self) -> str:
        return "claude-3.5-sonnet"

class OpenAIProvider(AIProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key and OPENAI_AVAILABLE:
            print("⚠️ OPENAI_API_KEY not set - OpenAI provider disabled")
            
        self.client = None
        if self.api_key and OPENAI_AVAILABLE:
            self.client = openai.OpenAI(api_key=self.api_key)
            
    async def generate_response(self, context: DevelopmentContext, 
                              user_intent: str, patterns: List[Dict]) -> IntelligentResponse:
        if not self.client:
            return self._fallback_response(context, user_intent)
            
        start_time = time.time()
        
        # Build development-focused prompt
        prompt = self._build_gpt_prompt(context, user_intent, patterns)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert development assistant integrated into Emacs. Provide context-aware, actionable development assistance."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            processing_time = time.time() - start_time
            
            return self._parse_gpt_response(content, context, processing_time)
            
        except Exception as e:
            print(f"🚨 OpenAI API error: {e}")
            return self._fallback_response(context, user_intent)
            
        
        
    def _fallback_response(self, context: DevelopmentContext, 
                         user_intent: str) -> IntelligentResponse:
        """Fallback when OpenAI unavailable"""
        return IntelligentResponse(
            response_type="message",
            content=f"Working in {context.current_buffer}. OpenAI unavailable - continuing with pattern analysis.",
            confidence=0.2,
            reasoning="OpenAI API unavailable",
            suggested_actions=["Check configuration"],
            context_used=[context.current_buffer],
            model_used="fallback",
            processing_time=0.001
        )
        
    def get_model_name(self) -> str:
        return "gpt-4-turbo"

class LocalModelProvider(AIProvider):
    """Local model provider (Ollama, etc.)"""
    
    def __init__(self, model_name: str = "codellama"):
        self.model_name = model_name
        self.available = self._check_availability()
        
            
    async def generate_response(self, context: DevelopmentContext, 
                              user_intent: str, patterns: List[Dict]) -> IntelligentResponse:
        if not self.available:
            return self._fallback_response(context, user_intent)
            
        start_time = time.time()
        
        # Use local model for code-specific tasks
        prompt = f"Code context: {context.current_buffer}\nUser intent: {user_intent}\nProvide brief, practical coding assistance."
        
        try:
            result = subprocess.run([
                'ollama', 'run', self.model_name, prompt
            ], capture_output=True, text=True, timeout=10)
            
            processing_time = time.time() - start_time
            
            return IntelligentResponse(
                response_type="message",
                content=result.stdout.strip() or "Local model response unavailable",
                confidence=0.6,
                reasoning=f"Local {self.model_name} analysis",
                suggested_actions=["Review code", "Continue development"],
                context_used=[context.current_buffer],
                model_used=self.model_name,
                processing_time=processing_time
            )
            
        except Exception as e:
            print(f"🚨 Local model error: {e}")
            return self._fallback_response(context, user_intent)
            
        
    def get_model_name(self) -> str:
        return self.model_name

class ContextBuilder:
    """Builds rich development context from facade data"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
    def build_context(self, facade_data: Dict[str, Any], 
                     recent_patterns: List[Dict]) -> DevelopmentContext:
        """Build comprehensive development context"""
        
        current_buffer = facade_data.get('current_buffer', 'unknown')
        buffer_type = self._classify_buffer_type(current_buffer)
        
        # Try to detect project root
        project_root = self._detect_project_root(current_buffer)
        
        # Get git info
        git_branch = self._get_git_branch(project_root)
        
        # Build cursor context (would normally read from buffer)
        cursor_context = self._get_cursor_context(facade_data)
        
        # Get recent activity
        recent_commands = facade_data.get('recent_commands', [facade_data.get('last_command', 'none')])
        
        return DevelopmentContext(
            current_buffer=current_buffer,
            buffer_type=buffer_type,
            project_root=project_root,
            git_branch=git_branch,
            recent_files=self._get_recent_files(),
            cursor_context=cursor_context,
            recent_commands=recent_commands,
            active_modes=facade_data.get('minor_modes', []),
            project_files=self._get_project_files(project_root),
            error_messages=self._get_recent_errors(),
            test_status=None,
            build_status=None
        )
        
            
        
            
        
        
            

class IntelligentResponseEngine:
    """Main engine that coordinates multiple AI providers"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.context_builder = ContextBuilder(redis_client)
        
        # Initialize AI providers
        self.providers = {
            'claude': ClaudeProvider(),
            'openai': OpenAIProvider(),
            'local': LocalModelProvider()
        }
        
        # Provider selection strategy
        self.primary_provider = 'claude'
        self.fallback_providers = ['openai', 'local']
        
        # Response cache
        self.response_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def generate_intelligent_response(self, facade_data: Dict[str, Any], 
                                          user_intent: str, 
                                          learned_patterns: List[Dict]) -> IntelligentResponse:
        """Generate intelligent response using best available AI"""
        
        # Build rich context
        context = self.context_builder.build_context(facade_data, learned_patterns)
        
        # Check cache first
        cache_key = self._build_cache_key(context, user_intent)
        cached_response = self._get_cached_response(cache_key)
        
        if cached_response:
            return cached_response
            
        # Try providers in order of preference
        providers_to_try = [self.primary_provider] + self.fallback_providers
        
        for provider_name in providers_to_try:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
                
            try:
                print(f"🧠 Generating response with {provider.get_model_name()}...")
                
                response = await provider.generate_response(
                    context, user_intent, learned_patterns
                )
                
                # Cache successful response
                self._cache_response(cache_key, response)
                
                print(f"✅ Generated intelligent response: {response.content[:100]}...")
                
                return response
                
            except Exception as e:
                print(f"🚨 Provider {provider_name} failed: {e}")
                continue
                
        # All providers failed - return fallback
        return IntelligentResponse(
            response_type="message",
            content="Intelligent response unavailable - all AI providers failed",
            confidence=0.0,
            reasoning="All AI providers unavailable",
            suggested_actions=["Check configuration", "Continue manually"],
            context_used=[context.current_buffer],
            model_used="none",
            processing_time=0.001
        )
        
        
        
        
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all AI providers"""
        status = {}
        
        for name, provider in self.providers.items():
            if hasattr(provider, 'client') and provider.client:
                status[name] = {'available': True, 'model': provider.get_model_name()}
            elif hasattr(provider, 'available') and provider.available:
                status[name] = {'available': True, 'model': provider.get_model_name()}
            else:
                status[name] = {'available': False, 'model': provider.get_model_name()}
                
        return status

async def demo_intelligent_responses():
    """Demo the intelligent response engine"""
    print("🧠 INTELLIGENT RESPONSE ENGINE DEMO")
    print("=" * 45)
    
    # Setup
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    engine = IntelligentResponseEngine(redis_client)
    
    # Show provider status
    status = engine.get_provider_status()
    print("🤖 AI Provider Status:")
    for name, info in status.items():
        icon = "✅" if info['available'] else "❌"
        print(f"   {icon} {name}: {info['model']}")
        
    # Test scenarios
    test_scenarios = [
        {
            'facade_data': {
                'current_buffer': 'main.py',
                'cursor_line': 45,
                'cursor_column': 12,
                'last_command': 'self-insert-command',
                'minor_modes': ['python-mode', 'flycheck-mode']
            },
            'user_intent': 'User is writing Python code and just typed something',
            'patterns': [{'description': 'User often writes functions after imports', 'confidence': 0.8}]
        },
        {
            'facade_data': {
                'current_buffer': 'README.md',
                'cursor_line': 1,
                'cursor_column': 1,
                'last_command': 'switch-to-buffer',
                'minor_modes': ['markdown-mode']
            },
            'user_intent': 'User switched to documentation file',
            'patterns': [{'description': 'User writes docs after coding', 'confidence': 0.7}]
        }
    ]
    
    print(f"\n🧪 Testing intelligent responses...")
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n--- Test {i}: {scenario['user_intent']} ---")
        
        try:
            response = await engine.generate_intelligent_response(
                scenario['facade_data'],
                scenario['user_intent'], 
                scenario['patterns']
            )
            
            print(f"📝 Response: {response.content}")
            print(f"🎯 Confidence: {response.confidence:.2f}")
            print(f"🤔 Reasoning: {response.reasoning}")
            print(f"🚀 Suggested actions: {', '.join(response.suggested_actions)}")
            print(f"⚡ Model: {response.model_used} ({response.processing_time:.3f}s)")
            
        except Exception as e:
            print(f"🚨 Error: {e}")
            
    print(f"\n✅ Intelligent response engine demo complete")

if __name__ == "__main__":
    asyncio.run(demo_intelligent_responses())