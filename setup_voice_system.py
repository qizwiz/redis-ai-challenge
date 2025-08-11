#!/usr/bin/env python3
"""
Setup Voice Learning System - Install dependencies and configure Azure
"""

import subprocess
import sys
import os


def install_dependencies():
    """Install required packages"""

    print("📦 Installing voice system dependencies...")

    packages = ["SpeechRecognition", "pyttsx3", "pyaudio", "openai"]

    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True,
                capture_output=True,
            )
            print(f"✅ {package} installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            if package == "pyaudio":
                print("💡 On macOS, try: brew install portaudio")
                print("💡 Then: pip install pyaudio")


def check_azure_config():
    """Check Azure OpenAI configuration"""

    print("\n🔧 Checking Azure OpenAI configuration...")

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    if not api_key:
        print("❌ AZURE_OPENAI_API_KEY not set")
        print("💡 Set it with: export AZURE_OPENAI_API_KEY='your-key'")
        print(
            "💡 Get it from: https://portal.azure.com → Azure OpenAI → Keys and Endpoint"
        )
    else:
        print("✅ AZURE_OPENAI_API_KEY is set")

    if not endpoint:
        print("❌ AZURE_OPENAI_ENDPOINT not set")
        print(
            "💡 Set it with: export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'"
        )
        print(
            "💡 Get it from: https://portal.azure.com → Azure OpenAI → Keys and Endpoint"
        )
    else:
        print("✅ AZURE_OPENAI_ENDPOINT is set")

    return bool(api_key and endpoint)


def check_microphone():
    """Check microphone availability"""

    print("\n🎤 Checking microphone...")

    try:
        import speech_recognition as sr

        r = sr.Recognizer()
        mic_list = sr.Microphone.list_microphone_names()

        print(f"✅ Found {len(mic_list)} microphones:")
        for i, name in enumerate(mic_list[:3]):  # Show first 3
            print(f"   {i}: {name}")

        return True

    except ImportError:
        print("❌ speech_recognition not installed")
        return False
    except Exception as e:
        print(f"❌ Microphone error: {e}")
        return False


def check_ollama():
    """Check Ollama availability"""

    print("\n🤖 Checking Ollama...")

    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=3)

        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama running with {len(models)} models")

            # Check for llama3.1
            llama_models = [m for m in models if "llama3.1" in m.get("name", "")]
            if llama_models:
                print(f"✅ Found llama3.1 model: {llama_models[0]['name']}")
            else:
                print("⚠️  No llama3.1 model found")
                print("💡 Install with: ollama pull llama3.1")

            return True
        else:
            print("❌ Ollama not responding")
            return False

    except Exception as e:
        print(f"❌ Ollama check failed: {e}")
        print("💡 Start Ollama with: ollama serve")
        return False


def check_emacs():
    """Check Emacs server availability"""

    print("\n📝 Checking Emacs...")

    try:
        # Check if Emacs is running
        result = subprocess.run(["pgrep", "emacs"], capture_output=True, text=True)
        emacs_running = result.returncode == 0

        if emacs_running:
            print("✅ Emacs is running")

            # Check if server is ready
            result = subprocess.run(
                ["emacsclient", "--eval", '(message "Voice system check")'],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                print("✅ Emacs server is ready")
                return True
            else:
                print("⚠️  Emacs server not ready")
                print("💡 In Emacs, run: M-x server-start")
                return False
        else:
            print("⚠️  Emacs not running")
            print("💡 Start with: emacs &")
            print("💡 Then in Emacs: M-x server-start")
            return False

    except Exception as e:
        print(f"❌ Emacs check failed: {e}")
        return False


def main():
    """Setup voice learning system"""

    print("🎤 VOICE LEARNING SYSTEM SETUP")
    print("=" * 50)

    # Install dependencies
    install_dependencies()

    # Check all components
    azure_ok = check_azure_config()
    mic_ok = check_microphone()
    ollama_ok = check_ollama()
    emacs_ok = check_emacs()

    # Summary
    print("\n" + "=" * 50)
    print("📊 SETUP SUMMARY")
    print("=" * 50)
    print(f"Azure OpenAI: {'✅' if azure_ok else '❌'}")
    print(f"Microphone: {'✅' if mic_ok else '❌'}")
    print(f"Ollama: {'✅' if ollama_ok else '❌'}")
    print(f"Emacs: {'✅' if emacs_ok else '⚠️ '}")

    if azure_ok and mic_ok and ollama_ok:
        print("\n🎉 READY TO RUN!")
        print("Run: python voice_learning_system.py")

        if not emacs_ok:
            print("💡 Voice system will work without Emacs (simulation mode)")
    else:
        print("\n❌ SETUP INCOMPLETE")
        print("Fix the issues above and run setup again")

    print(f"\n🔗 NEXT STEPS:")
    print("1. Fix any ❌ issues above")
    print("2. Run: python voice_learning_system.py")
    print("3. Say commands like 'move cursor forward' or 'save file'")
    print("4. Correct the AI when it's wrong to teach it")


if __name__ == "__main__":
    main()
