;; -*- lexical-binding: t; -*-
;; Real Emacs Claude REPL Test
;; This demonstrates the complete Claude REPL system working in actual Emacs

(defun test-claude-repl-complete ()
  "Test the complete Claude REPL system in real Emacs."
  (interactive)
  
  ;; Clear any existing messages first
  (shell-command "redis-cli DEL claude:messages claude:responses")
  
  (message "🧪 Testing Claude REPL System...")
  
  ;; 1. Load the claude_repl.el file
  (message "1️⃣ Loading claude_repl.el...")
  (load-file "/Users/jonathanhill/src/redis-ai-challenge/claude_repl.el")
  (message "✅ claude_repl.el loaded successfully")
  
  ;; 2. Start the Claude REPL buffer
  (message "2️⃣ Starting Claude REPL buffer...")
  (claude-repl)
  (message "✅ Claude REPL buffer created and displayed")
  
  ;; 3. Simulate sending a message
  (message "3️⃣ Simulating message send...")
  (with-current-buffer "*Claude-REPL*"
    ;; Go to the end and insert test message
    (goto-char (point-max))
    (insert "Hello Claude! Can you tell me what 2+2 equals?")
    
    ;; Call the send function
    (claude-repl-send-message)
    (message "✅ Test message sent via Redis"))
  
  ;; 4. Check Redis for the message
  (message "4️⃣ Checking Redis for message...")
  (let ((message-count (string-trim (shell-command-to-string "redis-cli XLEN claude:messages"))))
    (message "📨 Messages in Redis: %s" message-count))
  
  ;; 5. Instructions for bridge
  (message "5️⃣ To complete test:")
  (message "   Run: python3 claude_repl_bridge.py")
  (message "   This will process the message and add Claude's response")
  
  ;; 6. Show current buffer state
  (message "6️⃣ Claude REPL buffer is ready!")
  (message "✅ Complete test finished. Switch to *Claude-REPL* buffer to see results.")
  
  ;; Switch to the REPL buffer to show it
  (switch-to-buffer "*Claude-REPL*"))

;; Auto-run the test
(test-claude-repl-complete)