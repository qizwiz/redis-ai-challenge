#!/usr/bin/env python3
"""
Azure AI Voice Conversation Setup
Guide to configure your Azure resources for free AI conversation
"""

import os
import sys
import json
import requests
from pathlib import Path

sys.path.append('/Users/jonathanhill/src/redis-ai-challenge')
from redis_ai_patterns.homoiconic import HomoiconicRedis

class AzureVoiceConversation:
    """Setup and use Azure OpenAI for free AI conversation"""
    
    def __init__(self):
        self.redis_lisp = HomoiconicRedis()
        self.check_azure_config()
    
    def check_azure_config(self):
        """Check if Azure is configured"""
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.key = os.getenv('AZURE_OPENAI_API_KEY')
        self.deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini')
        
        print("🌐 Azure OpenAI Configuration Check:")
        print(f"   Endpoint: {'✅ Set' if self.endpoint else '❌ Missing'}")
        print(f"   API Key: {'✅ Set' if self.key else '❌ Missing'}")
        print(f"   Deployment: {self.deployment}")
        
        if not self.endpoint or not self.key:
            self.show_setup_instructions()
            return False
        return True
    
    def show_setup_instructions(self):
        """Show Azure setup instructions"""
        print("\n🔧 AZURE OPENAI SETUP (FREE $200 CREDITS):")
        print("=" * 50)
        
        print("1. Create free Azure account:")
        print("   → https://azure.microsoft.com/free/")
        print("   → Get $200 free credits (no card required initially)")
        
        print("\n2. Create Azure OpenAI resource:")
        print("   → Go to Azure Portal")
        print("   → Search 'Azure OpenAI'")
        print("   → Create new resource")
        print("   → Choose region (East US, West Europe work well)")
        
        print("\n3. Deploy a model:")
        print("   → Go to your Azure OpenAI resource")
        print("   → Click 'Model deployments'")  
        print("   → Deploy 'gpt-4o-mini' (cheapest, most efficient)")
        print("   → Note your deployment name")
        
        print("\n4. Get your keys:")
        print("   → Go to 'Keys and Endpoint'")
        print("   → Copy 'Endpoint' and 'KEY 1'")
        
        print("\n5. Set environment variables:")
        azure_commands = [
            "export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'",
            "export AZURE_OPENAI_API_KEY='your-api-key-here'",
            "export AZURE_OPENAI_DEPLOYMENT='gpt-4o-mini'  # or your deployment name"
        ]
        
        for cmd in azure_commands:
            print(f"   {cmd}")
        
        print("\n6. Add to your shell profile:")
        print("   echo 'export AZURE_OPENAI_ENDPOINT=...' >> ~/.zshrc")
        print("   echo 'export AZURE_OPENAI_API_KEY=...' >> ~/.zshrc")
        print("   source ~/.zshrc")
        
        print("\n💰 Cost estimate with free credits:")
        print("   • gpt-4o-mini: ~$0.15 per 1M input tokens")
        print("   • With $200 credits = ~1.3 billion tokens")
        print("   • Thousands of conversations possible")
    
    def test_azure_connection(self) -> bool:
        """Test Azure OpenAI connection"""
        if not self.endpoint or not self.key:
            return False
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'api-key': self.key
            }
            
            # Test with simple completion
            data = {
                'messages': [{'role': 'user', 'content': 'Hello, test message'}],
                'max_tokens': 10
            }
            
            url = f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version=2024-02-15-preview"
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                print("✅ Azure OpenAI connection successful!")
                return True
            else:
                print(f"❌ Azure test failed: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"❌ Azure connection error: {e}")
            return False
    
    def call_azure_ai(self, prompt: str, persona: str) -> str:
        """Call Azure OpenAI for AI response"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'api-key': self.key
            }
            
            data = {
                'messages': [
                    {'role': 'system', 'content': f'You are {persona}. Respond authentically in 1-2 sentences.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 150,
                'temperature': 0.8
            }
            
            url = f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version=2024-02-15-preview"
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"[Azure error {response.status_code}]"
                
        except Exception as e:
            return f"[Azure exception: {str(e)[:50]}...]"
    
    def run_conversation(self):
        """Run AI conversation using Azure"""
        if not self.check_azure_config():
            print("❌ Azure not configured. Please set up your Azure OpenAI resource first.")
            return None
        
        if not self.test_azure_connection():
            print("❌ Azure connection failed. Check your configuration.")
            return None
        
        print("\n🎤 AZURE AI VOICE CONVERSATION")
        print("💰 Using your free $200 Azure credits")
        print("=" * 50)
        
        # Setup personas
        topic = "What makes AI conversation genuinely unscripted?"
        
        personas = {
            'Maya': 'Maya, a curious philosopher who questions assumptions',
            'Zion': 'Zion, an analytical engineer focused on systems thinking'
        }
        
        conversation = []
        
        print(f"📝 Topic: {topic}")
        print("💬 Starting Azure AI conversation:")
        
        for turn in range(3):
            speaker = 'Maya' if turn % 2 == 0 else 'Zion'
            persona_desc = personas[speaker]
            
            prompt = f"Topic: {topic}\n\nRespond as {persona_desc}:"
            
            print(f"\n🎭 {speaker}: ", end="", flush=True)
            
            response = self.call_azure_ai(prompt, persona_desc)
            
            if not response.startswith('['):
                print(response)
                turn_data = {
                    'speaker': speaker,
                    'response': response,
                    'turn': turn + 1,
                    'model': self.deployment
                }
                conversation.append(turn_data)
                
                # Store in Redis
                self.redis_lisp.execute(['redis-set', f'azure-turn-{turn+1}', turn_data])
            else:
                print(response)
        
        # Summary
        summary = {
            'provider': 'azure_openai',
            'deployment': self.deployment,
            'turns': len(conversation),
            'cost_estimate': len(conversation) * 0.0001,  # Very rough estimate
            'status': 'completed'
        }
        
        self.redis_lisp.execute(['redis-set', 'azure-conversation-summary', summary])
        
        print(f"\n🎯 Azure Conversation Complete:")
        print(f"   💰 Estimated cost: ~${summary['cost_estimate']:.4f}")
        print(f"   🤖 Model: {self.deployment}")
        print(f"   ✅ Turns: {len(conversation)}")
        
        return summary

def main():
    azure_conv = AzureVoiceConversation()
    
    if azure_conv.endpoint and azure_conv.key:
        # Run actual conversation
        result = azure_conv.run_conversation()
        return result
    else:
        # Show setup instructions
        print("\n🎯 Next Steps:")
        print("1. Set up Azure OpenAI (free $200 credits)")
        print("2. Set environment variables")
        print("3. Run this script again")
        return None

if __name__ == "__main__":
    result = main()
    if result:
        print(f"\n✅ Success: {json.dumps(result, indent=2)}")
    else:
        print("\n❌ Setup required - follow the instructions above")