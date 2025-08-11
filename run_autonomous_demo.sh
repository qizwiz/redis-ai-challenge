#!/bin/bash
# Autonomous AI Emacs Tutorial Demo - Run independently
set -e

echo "🤖 AUTONOMOUS AI EMACS TUTORIAL DEMO"
echo "===================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v redis-cli &> /dev/null; then
    echo "❌ Redis not found. Install with: brew install redis"
    exit 1
fi

if ! pgrep redis-server > /dev/null; then
    echo "🚀 Starting Redis server..."
    redis-server --daemonize yes
    sleep 2
fi

if ! pgrep emacs > /dev/null; then
    echo "❌ Emacs not running. Please start Emacs first."
    exit 1
fi

if ! emacsclient -e "(buffer-name)" &> /dev/null; then
    echo "❌ emacsclient not working. Start Emacs server with: M-x server-start"
    exit 1
fi

echo "✅ All prerequisites met!"

# Setup tutorial
echo "📚 Setting up Emacs tutorial..."
emacsclient -e "(progn (delete-other-windows) (split-window-right) (other-window 1) (help-with-tutorial) (other-window 1) (switch-to-buffer \"*vterminal<1>*\") \"Layout ready\")" > /dev/null

# Check if tutorial buffer has content
tutorial_size=$(emacsclient -e "(with-current-buffer \"TUTORIAL\" (buffer-size))")
if [ "$tutorial_size" -eq 0 ]; then
    echo "🔧 Loading tutorial content..."
    emacsclient -e "(progn (other-window 1) (switch-to-buffer \"TUTORIAL\") (erase-buffer) (insert-file-contents (expand-file-name \"TUTORIAL\" data-directory)) (beginning-of-buffer) \"Tutorial loaded\")" > /dev/null
fi

# Disable evil mode for proper key interpretation
emacsclient -e "(evil-mode -1)" > /dev/null 2>&1 || true

echo "✅ Tutorial setup complete!"

# Start command processor in background
echo "🔧 Starting command processor..."
python simple_command_processor.py > /tmp/command_processor.log 2>&1 &
PROCESSOR_PID=$!

# Give processor time to start
sleep 2

echo "🚀 Starting autonomous AI..."
echo "   (Press Ctrl+C to stop)"
echo ""

# Run the autonomous AI
if python realtime_autonomous_ai.py; then
    echo "✅ Demo completed successfully!"
else
    echo "⚠️  Demo stopped"
fi

# Cleanup
echo "🧹 Cleaning up..."
kill $PROCESSOR_PID 2>/dev/null || true
echo "✅ Done!"