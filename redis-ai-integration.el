;;; redis-ai-integration.el --- Real-time Development Integration functions for Redis AI Emacs mode

;;; Code:

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

(provide 'redis-ai-integration)
;;; redis-ai-integration.el ends here
