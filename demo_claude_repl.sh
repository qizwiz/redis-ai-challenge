#!/bin/bash
# Claude REPL Demo Script
# Demonstrates the complete Emacs-Redis-Claude conversation system

set -e

echo "🚀 Claude REPL System Demo"
echo "========================="
echo
echo "This demo shows the complete conversation system:"
echo "Emacs → Redis → Claude → Redis → Emacs"
echo

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first:"
    echo "   brew services start redis"
    exit 1
fi

echo "✅ Redis is running"

# Test the system
echo
echo "🧪 Running system test..."
if python3 test_complete_repl_system.py; then
    echo
    echo "🎉 System test completed successfully!"
else
    echo "❌ System test failed"
    exit 1
fi

echo
echo "📖 Usage Instructions:"
echo "====================="
echo
echo "1. Start Emacs:"
echo "   emacs"
echo
echo "2. Load the Claude REPL:"
echo "   M-x load-file RET claude_repl_fixed.el RET"
echo
echo "3. Start the Claude REPL:"
echo "   M-x claude-repl RET"
echo
echo "4. In another terminal, start the bridge:"
echo "   python3 claude_repl_bridge.py"
echo
echo "5. Type messages in the Emacs REPL buffer and press RET"
echo
echo "🔧 Manual Testing:"
echo "=================="
echo
echo "You can also test manually:"
echo
echo "# Send a message from command line:"
echo "redis-cli XADD claude:messages '*' message 'Hello Claude!' user '\$USER' timestamp '\$(date +%s)'"
echo
echo "# Check for responses:"
echo "redis-cli XRANGE claude:responses - +"
echo
echo "🎯 The system provides:"
echo "• Real-time conversation with Claude"
echo "• Full conversation history"
echo "• Redis-based message queuing"
echo "• Emacs integration with syntax highlighting"
echo "• Fault-tolerant message processing"
echo
echo "✨ Ready to revolutionize AI development workflows!"