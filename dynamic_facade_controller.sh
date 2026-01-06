#!/bin/bash

# Dynamic Facade Controller - No Magic Numbers
# Real-time window tracking and control abstraction

REDIS_CLI="redis-cli"
FACADE_STREAM="facade:realtime"
WINDOW_STATE_KEY="facade:windows:current"

log_action() {
    local action="$1"
    shift
    $REDIS_CLI XADD $FACADE_STREAM '*' action "$action" timestamp "$(date +%s)" "$@"
}

get_frontmost_app() {
    osascript -e 'tell application "System Events" to get name of first process whose frontmost is true'
}

get_window_bounds() {
    local app="$1"
    osascript -e "tell application \"$app\" to get bounds of window 1" 2>/dev/null || echo "error"
}

get_screen_bounds() {
    osascript -e 'tell application "Finder" to get bounds of window of desktop' 2>/dev/null | tr -d ','
}

parse_bounds() {
    local bounds="$1"
    echo "$bounds" | tr -d ',' | awk '{print $1, $2, $3, $4}'
}

calculate_window_center() {
    local bounds="$1"
    read left top right bottom <<< $(parse_bounds "$bounds")
    local center_x=$(( (left + right) / 2 ))
    local center_y=$(( (top + bottom) / 2 ))
    echo "$center_x,$center_y"
}

get_running_apps() {
    osascript -e 'tell application "System Events" to get name of every process whose background only is false' | tr ',' '\n' | sed 's/^ *//'
}

update_window_state() {
    local app_list=$(get_running_apps)
    local timestamp=$(date +%s)
    
    # Store current window state
    $REDIS_CLI DEL $WINDOW_STATE_KEY
    
    while IFS= read -r app; do
        if [[ -n "$app" && "$app" != "System Events" ]]; then
            local bounds=$(get_window_bounds "$app")
            if [[ "$bounds" != "error" ]]; then
                local center=$(calculate_window_center "$bounds")
                $REDIS_CLI HSET $WINDOW_STATE_KEY "$app:bounds" "$bounds"
                $REDIS_CLI HSET $WINDOW_STATE_KEY "$app:center" "$center"
            fi
        fi
    done <<< "$app_list"
    
    $REDIS_CLI HSET $WINDOW_STATE_KEY "last_updated" "$timestamp"
    log_action "window_state_updated" apps_tracked "$(echo "$app_list" | wc -l)"
}

get_app_center() {
    local app="$1"
    $REDIS_CLI HGET $WINDOW_STATE_KEY "$app:center"
}

get_app_bounds() {
    local app="$1"
    $REDIS_CLI HGET $WINDOW_STATE_KEY "$app:bounds"
}

move_to_app_center() {
    local app="$1"
    local center=$(get_app_center "$app")
    if [[ -n "$center" ]]; then
        cliclick m:"$center"
        log_action "moved_to_app_center" app "$app" position "$center"
        echo "Moved to $app center: $center"
    else
        echo "No center data for $app"
    fi
}

split_screen_horizontal() {
    local app1="$1"
    local app2="$2"
    local screen_bounds=$(get_screen_bounds)
    read left top right bottom <<< $(parse_bounds "$screen_bounds")
    
    local mid_x=$(( (left + right) / 2 ))
    local app1_bounds="$left $top $mid_x $bottom"
    local app2_bounds="$mid_x $top $right $bottom"
    
    osascript -e "tell application \"$app1\" to set bounds of window 1 to {$app1_bounds}"
    osascript -e "tell application \"$app2\" to set bounds of window 1 to {$app2_bounds}"
    
    log_action "split_screen_horizontal" app1 "$app1" app2 "$app2" screen_bounds "$screen_bounds"
    update_window_state
}

case "$1" in
    "update")
        update_window_state
        ;;
    "center")
        move_to_app_center "$2"
        ;;
    "bounds")
        get_app_bounds "$2"
        ;;
    "split")
        split_screen_horizontal "$2" "$3"
        ;;
    "frontmost")
        get_frontmost_app
        ;;
    *)
        echo "Dynamic Facade Controller"
        echo "Usage: $0 {update|center APP|bounds APP|split APP1 APP2|frontmost}"
        echo ""
        echo "Commands:"
        echo "  update           - Update window state in Redis"
        echo "  center APP       - Move mouse to center of APP"
        echo "  bounds APP       - Get bounds of APP"
        echo "  split APP1 APP2  - Split screen between two apps"
        echo "  frontmost        - Get frontmost application"
        echo ""
        echo "Examples:"
        echo "  $0 update"
        echo "  $0 center Safari"
        echo "  $0 split iTerm2 Safari"
        ;;
esac