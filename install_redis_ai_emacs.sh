#!/bin/bash
# Install Redis AI Emacs Mode

EMACS_CONFIG_DIR="$HOME/.emacs.d"
REDIS_AI_DIR="$EMACS_CONFIG_DIR/redis-ai"

echo "🚀 Installing Redis AI Emacs Mode..."

# Create directory
mkdir -p "$REDIS_AI_DIR"

# Copy the mode file
cp redis-ai-emacs-mode.el "$REDIS_AI_DIR/"

# Add to Emacs configuration
INIT_FILE="$EMACS_CONFIG_DIR/init.el"
CONFIG_ENTRY="
;; Redis AI Workforce Integration
(add-to-list 'load-path "$REDIS_AI_DIR")
(require 'redis-ai-emacs-mode)
(redis-ai-global-mode-enable)
"

if ! grep -q "redis-ai-emacs-mode" "$INIT_FILE" 2>/dev/null; then
    echo "$CONFIG_ENTRY" >> "$INIT_FILE"
    echo "✅ Added Redis AI mode to Emacs configuration"
else
    echo "✅ Redis AI mode already configured"
fi

echo "🎉 Installation complete!"
echo ""
echo "Usage in Emacs:"
echo "  M-x redis-ai-mode    - Enable in current buffer"
echo "  C-c r c              - Connect to Redis"
echo "  C-c r t              - Generate tests"
echo "  C-c r o              - Generate documentation"
echo "  C-c r l              - Execute Lisp"
echo "  C-c r n              - Natural language command"
echo "  C-c r D              - Show dashboard"
echo ""
echo "Restart Emacs to complete installation."
