;;; working_mcp_lisp_executor.el --- Actually Working MCP Lisp Executor

(defvar mcp-lisp-last-id "0-0" "Last processed message ID")

(defun execute-mcp-lisp-from-redis ()
  "Execute new MCP Lisp commands from Redis port 6380"
  (interactive)
  
  (let* ((redis-output (shell-command-to-string 
                       (format "redis-cli -p 6380 XREAD STREAMS emacs:commands %s" mcp-lisp-last-id)))
         (lines (split-string redis-output "\n" t))
         (executed-count 0)
         (current-id nil))
    
    (dolist (line lines)
      (cond
       ;; Message ID line
       ((string-match "^\\([0-9]+-[0-9]+\\)$" line)
        (setq current-id line))
       ;; Skip metadata
       ((string-match-p "^emacs:commands$\\|^elisp$" line) nil)
       ;; Execute elisp
       ((string-match "^(" line)
        (condition-case err
            (let ((unescaped-line (replace-regexp-in-string "\\\\\"" "\"" line)))
              (eval (read unescaped-line))
              (setq executed-count (1+ executed-count))
              (when current-id
                (setq mcp-lisp-last-id current-id)))
          (error 
           (message "MCP Lisp error: %s" (error-message-string err)))))))
    
    (when (> executed-count 0)
      (message "✅ Executed %d new MCP Lisp commands" executed-count))
    executed-count))

(provide 'working-mcp-lisp-executor)