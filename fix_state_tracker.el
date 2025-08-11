;; -*- lexical-binding: t; -*-
;; FIXED State Tracker - Actually works

(defvar fix-state-active nil)

(defun fix-start-tracking ()
  "Start ACTUAL state tracking"
  (interactive)
  (setq fix-state-active t)
  (message "🔧 FIXED state tracker started")
  (fix-update-loop))

(defun fix-update-loop ()
  "Update loop that actually works"
  (when fix-state-active
    (condition-case err
        (fix-sync-real-state)
      (error (message "Fix sync error: %s" err)))
    (run-with-timer 1.0 nil #'fix-update-loop)))

(defun fix-sync-real-state ()
  "Sync the ACTUAL current state"
  (let* ((current-buf (buffer-name (current-buffer)))
         (current-point (point))
         (current-line (line-number-at-pos))
         (current-col (current-column))
         (timestamp (format-time-string "%s")))
    
    ;; Set the current buffer name as top-level key
    (shell-command-to-string 
     (format "redis-cli SET emacs:current '%s'" current-buf))
    
    ;; Set detailed state
    (shell-command-to-string
     (format "redis-cli HSET emacs:state buffer '%s' point %d line %d column %d timestamp %s"
             current-buf current-point current-line current-col timestamp))
    
    ;; Log the update
    (shell-command-to-string
     (format "redis-cli XADD emacs:updates '*' buffer '%s' point %d line %d timestamp %s"
             current-buf current-point current-line timestamp))))

(defun fix-stop-tracking ()
  "Stop tracking"
  (interactive)
  (setq fix-state-active nil)
  (message "⏹️ Fixed tracker stopped"))

;; Auto-start
(fix-start-tracking)

(provide 'fix-state-tracker)