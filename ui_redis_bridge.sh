#!/bin/bash
# UI-Redis Bridge: Complete macOS UI representation in Redis
# Every interactable element becomes Redis-controllable

echo "🌉 UI-Redis Bridge - Pure Shell Implementation"

# Function to discover and register UI elements
map_app_to_redis() {
    local app_name="$1"
    echo "🔍 Mapping $app_name to Redis..."
    
    # Get all buttons in the app
    local buttons=$(osascript -e "
        tell application \"System Events\"
            tell process \"$app_name\"
                set buttonList to every button
                set buttonInfo to {}
                repeat with i from 1 to (count of buttonList)
                    try
                        set btn to item i of buttonList
                        set btnPos to position of btn
                        set btnTitle to title of btn
                        set btnRole to subrole of btn
                        set end of buttonInfo to {i, btnPos, btnTitle, btnRole}
                    on error
                        set end of buttonInfo to {i, \"unknown\", \"unknown\", \"unknown\"}
                    end try
                end repeat
                return buttonInfo
            end tell
        end tell
    " 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        # Parse button info and store in Redis
        local button_count=0
        while IFS= read -r line; do
            if [[ "$line" =~ ^[0-9] ]]; then
                button_count=$((button_count + 1))
                local redis_key="ui:button:$app_name:$button_count"
                local redis_cmd="ui:click:$app_name:$button_count"
                
                # Store in Redis
                redis-cli HSET "$redis_key" \
                    "app" "$app_name" \
                    "type" "button" \
                    "index" "$button_count" \
                    "redis_command" "$redis_cmd" \
                    "info" "$line" \
                    "timestamp" "$(date +%s)" > /dev/null
                
                # Add to searchable index
                redis-cli SADD "ui:elements:index" "$redis_key" > /dev/null
                
                echo "   ✓ Registered: $redis_cmd"
            fi
        done <<< "$buttons"
        
        echo "   📊 Mapped $button_count buttons for $app_name"
        return $button_count
    else
        echo "   ❌ Failed to access $app_name"
        return 0
    fi
}

# Function to execute Redis UI commands
execute_ui_command() {
    local redis_command="$1"
    echo "🎯 Executing: $redis_command"
    
    # Parse command: ui:click:iTerm2:3
    IFS=':' read -ra PARTS <<< "$redis_command"
    local action="${PARTS[1]}"
    local app_name="${PARTS[2]}"
    local element_id="${PARTS[3]}"
    
    if [[ "$action" == "click" ]]; then
        # Execute click via AppleScript
        local result=$(osascript -e "
            tell application \"System Events\"
                tell process \"$app_name\"
                    try
                        click button $element_id
                        return \"success\"
                    on error errorMessage
                        return \"error: \" & errorMessage
                    end try
                end tell
            end tell
        " 2>&1)
        
        # Log to Redis
        redis-cli XADD "ui:actions" "*" \
            "action" "$action" \
            "app" "$app_name" \
            "element" "$element_id" \
            "result" "$result" \
            "timestamp" "$(date +%s)" > /dev/null
        
        echo "   Result: $result"
        return 0
    fi
    
    echo "   ❌ Unknown action: $action"
    return 1
}

# Function to store and execute osascript commands via Redis
store_osascript_command() {
    local script="$1"
    local description="$2"
    local cmd_id="osascript_$(date +%s%N | cut -b1-13)"
    
    # Store script in Redis
    redis-cli SET "osascript:cmd:$cmd_id" "$script" > /dev/null
    redis-cli HSET "osascript:meta:$cmd_id" \
        "description" "$description" \
        "created" "$(date +%s)" \
        "status" "stored" > /dev/null
    
    echo "$cmd_id"
}

execute_osascript_from_redis() {
    local cmd_id="$1"
    local script=$(redis-cli GET "osascript:cmd:$cmd_id")
    
    if [[ -n "$script" ]]; then
        echo "🔧 Executing: $cmd_id"
        local result=$(osascript -e "$script" 2>&1)
        local success=$?
        
        # Store result in Redis
        redis-cli XADD "osascript:results" "*" \
            "cmd_id" "$cmd_id" \
            "success" "$success" \
            "output" "$result" \
            "timestamp" "$(date +%s)" > /dev/null
        
        redis-cli HSET "osascript:meta:$cmd_id" "status" "executed" > /dev/null
        
        echo "   Result: $result"
        return $success
    else
        echo "   ❌ Command not found: $cmd_id"
        return 1
    fi
}

# Main execution
echo "🗺️  Mapping desktop UI to Redis..."

# Map key applications
for app in "iTerm2" "Emacs" "Safari" "Finder"; do
    map_app_to_redis "$app"
done

echo ""
echo "🧪 Testing osascript-Redis bridge..."

# Test command storage and execution
cmd_id=$(store_osascript_command \
    "tell application \"System Events\" to get name of first process whose frontmost is true" \
    "Get frontmost process")

execute_osascript_from_redis "$cmd_id"

echo ""
echo "✅ UI-Redis Bridge Ready!"
echo "   📋 Available commands:"
echo "      redis-cli SMEMBERS ui:elements:index"
echo "      redis-cli XREAD STREAMS ui:actions 0"
echo "      redis-cli XREAD STREAMS osascript:results 0"
echo ""
echo "   🎯 Execute UI element:"
echo "      ./ui_redis_bridge.sh execute ui:click:iTerm2:1"
echo ""
echo "   📝 Store osascript command:"
echo "      ./ui_redis_bridge.sh store 'tell app \"Finder\" to activate' 'Activate Finder'"

# Handle command line arguments
if [[ "$1" == "execute" && -n "$2" ]]; then
    execute_ui_command "$2"
elif [[ "$1" == "store" && -n "$2" ]]; then
    description="${3:-No description}"
    cmd_id=$(store_osascript_command "$2" "$description")
    echo "Stored as: $cmd_id"
elif [[ "$1" == "run" && -n "$2" ]]; then
    execute_osascript_from_redis "$2"
fi