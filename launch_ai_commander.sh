#!/bin/bash

# Ensure Emacs daemon is running
emacsclient -s redis-tutorial -e "(server-running-p)" &>/dev/null
if [ $? -ne 0 ]; then
  echo "Starting Emacs daemon..."
  emacs --daemon=redis-tutorial
  sleep 2 # Give Emacs time to start
fi

# Launch interactive AI Commander in a new Emacs frame
emacsclient -s redis-tutorial --create-frame --eval \
  "(progn
     (switch-to-buffer (get-buffer-create \"*AI Commander*\"))
     (shell)
     (message \"AI Commander buffer created. Please type 'python interactive_ai_commander.py' and press Enter.\")
     )"