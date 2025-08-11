;;; redis-ai-monitoring.el --- Monitoring and Status functions for Redis AI Emacs mode

;;; Code:

(defvar redis-ai-command-history '()
  "History of Redis AI commands.")

(defun redis-ai-start-monitoring ()
  "Start monitoring Redis AI system status."
  (run-with-timer 10 10 'redis-ai-check-status))

(defun redis-ai-check-status ()
  "Check status of Redis AI system."
  (when redis-ai-connection
    (redis-ai-send-command "PING")))

(defun redis-ai-show-dashboard ()
  "Show Redis AI system dashboard."
  (interactive)
  (let ((buffer (get-buffer-create "*Redis AI Dashboard*")))
    (with-current-buffer buffer
      (erase-buffer)
      (insert "\U0001f980 Redis AI Workforce Dashboard\n")
      (insert "================================\n\n")
      (insert (format "Connection: %s\n" 
                      (if redis-ai-connection "✅ Connected" "❌ Disconnected")))
      (insert (format "Active Agents: %d\n" (length redis-ai-active-agents)))
      (insert (format "Commands Sent: %d\n\n" (length redis-ai-command-history)))
      
      (insert "Active Agents:\n")
      (dolist (agent redis-ai-active-agents)
        (insert (format "  • %s\n" agent)))
      
      (insert "\nRecent Commands:\n")
      (dolist (cmd (reverse (last redis-ai-command-history 10)))
        (insert (format "  %s\n" cmd)))
      
      (goto-char (point-min)))
    (display-buffer buffer)))

(provide 'redis-ai-monitoring)
;;; redis-ai-monitoring.el ends here
