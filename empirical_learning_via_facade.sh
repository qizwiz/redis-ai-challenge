#!/bin/bash
# Pure facade-based learning - no Emacs execution needed

STREAM="empirical:learning"

capture_and_learn() {
  local lesson="$1"
  local observation="$2"

  # Capture full facade state
  local frontmost=$(osascript -e 'tell application "System Events" to get name of first process whose frontmost is true')
  local app_count=$(osascript -e 'tell application "System Events" to count (every process whose background only is false)')
  local proc_count=$(ps aux | wc -l | tr -d ' ')
  local connections=$(netstat -an | grep ESTABLISHED | wc -l | tr -d ' ')

  # Log to Redis
  redis-cli XADD "$STREAM" '*' \
    ts "$(date +%s)" \
    lesson "$lesson" \
    observation "$observation" \
    frontmost "$frontmost" \
    apps "$app_count" \
    processes "$proc_count" \
    connections "$connections"

  echo "✓ $lesson"
}

echo "=== Empirical Learning via Facade ==="
echo "Observing system state and logging to Redis..."
echo ""

# Lesson 1: Observe current state
capture_and_learn "system-observation" \
  "System has $(ps aux | wc -l) processes, $(netstat -an | grep ESTABLISHED | wc -l) network connections"

# Lesson 2: Observe running apps
capture_and_learn "application-discovery" \
  "Found $(osascript -e 'tell application "System Events" to count (every process whose background only is false)') GUI applications"

# Lesson 3: Observe frontmost app
frontmost=$(osascript -e 'tell application "System Events" to get name of first process whose frontmost is true')
capture_and_learn "focus-detection" \
  "Current focus: $frontmost"

# Lesson 4: Redis itself
redis_keys=$(redis-cli DBSIZE | cut -d: -f2 | tr -d ' ')
capture_and_learn "redis-introspection" \
  "Redis contains $redis_keys keys (homoiconic storage)"

# Lesson 5: Learning stream
stream_len=$(redis-cli XLEN "$STREAM")
capture_and_learn "meta-learning" \
  "This stream now contains $stream_len learning events"

echo ""
echo "=== Learning Summary ==="
redis-cli XLEN "$STREAM" | xargs echo "Total lessons:"
echo ""
echo "Recent lessons:"
redis-cli XREVRANGE "$STREAM" + - COUNT 3
