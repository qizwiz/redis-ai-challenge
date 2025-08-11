;;; reactive_mcp_executor.el --- Reactive MCP Lisp Executor

(defvar reactive-mcp-timer nil "Timer for reactive execution")
(defvar reactive-mcp-last-count 0 "Last stream length")

(defun reactive-mcp-start ()
  "Start reactive MCP Lisp execution"
  (interactive)
  (reactive-mcp-stop)
  (setq reactive-mcp-timer
        (run-with-timer 1 1 'reactive-mcp-check))
  (message "✅ Reactive MCP executor started - checking every second"))

(defun reactive-mcp-check ()
  "Check for new MCP Lisp commands and execute them"
  (let* ((current-count-output (shell-command-to-string "redis-cli -p 6380 XLEN emacs:commands"))
         (current-count (string-to-number current-count-output)))
    
    (when (> current-count reactive-mcp-last-count)
      (message "🔄 New MCP Lisp commands detected (%d -> %d)" reactive-mcp-last-count current-count)
      (execute-mcp-lisp-from-redis)
      (setq reactive-mcp-last-count current-count))))

(defun reactive-mcp-stop ()
  "Stop reactive MCP execution"
  (interactive)
  (when reactive-mcp-timer
    (cancel-timer reactive-mcp-timer)
    (setq reactive-mcp-timer nil))
  (message "Reactive MCP executor stopped"))

(provide 'reactive-mcp-executor)