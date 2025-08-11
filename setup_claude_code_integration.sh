#!/bin/bash

# Setup Claude Code Integration for Redis-Emacs System

echo "🚀 Setting up Redis-Emacs Claude Code Integration"
echo "=================================================="

# 1. Install MCP servers
echo "📦 Installing MCP Servers..."
if command -v claude &> /dev/null; then
    # Add Redis-Emacs server
    claude mcp add --scope project redis-emacs python $(pwd)/redis_emacs_mcp_server.py
    echo "✅ Redis-Emacs MCP server added"
    
    # Add Voice Mode server (if not already installed)
    if ! claude mcp list | grep -q "voice-mode"; then
        claude mcp add --scope user voice-mode uvx voice-mode
        echo "✅ Voice Mode MCP server added"
    else
        echo "✅ Voice Mode already installed"
    fi
else
    echo "⚠️  Claude Code CLI not found. Install Claude Code first."
fi

# 2. Create subagent directory
echo "📁 Creating subagent directory..."
mkdir -p ~/.claude/agents
mkdir -p .claude/agents

# 3. Install project-level subagent
echo "🤖 Installing Emacs Dev Assistant subagent..."
cp emacs_dev_subagent.md .claude/agents/emacs-dev-assistant.md
echo "✅ Subagent installed at project level"

# 4. Install user-level subagent (optional)
echo "🌐 Installing user-level subagent..."
cp emacs_dev_subagent.md ~/.claude/agents/emacs-dev-assistant.md
echo "✅ Subagent available globally"

# 5. Test MCP server
echo "🧪 Testing MCP server..."
python redis_emacs_mcp_server.py --test &
SERVER_PID=$!
sleep 2

if ps -p $SERVER_PID > /dev/null; then
    echo "✅ MCP server running successfully"
    kill $SERVER_PID
else
    echo "❌ MCP server failed to start"
fi

# 6. Verify Redis is running
echo "🔍 Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis not running. Start with: redis-server"
fi

# 7. Test Emacs connection
echo "🎯 Testing Emacs connection..."
if emacsclient --eval "(message \"Claude Code integration test\")" > /dev/null 2>&1; then
    echo "✅ Emacs daemon connection working"
else
    echo "⚠️  Emacs daemon not responding. Start with: emacs --daemon=redis-tutorial"
fi

echo ""
echo "🎉 SETUP COMPLETE!"
echo "===================="
echo ""
echo "Usage in Claude Code:"
echo "1. Use subagent: 'Use the emacs-dev-assistant to switch to scratch'"
echo "2. Direct MCP: Use @redis-emacs tools for Emacs control"
echo "3. Natural language: 'make scratch the lone window and insert hello'"
echo ""
echo "Example commands:"
echo "- 'Use emacs-dev-assistant to open tutorial and split window right'"
echo "- 'Have the emacs assistant undo twice then redo the insertion'"
echo "- 'Ask emacs-dev-assistant to make scratch lone window'"
echo ""
echo "The Redis coordination is transparent - just speak naturally!"
echo "🚀 Ready for revolutionary AI-powered Emacs development!"