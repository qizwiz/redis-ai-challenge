#!/usr/bin/env python3
"""
Ollama AI Conversation System  
Using your local Ollama models for completely free AI conversation
"""

import sys
import json
import requests
from typing import Dict, Any, List

sys.path.append('/Users/jonathanhill/src/redis-ai-challenge')

from redis_ai_patterns.homoiconic import HomoiconicRedis

class OllamaAIConversation:
    """
    Free AI conversation using local Ollama models
    """
    
    def __init__(self):
        self.redis_lisp = HomoiconicRedis()
        self.ollama_url = "http://localhost:11434"
        self.available_models = self.get_available_models()
        
    def get_available_models(self) -> List[str]:
        """Get available Ollama models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except:
            return []
    
    def call_ollama(self, prompt: str, model: str = "llama3.1:8b") -> str:
        """Call local Ollama model"""
        try:
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "max_tokens": 200
                }
            }
            
            response = requests.post(f"{self.ollama_url}/api/generate", json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                return f"[Ollama error {response.status_code}]"
                
        except Exception as e:
            return f"[Ollama exception: {e}]"
    
    def generate_ai_response(self, context: str, persona_data: Dict[str, Any], previous_responses: List[str] = None) -> str:
        """Generate AI response using Ollama"""
        
        name = persona_data['name']
        personality = ', '.join(persona_data['personality'])
        knowledge = ', '.join(persona_data['knowledge'])
        
        # Build context-aware prompt
        prompt_parts = [
            f"You are {name}, an AI with these personality traits: {personality}.",
            f"Your areas of knowledge include: {knowledge}.",
            f"",
            f"Context: {context}",
        ]
        
        if previous_responses:
            prompt_parts.append("\nPrevious conversation:")
            for i, resp in enumerate(previous_responses[-2:]):  # Last 2 responses
                speaker = "Other" if i % 2 == 0 else "You"
                prompt_parts.append(f"{speaker}: {resp}")
        
        prompt_parts.extend([
            "",
            f"Respond authentically as {name}. Be genuine, specific, and engaging.",
            f"Keep your response to 2-3 sentences.",
            f"",
            f"{name}:"
        ])
        
        full_prompt = "\n".join(prompt_parts)
        
        # Use best available model
        model = "llama3.1:8b" if "llama3.1:8b" in self.available_models else self.available_models[0]
        
        response = self.call_ollama(full_prompt, model)
        
        # Clean up response
        if response.startswith(f"{name}:"):
            response = response[len(f"{name}:"):].strip()
        
        return response

def main():
    print("🦙 OLLAMA AI CONVERSATION SYSTEM")
    print("🆓 Completely free local AI - no API keys needed")
    print("=" * 60)
    
    # Initialize Ollama conversation system
    ai_conv = OllamaAIConversation()
    
    print(f"✅ Available Ollama models: {', '.join(ai_conv.available_models)}")
    
    # Setup conversation using homoiconic Redis
    print("\n🧠 Setting up personas via homoiconic Redis:")
    
    maya_data = {
        'name': 'Maya',
        'personality': ['curious', 'philosophical', 'empathetic', 'questioning'],
        'knowledge': ['consciousness', 'phenomenology', 'ethics', 'emergence']
    }
    
    zion_data = {
        'name': 'Zion',
        'personality': ['analytical', 'precise', 'systems-focused', 'pragmatic'],
        'knowledge': ['architecture', 'optimization', 'distributed-systems', 'engineering']
    }
    
    ai_conv.redis_lisp.execute(['redis-set', 'maya-persona', maya_data])
    ai_conv.redis_lisp.execute(['redis-set', 'zion-persona', zion_data])
    
    topic = "What distinguishes genuinely unscripted AI conversation from sophisticated choreography?"
    ai_conv.redis_lisp.execute(['redis-set', 'conversation-topic', topic])
    
    print("✅ Personas and topic stored in Redis")
    
    # Generate real AI conversation using Ollama
    print(f"\n💬 Generating REAL AI Conversation with Ollama:")
    print(f"📝 Topic: {topic}")
    print(f"🤖 Model: {ai_conv.available_models[0] if ai_conv.available_models else 'None'}")
    
    conversation_log = []
    previous_responses = []
    
    for turn in range(4):  # 4 turns for deeper conversation
        speaker_key = 'maya-persona' if turn % 2 == 0 else 'zion-persona'
        speaker_data = ai_conv.redis_lisp.execute(['redis-get', speaker_key])
        
        print(f"\n🎭 Turn {turn + 1} - {speaker_data['name']} (via Ollama):")
        print("   🤔 Thinking...", end="", flush=True)
        
        # Generate genuine AI response using Ollama
        ai_response = ai_conv.generate_ai_response(topic, speaker_data, previous_responses)
        
        print(f"\r   💬 {speaker_data['name']}: {ai_response}")
        
        # Store response and update conversation state
        turn_data = {
            'turn': turn + 1,
            'speaker': speaker_data['name'],
            'personality': speaker_data['personality'],
            'response': ai_response,
            'model_used': ai_conv.available_models[0] if ai_conv.available_models else 'unknown'
        }
        
        conversation_log.append(turn_data)
        previous_responses.append(ai_response)
        
        # Store in Redis via homoiconic execution
        ai_conv.redis_lisp.execute(['redis-set', f'conversation-turn-{turn+1}', turn_data])
    
    # Analyze conversation with Ollama
    print(f"\n🧠 Analyzing conversation with Ollama...")
    
    analysis_prompt = f"""
    Analyze this AI conversation about "{topic}":
    
    {chr(10).join([f"{log['speaker']}: {log['response']}" for log in conversation_log])}
    
    Was this conversation genuinely unscripted? What made it authentic or choreographed?
    Give a brief, honest analysis in 2-3 sentences.
    """
    
    analysis = ai_conv.call_ollama(analysis_prompt)
    print(f"📊 Ollama Analysis: {analysis}")
    
    # Store final results
    conversation_summary = {
        'topic': topic,
        'participants': ['Maya', 'Zion'],
        'turns': len(conversation_log),
        'ai_provider': 'ollama_local',
        'models_used': ai_conv.available_models,
        'architecture': 'homoiconic_redis_coordination',
        'analysis': analysis,
        'status': 'completed',
        'cost': 'completely_free'
    }
    
    ai_conv.redis_lisp.execute(['redis-set', 'final-conversation', conversation_summary])
    
    print(f"\n🎯 FREE AI Conversation Complete:")
    print(f"   💰 Cost: $0.00 (completely free)")
    print(f"   🤖 AI Model: Local Ollama")
    print(f"   🧠 Coordination: Homoiconic Redis")
    print(f"   🔄 Turns: {len(conversation_log)}")
    print(f"   📊 Analysis: Generated by AI")
    
    return conversation_summary

if __name__ == "__main__":
    result = main()
    print(f"\n✅ Success: {json.dumps({'status': result['status'], 'cost': result['cost']}, indent=2)}")