#!/bin/bash

echo "🚀 ULTIMATE REDIS BROWSER CONTROL DEMO"
echo "======================================"
echo "The ultimate demonstration of Redis beyond cache!"
echo "Redis will control your browser to submit DEV.to articles!"
echo ""

# Check if Redis is running
echo "📡 Checking Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis not running - starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

echo ""
echo "🌐 Starting Redis Browser Control Daemon..."
echo "This will open Chrome and listen for Redis commands"
echo ""
echo "In another terminal, you can control the browser with:"
echo "  redis-cli xadd browser:commands * action navigate url https://dev.to/new"
echo "  redis-cli xadd browser:commands * action submit_devto_article title 'Redis Demo' content 'Amazing!'"
echo ""
echo "🎯 THE ULTIMATE COMPETITION DEMO:"
echo "Redis streams controlling your browser to submit competition entries!"
echo ""
echo "Press Ctrl+C to stop the browser daemon"
echo ""

# Start the browser daemon
python3 redis_browser_control.py daemon