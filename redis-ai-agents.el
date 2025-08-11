;;; redis-ai-agents.el --- AI Workforce Control functions for Redis AI Emacs mode

;;; Code:

(defvar redis-ai-active-agents '()
  "List of currently active AI agents.")

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

(provide 'redis-ai-agents)
;;; redis-ai-agents.el ends here
