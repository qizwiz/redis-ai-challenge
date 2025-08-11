#!/usr/bin/env python3
"""
Fast Ollama AI Conversation 
Optimized for quick responses with shorter prompts
"""

import sys
import json
import requests
from typing import Dict, Any

sys.path.append('/Users/jonathanhill/src/redis-ai-challenge')

from redis_ai_patterns.homoiconic import HomoiconicRedis

def quick_ollama_call(prompt: str, model: str = "phi3:mini") -> str:
    """Fast Ollama call with shorter timeout and concise prompt"""
    try:
        data = {
            "model": model,  # phi3:mini is faster than llama3.1:8b
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 100,  # Shorter responses
                "stop": ["\n\n", "Human:", "AI:"]
            }
        }
        
        response = requests.post("http://localhost:11434/api/generate", json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '').strip()
        else:
            return f"[Error {response.status_code}]"
            
    except Exception as e:
        return f"[Timeout/Error]"

def main():
    print("🦙 FAST OLLAMA AI CONVERSATION")
    print("⚡ Optimized for quick responses")
    print("=" * 50)
    
    redis_lisp = HomoiconicRedis()
    
    # Setup simple personas
    topic = "What makes AI conversation unscripted vs scripted?"
    
    personas = {
        'Maya': "You are Maya, a curious philosopher. Respond in 1-2 sentences only.",
        'Zion': "You are Zion, an analytical engineer. Respond in 1-2 sentences only."
    }
    
    print(f"📝 Topic: {topic}")
    print("💬 Starting conversation with phi3:mini (fastest model):")
    
    conversation = []
    previous_response = ""
    
    for turn in range(3):
        speaker = 'Maya' if turn % 2 == 0 else 'Zion'
        persona_prompt = personas[speaker]
        
        # Concise prompt for speed
        if turn == 0:
            prompt = f"{persona_prompt}\n\nTopic: {topic}\n\nYour response:"
        else:
            prompt = f"{persona_prompt}\n\nOther person said: \"{previous_response[:100]}...\"\n\nYour response to that:"
        
        print(f"\n🎭 {speaker}: ", end="", flush=True)
        
        response = quick_ollama_call(prompt, "phi3:mini")
        
        if not response.startswith('['):
            print(response)
            conversation.append({
                'speaker': speaker,
                'response': response,
                'turn': turn + 1
            })
            previous_response = response
            
            # Store in Redis
            redis_lisp.execute(['redis-set', f'turn-{turn+1}', {
                'speaker': speaker,
                'response': response
            }])
        else:
            print(f"⚠️  {response} - using fallback")
            fallback = f"As {speaker}, I think {topic.lower()} requires genuine uncertainty and authentic responses."
            conversation.append({
                'speaker': speaker, 
                'response': fallback,
                'turn': turn + 1
            })
    
    print(f"\n🎯 Conversation Summary:")
    print(f"   💰 Cost: $0.00 (free local AI)")
    print(f"   🤖 Model: phi3:mini via Ollama")
    print(f"   ⚡ Speed: Optimized for quick responses")
    print(f"   🧠 Coordination: Homoiconic Redis")
    
    # Final summary
    summary = {
        'turns': len(conversation),
        'cost': 0,
        'model': 'phi3:mini',
        'architecture': 'ollama_redis_homoiconic',
        'status': 'completed'
    }
    
    redis_lisp.execute(['redis-set', 'conversation-summary', summary])
    
    return summary

if __name__ == "__main__":
    result = main()
    print(f"\n✅ Result: {json.dumps(result, indent=2)}")