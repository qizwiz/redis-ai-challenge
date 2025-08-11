;; -*- lexical-binding: t; -*-
;; Manual Claude REPL Test - Run this in your Emacs to test the system

(defun manual-claude-repl-test ()
  "Manually test the Claude REPL system step by step."
  (interactive)
  
  (let ((test-buffer "*Claude-REPL-Test*"))
    
    ;; Create test buffer for logging
    (with-current-buffer (get-buffer-create test-buffer)
      (erase-buffer)
      (insert "=== Claude REPL Manual Test ===\n\n")
      
      ;; Test 1: Load the REPL
      (insert "1️⃣ Loading claude_repl.el...\n")
      (condition-case err
          (progn
            (load-file "/Users/jonathanhill/src/redis-ai-challenge/claude_repl.el")
            (insert "✅ claude_repl.el loaded successfully\n\n"))
        (error
         (insert (format "❌ Error loading: %s\n\n" err))))
      
      ;; Test 2: Start the REPL
      (insert "2️⃣ Starting Claude REPL...\n")
      (condition-case err
          (progn
            (claude-repl)
            (insert "✅ Claude REPL buffer created\n")
            (insert "📺 Switch to *Claude-REPL* buffer to see it\n\n"))
        (error
         (insert (format "❌ Error starting REPL: %s\n\n" err))))
      
      ;; Test 3: Check Redis connection
      (insert "3️⃣ Testing Redis connection...\n")
      (let ((redis-test (shell-command-to-string "redis-cli ping 2>/dev/null")))
        (if (string-match "PONG" redis-test)
            (insert "✅ Redis is running and responding\n\n")
          (insert "❌ Redis not responding - start with 'redis-server'\n\n")))
      
      ;; Test 4: Manual message test
      (insert "4️⃣ Manual message test:\n")
      (insert "   📝 Adding test message to Redis...\n")
      (let ((result (shell-command-to-string 
                     "redis-cli XADD claude:messages '*' message 'Hello from manual test!' user 'manual_tester' timestamp '1234567890'")))
        (if (> (length (string-trim result)) 0)
            (insert (format "   ✅ Message added: %s\n" (string-trim result)))
          (insert "   ❌ Failed to add message\n")))
      
      ;; Instructions
      (insert "\n📋 NEXT STEPS:\n")
      (insert "   1. In terminal: python3 claude_repl_bridge.py\n")
      (insert "   2. Switch to *Claude-REPL* buffer\n")
      (insert "   3. Type a message and press RET\n")
      (insert "   4. Watch for Claude's response!\n\n")
      
      ;; Show current Redis state
      (insert "🔍 CURRENT REDIS STATE:\n")
      (let ((msg-count (string-trim (shell-command-to-string "redis-cli XLEN claude:messages 2>/dev/null")))
            (resp-count (string-trim (shell-command-to-string "redis-cli XLEN claude:responses 2>/dev/null"))))
        (insert (format "   📨 Messages waiting: %s\n" msg-count))
        (insert (format "   🤖 Responses available: %s\n" resp-count)))
      
      (insert "\n✅ Manual test complete! Check results above.\n"))
    
    ;; Show the test buffer
    (pop-to-buffer test-buffer)
    (message "Manual Claude REPL test completed - see *Claude-REPL-Test* buffer")))

;; Convenient function to just start the REPL
(defun start-claude-repl ()
  "Quick function to load and start Claude REPL."
  (interactive)
  (load-file "/Users/jonathanhill/src/redis-ai-challenge/claude_repl.el")
  (claude-repl)
  (message "Claude REPL ready! Type messages and press RET. Start bridge with: python3 claude_repl_bridge.py"))

;; Run the test
(manual-claude-repl-test)