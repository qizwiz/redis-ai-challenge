;;; redis-ai-events.el --- Event handling for Redis AI Emacs mode

;;; Code:

(require 'json)
(require 'cl-lib)

(defvar redis-ai-event-handlers (make-hash-table :test 'equal)
  "Hash table of event type to handler function mappings.")

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

(provide 'redis-ai-events)
;;; redis-ai-events.el ends here
