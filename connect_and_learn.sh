#!/bin/bash
# Connect to running Emacs and learn with facade

echo "Connecting to Emacs PID 928..."

# Check if server is running
if ! pgrep -f "emacs.*server" > /dev/null; then
  echo "Starting Emacs server..."
  # Send command to running Emacs to start server
  osascript -e 'tell application "Emacs" to activate' 2>/dev/null
fi

# Capture facade state
redis-cli DEL facade:learning:session
redis-cli XADD facade:learning:session '*' \
  event "session-start" \
  frontmost "$(osascript -e 'tell application "System Events" to get name of first process whose frontmost is true')" \
  apps "$(osascript -e 'tell application "System Events" to count (every process whose background only is false)')" \
  ts "$(date +%s)"

echo "Facade captured. Learning session logged to Redis."
redis-cli XREAD COUNT 1 STREAMS facade:learning:session 0
