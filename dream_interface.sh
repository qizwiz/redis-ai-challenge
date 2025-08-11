#!/bin/bash

# 🌟 THE ULTIMATE DREAM INTERFACE 🌟
# Natural language → Claude Code headless → MCP subagents → Magic!

function dream() {
    local input="$*"
    
    # If no arguments, start interactive dream session
    if [ -z "$input" ]; then
        echo "✨ Welcome to the Dream Interface! ✨"
        echo "Just type naturally and I'll understand..."
        echo ""
        while true; do
            printf "💭 You: "
            read -r user_input
            
            # Exit conditions
            if [[ "$user_input" =~ ^(exit|quit|bye|goodbye)$ ]]; then
                echo "✨ Dream session ended. See you next time! ✨"
                break
            fi
            
            # Send to Claude with full MCP power
            echo "🤖 AI: "
            echo "$user_input" | claude -p "Use the subagent-coordinator MCP to handle this naturally: " --mcp-config .mcp.json
            echo ""
        done
    else
        # Direct command mode
        echo "$input" | claude -p "Use the subagent-coordinator MCP to handle this naturally: " --mcp-config .mcp.json
    fi
}

# Magical aliases for even more natural interaction
alias magic="dream"
alias ai="dream"
alias claude-dream="dream"

# Stream mode for real-time responses
dream-stream() {
    local input="$*"
    echo "$input" | claude -p "Use the subagent-coordinator MCP to handle this naturally: " --mcp-config .mcp.json --output-format stream-json
}

# Quick workspace setup
dream-workspace() {
    dream "start magical session"
}

# Pattern learning from shell history
dream-learn() {
    echo "Learning from your shell patterns..."
    history | tail -20 | claude -p "Analyze these recent shell commands and suggest workflow improvements using the subagent-coordinator: " --mcp-config .mcp.json
}

echo "🌟 Dream Interface loaded! Try:"
echo "  dream hello"
echo "  dream split the screen and show me the workspace" 
echo "  dream-workspace"
echo "  dream (for interactive mode)"
echo "✨ Your AI development companion is ready! ✨"