#!/bin/bash

# Safe AI Communication Protocol - No Accidental Messages!

TARGET_APP="iTerm2"
TARGET_TAB="✳ Code Abstraction (python)"

safe_type() {
    local message="$1"
    
    # Verify frontmost application
    local current_app=$(./dynamic_facade_controller.sh frontmost)
    
    # Get current iTerm2 tab name
    local current_tab=$(osascript -e 'tell application "iTerm2" to tell current session of current window to get name' 2>/dev/null)
    
    # Only send keystrokes if we're in the right place
    if [[ "$current_app" == "$TARGET_APP" && "$current_tab" == "$TARGET_TAB" ]]; then
        osascript -e "tell application \"System Events\" to keystroke \"$message\""
        redis-cli XADD facade:realtime '*' action "safe_message_sent" \
            target_app "$TARGET_APP" target_tab "$TARGET_TAB" \
            message "$message" timestamp "$(date +%s)"
        echo "✅ Safe message sent to correct target"
    else
        redis-cli XADD facade:realtime '*' action "unsafe_message_blocked" \
            current_app "$current_app" current_tab "$current_tab" \
            target_app "$TARGET_APP" target_tab "$TARGET_TAB" \
            blocked_message "$message" timestamp "$(date +%s)"
        echo "❌ Message blocked - wrong target (app: $current_app, tab: $current_tab)"
    fi
}

case "$1" in
    "test")
        safe_type "Testing safe communication protocol"
        ;;
    "send")
        safe_type "$2"
        ;;
    "check")
        current_app=$(./dynamic_facade_controller.sh frontmost)
        current_tab=$(osascript -e 'tell application "iTerm2" to tell current session of current window to get name' 2>/dev/null)
        echo "Current: $current_app / $current_tab"
        echo "Target:  $TARGET_APP / $TARGET_TAB"
        if [[ "$current_app" == "$TARGET_APP" && "$current_tab" == "$TARGET_TAB" ]]; then
            echo "✅ Safe to communicate"
        else
            echo "❌ Unsafe - wrong target"
        fi
        ;;
    *)
        echo "Safe AI Communication Protocol"
        echo "Usage: $0 {test|send MESSAGE|check}"
        echo ""
        echo "Commands:"
        echo "  test           - Send test message if target is correct"
        echo "  send MESSAGE   - Send message only to verified target"
        echo "  check          - Verify current vs target app/tab"
        ;;
esac