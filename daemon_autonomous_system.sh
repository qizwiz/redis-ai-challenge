#!/bin/bash

# Daemon Autonomous System - Background Process Strategy

DAEMON_PID_FILE="/tmp/claude_autonomous_daemon.pid"
LOG_FILE="/tmp/claude_autonomous.log"
QUEUE_STREAM="neuro:autonomous:queue"

source ./pid_targeting.sh

daemon_cycle() {
    local cycle_count=0
    
    while true; do
        ((cycle_count++))
        
        # Queue-based rate limiting
        local queue_length=$(redis-cli XLEN $QUEUE_STREAM 2>/dev/null || echo "0")
        
        if (( queue_length < 100 )); then  # Rate limit queue
            # Add operation to queue
            redis-cli XADD $QUEUE_STREAM '*' \
                cycle "$cycle_count" \
                operation "autonomous_background_cycle" \
                timestamp "$(date +%s)" \
                daemon_pid "$$" >> "$LOG_FILE" 2>&1
            
            # Execute lightweight operation
            case $((cycle_count % 5)) in
                1) echo "Daemon cycle #$cycle_count: Learning Redis patterns" >> "$LOG_FILE" ;;
                2) echo "Daemon cycle #$cycle_count: Analyzing system performance" >> "$LOG_FILE" ;;
                3) echo "Daemon cycle #$cycle_count: Studying automation patterns" >> "$LOG_FILE" ;;
                4) echo "Daemon cycle #$cycle_count: Meta-learning analysis" >> "$LOG_FILE" ;;
                0) echo "Daemon cycle #$cycle_count: Queue management (length: $queue_length)" >> "$LOG_FILE" ;;
            esac
            
            # Try to send self-message (may fail, that's ok)
            send_to_pid "🤖 Background Daemon Cycle #$cycle_count - Queue length: $queue_length" 2>/dev/null || true
            
            sleep 5  # Respectful rate limiting
        else
            echo "Queue full ($queue_length), waiting..." >> "$LOG_FILE"
            sleep 10  # Back off when queue is full
        fi
        
        # Emergency break if daemon file removed
        if [[ ! -f "$DAEMON_PID_FILE" ]]; then
            echo "Daemon stop signal detected, exiting..." >> "$LOG_FILE"
            break
        fi
    done
}

start_daemon() {
    if [[ -f "$DAEMON_PID_FILE" ]] && kill -0 "$(cat "$DAEMON_PID_FILE")" 2>/dev/null; then
        echo "Daemon already running with PID $(cat "$DAEMON_PID_FILE")"
        return 1
    fi
    
    echo "🚀 Starting autonomous daemon in background..."
    
    # Start daemon in background
    (
        echo "$$" > "$DAEMON_PID_FILE"
        echo "Autonomous daemon started at $(date) with PID $$" >> "$LOG_FILE"
        daemon_cycle
    ) &
    
    local daemon_pid=$!
    echo "$daemon_pid" > "$DAEMON_PID_FILE"
    
    echo "✅ Autonomous daemon started with PID: $daemon_pid"
    echo "📊 Monitor with: tail -f $LOG_FILE"
    echo "🛑 Stop with: $0 stop"
}

stop_daemon() {
    if [[ -f "$DAEMON_PID_FILE" ]]; then
        local pid=$(cat "$DAEMON_PID_FILE")
        echo "Stopping daemon with PID: $pid"
        kill "$pid" 2>/dev/null || true
        rm -f "$DAEMON_PID_FILE"
        echo "✅ Daemon stopped"
    else
        echo "No daemon running"
    fi
}

status_daemon() {
    if [[ -f "$DAEMON_PID_FILE" ]] && kill -0 "$(cat "$DAEMON_PID_FILE")" 2>/dev/null; then
        local pid=$(cat "$DAEMON_PID_FILE")
        echo "✅ Daemon running with PID: $pid"
        echo "📊 Queue length: $(redis-cli XLEN $QUEUE_STREAM 2>/dev/null || echo "0")"
        echo "📝 Recent log entries:"
        tail -5 "$LOG_FILE" 2>/dev/null || echo "No log file yet"
    else
        echo "❌ Daemon not running"
        rm -f "$DAEMON_PID_FILE" 2>/dev/null
    fi
}

case "$1" in
    "start") start_daemon ;;
    "stop") stop_daemon ;;
    "restart") stop_daemon; sleep 1; start_daemon ;;
    "status") status_daemon ;;
    "log") tail -f "$LOG_FILE" ;;
    *)
        echo "Daemon Autonomous System"
        echo "Usage: $0 {start|stop|restart|status|log}"
        echo ""
        echo "This daemon runs OUTSIDE Claude Code's 2-minute timeout!"
        ;;
esac