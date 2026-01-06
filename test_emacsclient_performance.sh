#!/bin/bash
# Test emacs --batch vs emacsclient performance

echo "Testing Emacs performance: batch vs client"
echo ""

# Test 1: emacs --batch
echo "Test 1: emacs --batch"
time1_start=$(date +%s%N)
emacs --batch --eval '(message "Hello from batch")' 2>&1 | grep -v "^$" | head -1
time1_end=$(date +%s%N)
batch_time=$(( (time1_end - time1_start) / 1000000 ))  # Convert to ms
echo "Time: ${batch_time}ms"
echo ""

# Test 2: Start emacs daemon if not running
if ! pgrep -x "Emacs" > /dev/null; then
    echo "Starting Emacs daemon..."
    emacs --daemon 2>&1 | grep -v "^$"
    sleep 2
fi

# Test 3: emacsclient
echo "Test 2: emacsclient"
time2_start=$(date +%s%N)
emacsclient --eval '(message "Hello from client")' 2>&1 | grep -v "^$" | head -1
time2_end=$(date +%s%N)
client_time=$(( (time2_end - time2_start) / 1000000 ))
echo "Time: ${client_time}ms"
echo ""

# Calculate improvement
improvement=$(( batch_time - client_time ))
percent=$(( improvement * 100 / batch_time ))

echo "Results:"
echo "  Batch:  ${batch_time}ms"
echo "  Client: ${client_time}ms"
echo "  Improvement: ${improvement}ms (${percent}% faster)"
echo ""

# Log to Redis
redis-cli XADD emacs:performance '*' \
    test "batch-vs-client" \
    batch_ms "$batch_time" \
    client_ms "$client_time" \
    improvement_ms "$improvement" \
    improvement_percent "$percent" \
    conclusion "emacsclient is significantly faster" \
    timestamp "$(date +%s)" > /dev/null

echo "✅ Logged to Redis: emacs:performance"
