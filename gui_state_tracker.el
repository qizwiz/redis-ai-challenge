;; -*- lexical-binding: t; -*-
;; GUI State Tracker - Run this directly in your GUI Emacs

(defvar gui-state-active nil)

(defun gui-start-state-tracking ()
  "Start state tracking from GUI Emacs"
  (interactive)
  (setq gui-state-active t)
  (message "🎯 GUI state tracking started")
  (gui-state-loop))

(defun gui-state-loop ()
  "State tracking loop"
  (when gui-state-active
    (condition-case err
        (gui-sync-state)
      (error (message "GUI state error: %s" err)))
    (run-with-timer 2.0 nil #'gui-state-loop)))

(defun gui-sync-state ()
  "Sync GUI state to Redis"
  (let* ((buf (buffer-name))
         (pt (point))
         (ln (line-number-at-pos))
         (col (current-column))
         (ts (format-time-string "%s")))
    
    ;; Set current buffer
    (shell-command-to-string 
     (format "redis-cli SET emacs:current '%s'" buf))
    
    ;; Set detailed state
    (shell-command-to-string
     (format "redis-cli HSET emacs:state buffer '%s' point %d line %d column %d timestamp %s"
             buf pt ln col ts))
    
    ;; Visual confirmation
    (message "📡 Synced: %s (line %d)" buf ln)))

(defun gui-stop-state-tracking ()
  "Stop state tracking"
  (interactive)
  (setq gui-state-active nil)
  (message "⏹️ GUI state tracking stopped"))

;; Auto-start
(gui-start-state-tracking)

(provide 'gui-state-tracker)