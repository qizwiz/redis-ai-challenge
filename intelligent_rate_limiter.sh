#!/bin/bash

# Intelligent Rate Limiter - Queue-Based API Negotiation

RATE_QUEUE="neuro:rate:queue"
RATE_TRACKER="neuro:rate:tracker"
MAX_QUEUE_SIZE=200
RATE_WINDOW=60  # 1 minute window

source ./pid_targeting.sh

add_to_queue() {
    local operation="$1"
    local priority="${2:-5}"  # Default priority 5
    
    # Check queue size
    local queue_size=$(redis-cli XLEN $RATE_QUEUE)
    
    if (( queue_size >= MAX_QUEUE_SIZE )); then
        echo "❌ Queue full ($queue_size/$MAX_QUEUE_SIZE)"
        return 1
    fi
    
    # Add with priority and timestamp
    redis-cli XADD $RATE_QUEUE '*' \
        operation "$operation" \
        priority "$priority" \
        timestamp "$(date +%s)" \
        queued_at "$(date)" \
        status "pending"
    
    echo "✅ Queued: $operation (priority: $priority)"
}

process_queue() {
    echo "🔄 Processing rate-limited queue..."
    
    while true; do
        # Check current rate usage
        local current_time=$(date +%s)
        local window_start=$((current_time - RATE_WINDOW))
        
        # Clean old rate tracking entries
        redis-cli ZREMRANGEBYSCORE $RATE_TRACKER 0 "$window_start" >/dev/null
        
        # Check current rate
        local current_rate=$(redis-cli ZCARD $RATE_TRACKER)
        
        # Conservative rate limit (adjust based on testing)
        if (( current_rate < 30 )); then  # 30 operations per minute
            # Get next operation from queue
            local next_op=$(redis-cli XREAD COUNT 1 BLOCK 1000 STREAMS $RATE_QUEUE 0 2>/dev/null | grep -A 10 "operation" | head -20)
            
            if [[ -n "$next_op" ]]; then
                # Extract operation details
                local operation=$(echo "$next_op" | grep -A 1 "operation" | tail -1)
                
                # Execute operation
                case "$operation" in
                    *"autonomous"*) 
                        send_to_pid "🤖 Rate-limited autonomous operation: $operation"
                        ;;
                    *"learning"*)
                        send_to_pid "🧠 Rate-limited learning operation: $operation"
                        ;;
                    *)
                        send_to_pid "⚡ Rate-limited operation: $operation"
                        ;;
                esac
                
                # Track this operation in rate limiter
                redis-cli ZADD $RATE_TRACKER "$current_time" "op_$current_time"
                
                echo "✅ Processed operation (rate: $current_rate/30)"
            fi
        else
            echo "🚦 Rate limit reached ($current_rate/30), waiting..."
            sleep 2
        fi
        
        sleep 1  # Base processing delay
    done
}

intelligent_queue_manager() {
    echo "🧠 Starting intelligent queue manager..."
    
    # Fork rate limiter in background
    process_queue &
    local processor_pid=$!
    
    # Intelligent operation generator
    local op_count=0
    while (( op_count < 100 )); do  # Generate 100 operations
        ((op_count++))
        
        # Vary operation types and priorities
        case $((op_count % 6)) in
            1) add_to_queue "autonomous_learning_cycle_$op_count" 8 ;;
            2) add_to_queue "system_performance_analysis_$op_count" 6 ;;
            3) add_to_queue "redis_pattern_study_$op_count" 7 ;;
            4) add_to_queue "meta_learning_analysis_$op_count" 9 ;;
            5) add_to_queue "window_automation_test_$op_count" 4 ;;
            0) add_to_queue "queue_optimization_$op_count" 10 ;;
        esac
        
        # Adaptive delay based on queue size
        local queue_size=$(redis-cli XLEN $RATE_QUEUE)
        if (( queue_size > 50 )); then
            sleep 5  # Slower when queue is full
        else
            sleep 2  # Faster when queue has space
        fi
    done
    
    echo "🏁 Generated 100 operations, processor continues in background"
    echo "📊 Monitor with: redis-cli XLEN $RATE_QUEUE"
    echo "🛑 Stop processor: kill $processor_pid"
}

queue_status() {
    echo "📊 Rate Limiter Status:"
    echo "Queue size: $(redis-cli XLEN $RATE_QUEUE)"
    echo "Current rate: $(redis-cli ZCARD $RATE_TRACKER)/30 per minute"
    echo ""
    echo "Recent queue entries:"
    redis-cli XREVRANGE $RATE_QUEUE + - COUNT 5 2>/dev/null || echo "No entries yet"
}

case "$1" in
    "add") add_to_queue "$2" "$3" ;;
    "process") process_queue ;;
    "smart") intelligent_queue_manager ;;
    "status") queue_status ;;
    *)
        echo "Intelligent Rate Limiter"
        echo "Usage: $0 {add OPERATION [PRIORITY]|process|smart|status}"
        echo ""
        echo "Creative API rate limit negotiation system!"
        ;;
esac