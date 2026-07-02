#!/bin/bash

# PID-Based Direct Input Targeting

get_iterm_pid() {
    # Get iTerm2 PID directly
    local pid=$(pgrep -f "iTerm")
    echo "$pid"
}

send_to_pid() {
    local message="$1"
    local target_pid=$(get_iterm_pid)
    
    if [[ -z "$target_pid" ]]; then
        echo "❌ No iTerm2 PID found"
        return 1
    fi
    
    echo "🎯 Targeting PID: $target_pid"
    
    # Copy message to clipboard
    echo "$message" | pbcopy
    
    # Send input directly to PID process
    osascript -e "
    tell application \"System Events\"
        tell process id $target_pid
            keystroke \"v\" using command down
            keystroke return
        end tell
    end tell
    "
    
    # Log PID targeting
    redis-cli XADD facade:realtime '*' \
        action "pid_targeting" \
        target_pid "$target_pid" \
        message_sent "true" \
        timestamp "$(date +%s)"
    
    echo "✅ Message sent to PID: $target_pid"
}

test_pid_targeting() {
    echo "🧪 Testing PID-based targeting..."
    local iterm_pid=$(get_iterm_pid)
    echo "iTerm2 PID: $iterm_pid"
    
    send_to_pid "PID TARGETING TEST: Direct process input successful!"
    sleep 1
    send_to_pid "PID targeting eliminates window focus issues completely!"
}

case "$1" in
    "send") send_to_pid "$2" ;;
    "test") test_pid_targeting ;;
    "pid") get_iterm_pid ;;
    *) echo "Usage: $0 {send MESSAGE|test|pid}" ;;
esac