#!/bin/bash

# Precise Window Targeting Architecture - No More Random Messages!

TARGET_PROCESS="iTerm2"
TARGET_WINDOW_ID=""
TARGET_TAB_ID=""

# Get precise window and tab identification
identify_target_window() {
    echo "🎯 Identifying precise target window..."
    
    # Get all iTerm2 windows and their IDs
    local window_info=$(osascript -e '
    tell application "iTerm2"
        set window_list to {}
        repeat with w from 1 to count of windows
            set window_id to id of window w
            set tab_list to {}
            repeat with t from 1 to count of tabs of window w
                set tab_name to name of session 1 of tab t of window w
                set end of tab_list to ("Tab " & t & ": " & tab_name)
            end repeat
            set end of window_list to ("Window " & w & " (ID: " & window_id & "):" & return & (my join_list(tab_list, return)))
        end repeat
        return my join_list(window_list, return & return)
    end tell
    
    on join_list(lst, delimiter)
        set AppleScript'"'"'s text item delimiters to delimiter
        set joined to lst as string
        set AppleScript'"'"'s text item delimiters to ""
        return joined
    end join_list
    ')
    
    echo "$window_info"
    
    # Find our conversation tab
    local our_tab=$(osascript -e '
    tell application "iTerm2"
        repeat with w from 1 to count of windows
            repeat with t from 1 to count of tabs of window w
                set tab_name to name of session 1 of tab t of window w
                if tab_name contains "Code Abstraction" then
                    return "Window:" & w & ",Tab:" & t & ",ID:" & (id of window w)
                end if
            end repeat
        end repeat
    end tell
    ')
    
    echo "🎯 Found our target: $our_tab"
    
    # Extract window and tab numbers
    TARGET_WINDOW_ID=$(echo "$our_tab" | cut -d',' -f1 | cut -d':' -f2)
    TARGET_TAB_ID=$(echo "$our_tab" | cut -d',' -f2 | cut -d':' -f2)
    
    echo "✅ Target identified: Window $TARGET_WINDOW_ID, Tab $TARGET_TAB_ID"
    
    # Store in Redis for persistence
    redis-cli HSET neuro:targeting window_id "$TARGET_WINDOW_ID" tab_id "$TARGET_TAB_ID" process "$TARGET_PROCESS"
}

# Send message to EXACT target
send_to_exact_target() {
    local message="$1"
    
    # Verify we have targeting info
    if [[ -z "$TARGET_WINDOW_ID" || -z "$TARGET_TAB_ID" ]]; then
        # Load from Redis
        TARGET_WINDOW_ID=$(redis-cli HGET neuro:targeting window_id)
        TARGET_TAB_ID=$(redis-cli HGET neuro:targeting tab_id)
        
        if [[ -z "$TARGET_WINDOW_ID" ]]; then
            echo "❌ No target identified! Run identify_target_window first"
            return 1
        fi
    fi
    
    echo "🎯 Sending to Window $TARGET_WINDOW_ID, Tab $TARGET_TAB_ID"
    
    # Write message to temp file
    echo "$message" > /tmp/precise_message.txt
    pbcopy < /tmp/precise_message.txt
    
    # Send to EXACT window and tab
    osascript -e "
    tell application \"iTerm2\"
        tell window $TARGET_WINDOW_ID
            tell tab $TARGET_TAB_ID
                select
                tell current session
                    write text \"\"
                end tell
            end tell
        end tell
    end tell
    
    delay 0.1
    
    tell application \"System Events\"
        keystroke \"v\" using command down
        keystroke return
    end tell
    "
    
    rm -f /tmp/precise_message.txt
    
    # Log successful targeting
    redis-cli XADD facade:realtime '*' \
        action "precise_targeting_success" \
        window_id "$TARGET_WINDOW_ID" \
        tab_id "$TARGET_TAB_ID" \
        message_length "${#message}" \
        timestamp "$(date +%s)"
    
    echo "✅ Message sent to exact target"
}

# Test the targeting system
test_precise_targeting() {
    echo "🧪 Testing precise window targeting system..."
    
    identify_target_window
    sleep 1
    
    send_to_exact_target "PRECISE TARGETING TEST: This message should go ONLY to our conversation tab!"
    sleep 1
    
    send_to_exact_target "Testing again: Window $TARGET_WINDOW_ID, Tab $TARGET_TAB_ID - no more random messages!"
    
    echo "🎯 Precise targeting test complete"
}

case "$1" in
    "identify") identify_target_window ;;
    "send") send_to_exact_target "$2" ;;
    "test") test_precise_targeting ;;
    *)
        echo "Precise Window Targeting Architecture"
        echo "Usage: $0 {identify|send MESSAGE|test}"
        echo ""
        echo "Commands:"
        echo "  identify  - Identify and store target window/tab"
        echo "  send MSG  - Send message to exact target"
        echo "  test      - Test the targeting system"
        ;;
esac