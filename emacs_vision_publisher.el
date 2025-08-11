;; emacs_vision_publisher.el --- Publishes Emacs state to Redis for persistent vision

(defvar emacs-vision-timer nil "Timer for periodically publishing Emacs state.")
(defvar emacs-vision-redis-key "emacs:facade" "Redis key to store Emacs live state.")
(defvar emacs-vision-publish-interval 0.1 "Interval in seconds to publish Emacs state.")

(defun emacs-vision-get-state ()
  "Collects relevant Emacs state information."
  (let* ((current-buffer (buffer-name (current-buffer)))
         (point (point))
         (line (line-number-at-pos))
         (column (current-column))
         (buffer-size (buffer-size))
         (window-list (mapcar (lambda (w) (buffer-name (window-buffer w))) (window-list)))
         (mode (symbol-name major-mode))
         (modified (buffer-modified-p))
         (timestamp (float-time)))
    (list
     (cons 'buffer current-buffer)
     (cons 'point point)
     (cons 'line line)
     (cons 'column column)
     (cons 'size buffer-size)
     (cons 'windows (length (window-list))) ;; Number of windows
     (cons 'visible-buffers window-list)
     (cons 'mode mode)
     (cons 'modified modified)
     (cons 'timestamp timestamp))))

(defun emacs-vision-publish-state ()
  "Publishes the current Emacs state to Redis."
  (interactive)
  (let* ((state (emacs-vision-get-state))
         (json-state (json-encode state))
         (command-string (format "redis-cli SET %s '%s'" emacs-vision-redis-key json-state))
         (shell-output (shell-command-to-string command-string)))
    
    ;;  ;; For debugging
    ))

(defun emacs-vision-start-publisher ()
  "Starts the periodic Emacs state publisher."
  (interactive)
  (when emacs-vision-timer
    (cancel-timer emacs-vision-timer))
  (setq emacs-vision-timer
        (run-with-timer 0 emacs-vision-publish-interval 'emacs-vision-publish-state))
  )
  

(defun emacs-vision-stop-publisher ()
  "Stops the periodic Emacs state publisher."
  (interactive)
  (when emacs-vision-timer
    (cancel-timer emacs-vision-timer)
    (setq emacs-vision-timer nil)))
  

(provide 'emacs-vision-publisher)

;; To start: M-x emacs-vision-start-publisher
;; To stop: M-x emacs-vision-stop-publisher
;; To manually publish: M-x emacs-vision-publish-state
