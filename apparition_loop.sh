#!/bin/bash

# apparition_loop.sh - Digital Apparition Continuous Sensing Loop
# This script continuously scans the desktop UI elements and persists them to Redis.

PHOENIX_LOG="phoenix:log" # Still log to phoenix log to combine logs
REDIS_CLI="redis-cli"
NEUROCOMMANDER_PATH="/Users/jonathanhill/src/redis-ai-challenge/neurocommander.sh"
APPARITION_LOG="apparition:log"
DESKTOP_STATE_KEY="desktop:state"

# Log function for the Apparition process
apparition_log() {
    local phase="$1"
    shift
    $REDIS_CLI XADD $APPARITION_LOG '*' phase "$phase" timestamp "$(date +%s)" "$@"
}

# Ensure neurocommander.sh is executable
if [[ ! -x "$NEUROCOMMANDER_PATH" ]]; then
    chmod +x "$NEUROCOMMANDER_PATH"
fi

# Main Apparition loop
while true; do
    apparition_log "sensing" status "started" message "Performing deep scan of frontmost application."

    # Get the frontmost application name using the new, fixed neurocommander.sh
    FRONTMOST_APP=$($NEUROCOMMANDER_PATH get frontmost_app_name)

    if [[ -n "$FRONTMOST_APP" ]]; then
        apparition_log "sensing" status "deep_scanning" app "$FRONTMOST_APP"
        
        # Use the new nc_scan_elements function
        DEEP_SCAN_JSON=$($NEUROCOMMANDER_PATH deepscan "$FRONTMOST_APP")
        
        if [[ -n "$DEEP_SCAN_JSON" ]]; then
            # Store the detailed UI hierarchy in a dedicated key for the app
            $REDIS_CLI HSET "desktop:app:$FRONTMOST_APP" "ui_hierarchy" "$DEEP_SCAN_JSON"
            apparition_log "sensing" status "ui_hierarchy_persisted" app "$FRONTMOST_APP"

            # Extract a simplified frontmost state for quick lookup
            $REDIS_CLI HSET "$DESKTOP_STATE_KEY" "frontmost_app" "$FRONTMOST_APP"
            $REDIS_CLI HSET "$DESKTOP_STATE_KEY" "last_deepscan_app" "$FRONTMOST_APP"
            $REDIS_CLI HSET "$DESKTOP_STATE_KEY" "last_deepscan_time" "$(date +%s)"
            
            apparition_log "sensing" status "frontmost_app_state_updated" app "$FRONTMOST_APP"
        else
            apparition_log "sensing" status "deep_scan_failed" app "$FRONTMOST_APP" message "No UI hierarchy returned."
        fi
    else
        apparition_log "sensing" status "no_frontmost_app" message "Could not determine frontmost application."
    fi

    apparition_log "sensing" status "completed" message "Deep scan cycle finished. Waiting for next cycle."
    sleep 10 # Scan every 10 seconds
done
