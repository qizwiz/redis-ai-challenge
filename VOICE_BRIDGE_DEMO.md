# Voice-Claude Bridge Usage Demo

## 1. Start Voice Session
```
Tool: start_voice_session
Parameters: {
    "greeting": "Hello! I'm Claude and I'm ready for a voice conversation. What would you like to discuss?",
    "voice": "af_sky",
    "tts_provider": "kokoro"
}
```

## 2. Conversation Loop

### Step A: Claude speaks and listens
```
Tool: converse_step  
Parameters: {
    "claude_response": "That's interesting! Can you tell me more about that?",
    "voice": "af_sky",
    "tts_provider": "kokoro", 
    "listen_duration": 45.0
}
```

This returns instructions to call:
```
Tool: mcp__voice-mode__converse
Parameters: {
    "message": "That's interesting! Can you tell me more about that?",
    "voice": "af_sky",
    "tts_provider": "kokoro",
    "listen_duration": 45.0,
    "wait_for_response": true
}
```

### Step B: Process user response
```
Tool: handle_user_response
Parameters: {
    "user_transcription": "Well, I was thinking about machine learning..."
}
```

### Step C: Repeat with Claude's next response
Continue the loop with `converse_step` → voice call → `handle_user_response`

## 3. End Session
```
Tool: end_voice_session
Parameters: {}
```

## Quick Commands

### Speak Only (no listening)
```
Tool: speak_only
Parameters: {
    "text": "Thank you for the conversation!",
    "voice": "af_sky"
}
```

### Listen Only (no speaking)
```
Tool: listen_only
Parameters: {
    "listen_duration": 30.0
}
```

### Check Status
```
Tool: get_conversation_status
Parameters: {}
```