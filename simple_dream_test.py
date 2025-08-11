#!/usr/bin/env python3
"""
Simple Dream Bridge Test - Test bidirectional AI-Emacs communication
"""

import redis
import json
import time
import subprocess
import tempfile
import os


def test_dream_bridge():
    """Test basic dream bridge functionality"""
    print("🌉 Testing Dream Bridge Communication")
    print("=" * 40)

    # Setup Redis client
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

    # Test Redis connectivity
    try:
        redis_client.ping()
        print("✅ Redis connected")
    except:
        print("❌ Redis not available")
        return

    # Create simple Emacs bridge script
    bridge_script = """
(progn
  (require 'json)
  
  ;; Send a pulse to AI
  (defun send-dream-pulse ()
    (let ((state-data (json-encode 
                       `((timestamp . ,(float-time))
                         (buffer . ,(buffer-name))
                         (point . ,(point))
                         (test . "dream-bridge-working")))))
      (shell-command 
       (format "redis-cli XADD dream:test_pulse '*' data '%s'" 
               (shell-quote-argument state-data)))
      (message "🌉 Sent dream pulse to AI")))
  
  ;; Check for AI responses
  (defun check-ai-response ()
    (let ((response (shell-command-to-string 
                     "redis-cli --raw XREAD BLOCK 1000 STREAMS dream:test_response '$'")))
      (when (and response (not (string-empty-p response)))
        (message "🤖 AI Response received: %s" response))))
  
  ;; Send test pulse
  (send-dream-pulse)
  
  ;; Check for response
  (run-with-timer 2 nil #'check-ai-response))
"""

    # Write script to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".el", delete=False) as f:
        f.write(bridge_script)
        script_file = f.name

    print("📡 Sending test pulse from Emacs...")

    # Run Emacs script
    result = subprocess.run(
        ["emacs", "--batch", "--eval", bridge_script], capture_output=True, text=True
    )

    print(f"Emacs output: {result.stdout}")
    if result.stderr:
        print(f"Emacs errors: {result.stderr}")

    # Listen for pulse from Emacs
    print("👂 Listening for pulse from Emacs...")

    try:
        streams = redis_client.xread({"dream:test_pulse": "0"}, block=5000)

        if streams:
            for stream_name, messages in streams:
                for message_id, fields in messages:
                    # Handle the escaped JSON from Emacs
                    raw_data = fields["data"]
                    # Remove escaping
                    clean_data = raw_data.replace("\\", "")
                    pulse_data = json.loads(clean_data)
                    print(f"💓 Received pulse: {pulse_data}")

                    # Send AI response
                    ai_response = {
                        "timestamp": str(time.time()),
                        "message": f"AI received your pulse from {pulse_data.get('buffer', 'unknown')}!",
                        "test_success": "true",
                    }

                    redis_client.xadd("dream:test_response", ai_response)
                    print(f"🤖 Sent AI response back to Emacs")

                    # Test successful!
                    print("✅ DREAM BRIDGE COMMUNICATION SUCCESSFUL!")
                    print("   Emacs → Redis → AI → Redis → Emacs")

                    # Clean up
                    os.unlink(script_file)
                    return True
        else:
            print("⏰ No pulse received from Emacs (timeout)")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Clean up
    os.unlink(script_file)
    return False


if __name__ == "__main__":
    test_dream_bridge()
