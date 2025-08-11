;;; redis-ai-natural-lang.el --- Natural Language Commands for Redis AI Emacs mode

;;; Code:

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

(provide 'redis-ai-natural-lang)
;;; redis-ai-natural-lang.el ends here
