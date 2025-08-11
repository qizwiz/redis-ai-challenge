;;; controlled_mcp_lisp.el --- Controlled MCP Lisp Execution

(defvar mcp-lisp-last-processed "0" "Last processed message ID")

(defun mcp-lisp-execute-once ()
  "Execute new MCP Lisp commands once only"
  (interactive)
  (let* ((cmd (format "redis-cli XREAD STREAMS emacs:commands %s" mcp-lisp-last-processed))
         (output (shell-command-to-string cmd))
         (lines (split-string output "\n" t))
         (current-id nil)
         (executed 0))
    
    (dolist (line lines)
      (cond
       ;; Message ID line
       ((string-match "^\\([0-9]+-[0-9]+\\)$" line)
        (setq current-id (match-string 1 line)))
       ;; Skip stream name and field name
       ((string-match-p "^emacs:commands$\\|^elisp$" line)
        nil)
       ;; Execute elisp
       ((string-match-p "^(" line)
        (condition-case err
            (progn
              (eval (read line))
              (setq executed (1+ executed))
              (when current-id
                (setq mcp-lisp-last-processed current-id)))
          (error 
           (message "MCP Lisp error: %s" (error-message-string err)))))))
    
    (when (> executed 0)
      (message "Executed %d MCP Lisp commands" executed))))

(defun mcp-lisp-status ()
  "Show MCP Lisp execution status"
  (interactive)
  (message "Last processed: %s" mcp-lisp-last-processed))

(provide 'controlled-mcp-lisp)