#!/bin/bash

# Simple Precise Targeting - Direct Approach

send_to_this_session() {
    local message="$1"
    
    # Get current session details for verification
    local current_session=$(osascript -e 'tell application "iTerm2" to get name of current session of current tab of current window')
    echo "🎯 Current session: $current_session"
    
    # Write message and send directly to current session
    echo "$message" > /tmp/direct_message.txt
    pbcopy < /tmp/direct_message.txt
    
    # Send directly without window switching
    osascript -e 'tell application "System Events" to keystroke "v" using command down'
    osascript -e 'tell application "System Events" to keystroke return'
    
    rm -f /tmp/direct_message.txt
    
    # Log the targeting
    redis-cli XADD facade:realtime '*' \
        action "direct_session_targeting" \
        session "$current_session" \
        message_sent "true" \
        timestamp "$(date +%s)"
    
    echo "✅ Message sent to session: $current_session"
}

# Test direct targeting
test_direct() {
    echo "🧪 Testing direct session targeting..."
    send_to_this_session "DIRECT TARGETING TEST: This should appear in our conversation!"
    sleep 1
    send_to_this_session "Second test: Direct targeting architecture working!"
}

case "$1" in
    "send") send_to_this_session "$2" ;;
    "test") test_direct ;;
    *) echo "Usage: $0 {send MESSAGE|test}" ;;
esac