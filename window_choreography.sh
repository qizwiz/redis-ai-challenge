#!/bin/bash

# Window Choreography - Advanced NeuroCommander Patterns

source ./neurocommander.sh

# Pattern 1: Spiral Layout
spiral_layout() {
    echo "🌀 Executing spiral window layout..."
    ./neurocommander.sh drag Safari 100 100
    sleep 0.1
    ./neurocommander.sh drag Messages 300 200  
    sleep 0.1
    ./neurocommander.sh drag Emacs 500 300
    sleep 0.1
    ./neurocommander.sh drag System\ Settings 700 400
    echo "✅ Spiral complete"
}

# Pattern 2: Rapid Window Cascade
cascade_windows() {
    echo "📚 Cascading windows rapidly..."
    local x=50
    local y=50
    for app in Safari Messages Emacs Contacts; do
        ./neurocommander.sh drag "$app" "$x" "$y" &
        x=$((x + 50))
        y=$((y + 50))
    done
    wait
    echo "✅ Cascade complete"
}

# Pattern 3: Gaming Speed Test
gaming_speed_test() {
    echo "🎮 Gaming speed window manipulation test..."
    local start_time=$(gdate +%s%3N)
    
    for i in {1..10}; do
        ./neurocommander.sh drag Safari $((100 + i*50)) $((100 + i*30))
        sleep 0.01
    done
    
    local end_time=$(gdate +%s%3N)
    local duration=$((end_time - start_time))
    echo "✅ 10 window moves in ${duration}ms - $(bc <<< "scale=2; 1000/$duration * 10") moves/second"
}

# Pattern 4: Self-Improving Loop
self_improving_loop() {
    echo "🧠 Self-improving automation loop..."
    
    # Measure current performance
    local start=$(gdate +%s%3N)
    ./neurocommander.sh update
    local update_time=$(($(gdate +%s%3N) - start))
    
    # Log performance and improve
    redis-cli XADD facade:performance '*' \
        action "update_benchmark" \
        duration_ms "$update_time" \
        timestamp "$(date +%s)"
    
    echo "Update took ${update_time}ms - logging for future optimization"
    
    # Suggest improvement
    if [ "$update_time" -gt 100 ]; then
        echo "🔧 Performance issue detected - caching window states"
        redis-cli HSET neuro:optimization cache_enabled "true"
    fi
}

# Execute all patterns
execute_choreography() {
    echo "🎭 Starting Window Choreography Performance..."
    
    spiral_layout
    sleep 1
    
    cascade_windows  
    sleep 1
    
    gaming_speed_test
    sleep 1
    
    self_improving_loop
    
    echo "🎊 Choreography complete! NeuroCommander mastery demonstrated."
}

case "$1" in
    "spiral") spiral_layout ;;
    "cascade") cascade_windows ;;
    "gaming") gaming_speed_test ;;
    "improve") self_improving_loop ;;
    "all") execute_choreography ;;
    *)
        echo "Window Choreography Patterns"
        echo "Usage: $0 {spiral|cascade|gaming|improve|all}"
        ;;
esac