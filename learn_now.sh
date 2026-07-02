#!/bin/bash
# Learn Emacs RIGHT NOW using the facade

redis-cli XADD learning:stream '*' \
  ts "$(date +%s)" \
  event "starting-learning" \
  facade "$(redis-cli GET facade:test:frontmost)"

echo "Starting empirical Emacs learning with facade..."
echo "Frontmost: $(redis-cli GET facade:test:frontmost)"
echo ""

# Learn by doing - execute and log
learn_command() {
  local name="$1"
  local elisp="$2"

  echo "Learning: $name"
  result=$(emacs --batch --eval "$elisp" 2>&1)

  redis-cli XADD learning:stream '*' \
    ts "$(date +%s)" \
    lesson "$name" \
    elisp "$elisp" \
    result "$result"

  echo "  Result: $result"
}

# Buffer operations
learn_command "buffer-creation" '(message "Buffer: %s" (buffer-name))'
learn_command "point-query" '(message "Point: %d" (point))'
learn_command "insert-text" '(progn (insert "test") (message "Inserted"))'

# Verification
count=$(redis-cli XLEN learning:stream)
echo ""
echo "Learned $count lessons"
redis-cli XREAD COUNT 3 STREAMS learning:stream 0
