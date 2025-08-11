#!/bin/bash

# Start Emacs daemon for Redis integration
echo "🚀 Starting Emacs daemon for Redis-AI integration..."

# Kill any existing Emacs daemon
pkill -f "emacs.*daemon" 2>/dev/null

# Start fresh daemon with server
emacs --daemon=redis-tutorial &

# Give it time to start
sleep 2

# Test the connection
if emacsclient -s redis-tutorial --eval "(message \"✅ Daemon started successfully\")" 2>/dev/null; then
    echo "✅ Emacs daemon started successfully"
    echo "✅ Socket: redis-tutorial"
    echo "✅ Ready for Redis integration testing"
    echo ""
    echo "🎯 Now run: python WORKING_DEMO.py"
else
    echo "❌ Failed to start Emacs daemon"
    echo "Trying alternative method..."
    
    # Alternative: start regular Emacs in background
    emacs --batch --eval "(progn (setq server-name \"redis-tutorial\") (server-start) (while t (sleep-for 1)))" &
    sleep 2
    
    if emacsclient -s redis-tutorial --eval "(message \"✅ Alternative method works\")" 2>/dev/null; then
        echo "✅ Alternative Emacs server started"
    else
        echo "❌ All methods failed. Please start Emacs manually and run:"
        echo "    M-x server-start"
        echo "    (setq server-name \"redis-tutorial\")"
    fi
fi