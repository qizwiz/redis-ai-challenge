#!/usr/bin/env python3
"""
Setup Free AI Resources for Voice Conversation
Configure Azure, Ollama, or Hugging Face for free AI responses
"""

import os
import subprocess
import requests

def check_ollama():
    """Check if Ollama is installed and running"""
    print("🦙 Checking Ollama (completely free local AI)...")
    
    try:
        # Check if ollama command exists
        result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Ollama not installed")
            print("🔧 To install Ollama (free):")
            print("   curl -fsSL https://ollama.ai/install.sh | sh")
            return False
        
        # Check if ollama is running
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                print(f"✅ Ollama running with {len(models)} models")
                for model in models[:3]:  # Show first 3 models
                    print(f"   • {model['name']}")
                return True
            else:
                print("❌ Ollama not responding")
                print("🔧 Start with: ollama serve")
                return False
        except:
            print("❌ Ollama not running")
            print("🔧 Start with: ollama serve")
            print("🔧 Then install a model: ollama pull llama2:7b")
            return False
            
    except Exception as e:
        print(f"❌ Ollama check failed: {e}")
        return False

def check_azure():
    """Check Azure OpenAI configuration"""
    print("\n🌐 Checking Azure OpenAI (has free tier)...")
    
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    key = os.getenv('AZURE_OPENAI_API_KEY')
    
    if not endpoint or not key:
        print("❌ Azure not configured")
        print("🔧 To setup Azure OpenAI (free tier available):")
        print("   1. Go to https://azure.microsoft.com/free/")
        print("   2. Create free Azure account ($200 free credits)")
        print("   3. Create Azure OpenAI resource")
        print("   4. Set environment variables:")
        print("      export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        print("      export AZURE_OPENAI_API_KEY='your-api-key'")
        return False
    else:
        print(f"✅ Azure endpoint configured: {endpoint[:30]}...")
        # Test connection
        try:
            headers = {'api-key': key}
            test_url = f"{endpoint}/openai/models?api-version=2024-02-15-preview"
            response = requests.get(test_url, headers=headers, timeout=10)
            if response.status_code == 200:
                print("✅ Azure connection working")
                return True
            else:
                print(f"❌ Azure connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Azure test failed: {e}")
            return False

def check_huggingface():
    """Check Hugging Face setup"""
    print("\n🤗 Checking Hugging Face (free tier available)...")
    
    token = os.getenv('HUGGINGFACE_TOKEN')
    
    if not token:
        print("❌ Hugging Face token not set")
        print("🔧 To setup Hugging Face (free):")
        print("   1. Go to https://huggingface.co/settings/tokens")
        print("   2. Create free account and generate token")
        print("   3. Set: export HUGGINGFACE_TOKEN='your-token'")
        return False
    else:
        print("✅ Hugging Face token configured")
        # Test API
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get("https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium", 
                                  headers=headers, timeout=10)
            if response.status_code == 200:
                print("✅ Hugging Face API working")
                return True
            else:
                print(f"❌ HF API test failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ HF test failed: {e}")
            return False

def setup_local_transformers():
    """Setup local Hugging Face Transformers"""
    print("\n🤖 Setting up local Transformers (completely free)...")
    
    try:
        import transformers
        print("✅ Transformers already installed")
        return True
    except ImportError:
        print("❌ Transformers not installed")
        print("🔧 Installing local Transformers:")
        print("   pip install transformers torch")
        
        try:
            subprocess.run([
                'pip', 'install', 'transformers', 'torch', '--quiet'
            ], check=True)
            print("✅ Transformers installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install Transformers")
            return False

def main():
    print("🆓 FREE AI RESOURCES SETUP")
    print("🎯 Configure free AI for voice conversation")
    print("=" * 50)
    
    # Check all options
    ollama_ok = check_ollama()
    azure_ok = check_azure()
    hf_ok = check_huggingface()
    transformers_ok = setup_local_transformers()
    
    print(f"\n📊 Summary:")
    print(f"   Ollama (local): {'✅' if ollama_ok else '❌'}")
    print(f"   Azure OpenAI: {'✅' if azure_ok else '❌'}")
    print(f"   Hugging Face API: {'✅' if hf_ok else '❌'}")
    print(f"   Local Transformers: {'✅' if transformers_ok else '❌'}")
    
    if ollama_ok:
        print(f"\n🎯 READY: Use Ollama for completely free local AI")
        print(f"   • No API keys needed")
        print(f"   • Runs entirely on your machine")
        print(f"   • Multiple models available")
        
    elif azure_ok:
        print(f"\n🎯 READY: Use Azure OpenAI")
        print(f"   • Free tier includes $200 credits")
        print(f"   • High quality responses")
        print(f"   • Same API as OpenAI")
        
    elif hf_ok:
        print(f"\n🎯 READY: Use Hugging Face Inference API")
        print(f"   • Free tier available")
        print(f"   • Multiple models")
        print(f"   • Cloud-based")
        
    elif transformers_ok:
        print(f"\n🎯 READY: Use local Transformers")
        print(f"   • Completely free")
        print(f"   • No network needed")
        print(f"   • Download models once")
        
    else:
        print(f"\n❌ No AI resources configured")
        print(f"🔧 Easiest options:")
        print(f"   1. Install Ollama (completely free)")
        print(f"   2. Get Azure free account ($200 credits)")
        print(f"   3. Create HuggingFace account (free tier)")
    
    return {
        'ollama': ollama_ok,
        'azure': azure_ok, 
        'huggingface': hf_ok,
        'transformers': transformers_ok
    }

if __name__ == "__main__":
    result = main()