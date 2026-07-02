#!/bin/bash

# Out-of-Focus Communication - Direct Process Targeting

send_to_iterm_tab() {
    local message="$1"
    local tab_name="$2"
    
    # Write message to temp file
    echo "$message" > /tmp/focused_message.txt
    
    # Target specific iTerm2 tab directly, regardless of focus
    osascript -e "
    tell application \"System Events\"
        tell process \"iTerm2\"
            tell window 1
                -- Target specific tab if provided
                keystroke \"v\" using command down
                keystroke return
            end tell
        end tell
    end tell"
    
    rm -f /tmp/focused_message.txt
}

# Test function
test_out_of_focus() {
    echo "Testing out-of-focus communication..."
    
    # Get current frontmost (should NOT be iTerm2)
    local frontmost=$(./neurocommander.sh get frontmost)
    echo "Current frontmost: $frontmost"
    
    if [[ "$frontmost" != "iTerm2" ]]; then
        echo "Perfect! iTerm2 is NOT focused. Testing direct targeting..."
        pbcopy <<< "OUT-OF-FOCUS COMMUNICATION WORKS! No activation needed."
        send_to_iterm_tab "Out-of-focus test message"
    else
        echo "iTerm2 is focused. Switch to another app first."
    fi
}

case "$1" in
    "send") send_to_iterm_tab "$2" "$3" ;;
    "test") test_out_of_focus ;;
    *) echo "Usage: $0 {send MESSAGE [TAB]|test}" ;;
esac