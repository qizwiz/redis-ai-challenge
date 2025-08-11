;;; redis-ai-emacs-mode.el --- Emacs minor mode for Redis AI workforce control

;;; Commentary:
;; This minor mode connects Emacs to the Redis AI workforce system,
;; allowing real-time control of autonomous AI agents from within Emacs.
;; Implements the composable event server pattern for homoiconic development.

;;; Code:

(require 'json)
(require 'cl-lib)

(defgroup redis-ai nil
  "Redis AI workforce integration for Emacs"
  :group 'tools
  :prefix "redis-ai-")

(defcustom redis-ai-host "localhost"
  "Redis server host"
  :type 'string
  :group 'redis-ai)

(defcustom redis-ai-port 6379
  "Redis server port"
  :type 'integer
  :group 'redis-ai)

(defcustom redis-ai-mcp-server-port 8881
  "MCP Redis Lisp server port"
  :type 'integer
  :group 'redis-ai)

(defvar redis-ai-mode nil
  "Non-nil if Redis AI mode is enabled.")

(defvar redis-ai-connection nil
  "Redis connection process.")

(defvar redis-ai-event-handlers (make-hash-table :test 'equal)
  "Hash table of event type to handler function mappings.")

(defvar redis-ai-active-agents '()
  "List of currently active AI agents.")

(defvar redis-ai-command-history '()
  "History of Redis AI commands.")

;;;; Core Redis Communication

(defun redis-ai-connect ()
  "Connect to Redis server."
  (interactive)
  (when redis-ai-connection
    (delete-process redis-ai-connection))
  
  (setq redis-ai-connection
        (make-network-process
         :name "redis-ai"
         :host redis-ai-host
         :port redis-ai-port
         :filter 'redis-ai-filter
         :sentinel 'redis-ai-sentinel))
  
  (when redis-ai-connection
    (message "✅ Connected to Redis AI system at %s:%d" redis-ai-host redis-ai-port)
    (redis-ai-initialize-event-handlers)
    (redis-ai-start-monitoring)))

(defun redis-ai-disconnect ()
  "Disconnect from Redis server."
  (interactive)
  (when redis-ai-connection
    (delete-process redis-ai-connection)
    (setq redis-ai-connection nil)
    (message "Disconnected from Redis AI system")))

(defun redis-ai-send-command (command)
  "Send COMMAND to Redis server."
  (when redis-ai-connection
    (process-send-string redis-ai-connection 
                         (format "%s\r\n" command))
    (push command redis-ai-command-history)))

(defun redis-ai-filter (proc string)
  "Process filter for Redis AI connection."
  (let ((response (string-trim string)))
    (when (> (length response) 0)
      (redis-ai-handle-response response))))

(defun redis-ai-sentinel (proc event)
  "Process sentinel for Redis AI connection."
  (message "Redis AI connection: %s" (string-trim event)))

;;;; Event System - Composable Event Servers

(defun redis-ai-register-event-handler (event-type handler-func)
  "Register HANDLER-FUNC for EVENT-TYPE in the composable event system."
  (puthash event-type handler-func redis-ai-event-handlers)
  (message "Registered handler for event: %s" event-type))

(defun redis-ai-handle-response (response)
  "Handle RESPONSE from Redis using registered event handlers."
  (condition-case err
      (let* ((data (json-read-from-string response))
             (event-type (alist-get 'type data))
             (handler (gethash event-type redis-ai-event-handlers)))
        (if handler
            (funcall handler data)
          (redis-ai-handle-default-response data)))
    (error
     (message "Redis AI response parse error: %s" (error-message-string err)))))

(defun redis-ai-handle-default-response (data)
  "Default handler for unrecognized Redis responses."
  (message "Redis AI: %s" (prin1-to-string data)))

;;;; AI Workforce Control

(defun redis-ai-list-agents ()
  "List all active AI agents."
  (interactive)
  (redis-ai-send-command "KEYS agent:*:status")
  (message "Listing active AI agents..."))

(defun redis-ai-assign-work (agent-id task-description target-files)
  "Assign work to AGENT-ID with TASK-DESCRIPTION for TARGET-FILES."
  (interactive 
   (list (completing-read "Agent ID: " redis-ai-active-agents)
         (read-string "Task description: ")
         (list (buffer-file-name))))
  
  (let ((work-data (json-encode 
                    `((task_type . "custom")
                      (description . ,task-description)
                      (target_files . ,target-files)
                      (priority . 5)
                      (estimated_duration . 30)))))
    (redis-ai-send-command 
     (format "LPUSH agent_work:%s %s" agent-id work-data))
    (message "✅ Assigned work to %s: %s" agent-id task-description)))

(defun redis-ai-generate-tests-for-buffer ()
  "Generate tests for the current buffer using AI agents."
  (interactive)
  (if (buffer-file-name)
      (let ((file-path (buffer-file-name)))
        (redis-ai-assign-work "test_agent_01" 
                              (format "Generate comprehensive tests for %s" 
                                      (file-name-nondirectory file-path))
                              (list file-path)))
    (message "Buffer has no associated file")))

(defun redis-ai-document-buffer ()
  "Generate documentation for functions in current buffer."
  (interactive)
  (if (buffer-file-name)
      (let ((file-path (buffer-file-name)))
        (redis-ai-assign-work "doc_agent_01"
                              (format "Add docstrings to complex functions in %s"
                                      (file-name-nondirectory file-path))
                              (list file-path)))
    (message "Buffer has no associated file")))

(defun redis-ai-refactor-buffer ()
  "Refactor current buffer using AI agents."
  (interactive)
  (if (buffer-file-name)
      (let ((file-path (buffer-file-name)))
        (redis-ai-assign-work "refactor_agent_01"
                              (format "Intelligently refactor %s for better code quality"
                                      (file-name-nondirectory file-path))
                              (list file-path)))
    (message "Buffer has no associated file")))

;;;; MCP Lisp Integration - Homoiconic Commands

(defun redis-ai-execute-lisp (lisp-expr)
  "Execute LISP-EXPR using the MCP Redis Lisp server."
  (interactive "sLisp expression: ")
  (let ((json-expr (json-encode (read lisp-expr))))
    (redis-ai-send-mcp-command "execute_lisp" 
                               `((code . ,json-expr)))
    (message "Executing Lisp: %s" lisp-expr)))

(defun redis-ai-store-lisp-code (key lisp-code)
  "Store LISP-CODE under KEY in Redis for later execution."
  (interactive "sKey: 
sLisp code: ")
  (let ((json-code (json-encode (read lisp-code))))
    (redis-ai-send-mcp-command "store_lisp_code"
                               `((key . ,key)
                                 (code . ,json-code)))
    (message "Stored Lisp code under key: %s" key)))

(defun redis-ai-execute-stored-lisp (key)
  "Execute Lisp code stored under KEY."
  (interactive "sKey: ")
  (redis-ai-send-mcp-command "execute_stored_lisp"
                             `((key . ,key)))
  (message "Executing stored Lisp code: %s" key))

(defun redis-ai-send-mcp-command (tool-name args)
  "Send MCP command to Redis Lisp server."
  (let ((mcp-request (json-encode 
                      `((jsonrpc . "2.0")
                        (method . "tools/call")
                        (params . ((name . ,tool-name)
                                   (arguments . ,args)))
                        (id . ,(random 10000))))))
    ;; For now, send via Redis - could be direct HTTP in full implementation
    (redis-ai-send-command 
     (format "LPUSH mcp:requests %s" mcp-request))))

;;;; Real-time Development Integration

(defun redis-ai-on-buffer-save ()
  "Hook function called when buffer is saved."
  (when (and redis-ai-mode (buffer-file-name))
    (let ((file-path (buffer-file-name)))
      ;; Automatically analyze saved files for work opportunities
      (redis-ai-send-command
       (format "LPUSH file_changes %s" 
               (json-encode `((file . ,file-path)
                              (event . "saved")
                              (timestamp . ,(current-time-string))))))
      (message "Redis AI: Notified agents of file save"))))

(defun redis-ai-smart-completion ()
  "Provide AI-powered completion suggestions."
  (interactive)
  (let* ((current-symbol (thing-at-point 'symbol))
         (context (buffer-substring-no-properties
                   (max (point-min) (- (point) 200))
                   (min (point-max) (+ (point) 200)))))
    (when current-symbol
      (redis-ai-send-command
       (format "LPUSH completion_requests %s"
               (json-encode `((symbol . ,current-symbol)
                              (context . ,context)
                              (buffer . ,(buffer-name))
                              (file . ,(buffer-file-name))))))
      (message "Requesting AI completion for: %s" current-symbol))))

;;;; Natural Language Commands

(defun redis-ai-natural-command (command)
  "Execute natural language COMMAND via AI agents."
  (interactive "sNatural command: ")
  (redis-ai-send-command
   (format "LPUSH natural_commands %s"
           (json-encode `((command . ,command)
                          (buffer . ,(buffer-name))
                          (file . ,(buffer-file-name))
                          (point . ,(point))
                          (mode . ,major-mode)))))
  (message "Executing natural command: %s" command))

(defun redis-ai-explain-code ()
  "Explain the code at point using AI."
  (interactive)
  (let ((code-region (if (region-active-p)
                         (buffer-substring-no-properties (region-beginning) (region-end))
                       (thing-at-point 'defun))))
    (when code-region
      (redis-ai-natural-command (format "Explain this code: %s" code-region)))))

(defun redis-ai-optimize-function ()
  "Optimize function at point using AI."
  (interactive)
  (redis-ai-natural-command "Optimize the function at point for performance and readability"))

;;;; Event Handlers

(defun redis-ai-initialize-event-handlers ()
  "Initialize event handlers for composable event system."
  (redis-ai-register-event-handler "agent_status" 'redis-ai-handle-agent-status)
  (redis-ai-register-event-handler "work_completed" 'redis-ai-handle-work-completed)
  (redis-ai-register-event-handler "error" 'redis-ai-handle-error)
  (redis-ai-register-event-handler "lisp_result" 'redis-ai-handle-lisp-result)
  (redis-ai-register-event-handler "completion" 'redis-ai-handle-completion))

(defun redis-ai-handle-agent-status (data)
  "Handle agent status updates."
  (let ((agent-id (alist-get 'agent_id data))
        (status (alist-get 'status data)))
    (message "Agent %s: %s" agent-id status)
    (cl-pushnew agent-id redis-ai-active-agents :test 'string=)))

(defun redis-ai-handle-work-completed (data)
  "Handle work completion notifications."
  (let ((task (alist-get 'task data))
        (artifacts (alist-get 'artifacts data)))
    (message "✅ Work completed: %s" task)
    (when artifacts
      (dolist (artifact artifacts)
        (when (file-exists-p artifact)
          (message "📄 Created: %s" artifact)
          ;; Optionally open created files
          (when (y-or-n-p (format "Open %s? " artifact))
            (find-file artifact)))))))

(defun redis-ai-handle-error (data)
  "Handle error notifications."
  (let ((error-msg (alist-get 'message data)))
    (message "⚠️ Redis AI Error: %s" error-msg)))

(defun redis-ai-handle-lisp-result (data)
  "Handle Lisp execution results."
  (let ((result (alist-get 'result data))
        (code (alist-get 'code data)))
    (message "Lisp result: %s → %s" code result)
    ;; Could display in a dedicated buffer
    (with-current-buffer (get-buffer-create "*Redis AI Lisp*")
      (goto-char (point-max))
      (insert (format "%s → %s\n" code result)))))

(defun redis-ai-handle-completion (data)
  "Handle completion suggestions."
  (let ((suggestions (alist-get 'suggestions data)))
    (when suggestions
      (let ((choice (completing-read "AI suggestion: " suggestions)))
        (when choice
          (delete-region (save-excursion (skip-syntax-backward "w_") (point)) (point))
          (insert choice))))))

;;;; Monitoring and Status

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
      (insert "🤖 Redis AI Workforce Dashboard\n")
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

;;;; Mode Definition

(defvar redis-ai-mode-map
  (let ((map (make-sparse-keymap)))
    (define-key map (kbd "C-c r c") 'redis-ai-connect)
    (define-key map (kbd "C-c r d") 'redis-ai-disconnect)
    (define-key map (kbd "C-c r t") 'redis-ai-generate-tests-for-buffer)
    (define-key map (kbd "C-c r o") 'redis-ai-document-buffer)
    (define-key map (kbd "C-c r r") 'redis-ai-refactor-buffer)
    (define-key map (kbd "C-c r l") 'redis-ai-execute-lisp)
    (define-key map (kbd "C-c r s") 'redis-ai-store-lisp-code)
    (define-key map (kbd "C-c r e") 'redis-ai-execute-stored-lisp)
    (define-key map (kbd "C-c r n") 'redis-ai-natural-command)
    (define-key map (kbd "C-c r ?") 'redis-ai-explain-code)
    (define-key map (kbd "C-c r +") 'redis-ai-optimize-function)
    (define-key map (kbd "C-c r TAB") 'redis-ai-smart-completion)
    (define-key map (kbd "C-c r a") 'redis-ai-list-agents)
    (define-key map (kbd "C-c r D") 'redis-ai-show-dashboard)
    map)
  "Keymap for Redis AI mode.")

;;;###autoload
(define-minor-mode redis-ai-mode
  "Minor mode for Redis AI workforce integration.
  
This mode connects Emacs to a Redis-based AI workforce system,
enabling real-time AI assistance, code generation, testing,
documentation, and homoiconic Lisp execution.

Key bindings:
\{redis-ai-mode-map}"
  :init-value nil
  :lighter " 🤖"
  :keymap redis-ai-mode-map
  :group 'redis-ai
  
  (if redis-ai-mode
      (progn
        (add-hook 'after-save-hook 'redis-ai-on-buffer-save nil t)
        (message "Redis AI mode enabled - Use C-c r c to connect"))
    (progn
      (remove-hook 'after-save-hook 'redis-ai-on-buffer-save t)
      (redis-ai-disconnect)
      (message "Redis AI mode disabled"))))

;;;###autoload
(defun redis-ai-global-mode-enable ()
  "Enable Redis AI mode globally."
  (interactive)
  (add-hook 'prog-mode-hook 'redis-ai-mode)
  (message "Redis AI mode enabled globally for programming modes"))

(provide 'redis-ai-emacs-mode)

;;; redis-ai-emacs-mode.el ends here
