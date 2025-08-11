#!/bin/bash

LOG_DIR="/Users/jonathanhill/src/redis-ai-challenge/tmp_logs/"
mkdir -p "$LOG_DIR"

# List of MCP servers to start
servers=(
    "mcp-redis-lisp-server mcp_redis_lisp_server.py"
    "emacs-persistent-vision-mcp emacs_persistent_vision_mcp.py --stdio"
    "mcp-ai-assistant mcp_ai_assistant.py"
    "redis-state-diff-mcp redis_state_diff_mcp.py"
    "redis-emacs-mcp-server redis_emacs_mcp_server.py"
)

for server_info in "${servers[@]}"; do
    name=$(echo "$server_info" | awk '{print $1}')
    script=$(echo "$server_info" | awk '{print $2}')
    args=$(echo "$server_info" | cut -d' ' -f3-)
    log_file="${LOG_DIR}${name}.log"

    echo "Starting $name, logging to $log_file..."
    /Users/jonathanhill/.pyenv/versions/3.12.2/bin/python3 "$script" $args > "$log_file" 2>&1 &
    sleep 0.5 # Give it a moment to start
    echo "$name launched. Check $log_file for output."
done

echo "All MCP servers launched. Check their respective ${LOG_DIR}*.log files for output."
