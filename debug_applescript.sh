#!/bin/bash
# This is a SIMPLER debug script to find the syntax error.

echo "Running simplified AppleScript test..."

# This version removes all complex error handling to isolate the syntax issue.
# It will only log to the macOS Console.app (which we can't see)
# but if it runs without a syntax error, it will print the final return string.
osascript <<'END'
    set app_count to 0
    try
        tell application "System Events"
            set process_names to name of every process where background only is false and visible is true
        end tell
        
        repeat with app_name in process_names
            try
                tell application app_name
                    if (count of windows) > 0 then
                        set app_count to app_count + 1
                    end if
                end tell
            end try
        end repeat
        
        return "SUCCESS: Script ran without syntax errors. Found " & app_count & " apps with windows."
        
    on error err_msg
        return "FAILURE: Script failed during execution. Error: " & err_msg
    end try
END