#!/bin/bash

# 🌟 DREAM INTERFACE ALIASES 🌟
# Source this file to get magical aliases

# Direct dream interface
alias dream='python3 /Users/jonathanhill/src/redis-ai-challenge/direct_dream_interface.py'
alias magic='python3 /Users/jonathanhill/src/redis-ai-challenge/direct_dream_interface.py'
alias ai='python3 /Users/jonathanhill/src/redis-ai-challenge/direct_dream_interface.py'

# Quick actions
alias dream-split='dream "split the screen"'
alias dream-workspace='dream "show me the workspace"'  
alias dream-hello='dream "hello, start the session"'
alias dream-focus='dream "focus on this window"'

# Conversational development
dream-chat() {
    echo "✨ Dream Interface Chat Mode ✨"
    echo "Type 'exit' to quit"
    echo ""
    while true; do
        printf "💭 You: "
        read -r input
        if [[ "$input" == "exit" || "$input" == "quit" ]]; then
            echo "✨ Sweet dreams! ✨"
            break
        fi
        echo -n "🤖 AI: "
        dream "$input"
        echo ""
    done
}

echo "🌟 Dream interface aliases loaded!"
echo "Try: dream 'hello there'"
echo "     dream 'split the screen'"  
echo "     dream-chat (for interactive mode)"