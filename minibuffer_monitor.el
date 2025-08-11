;;; minibuffer_monitor.el --- Monitor minibuffer activity

;; -*- lexical-binding: t -*-

(defvar minibuffer-monitor-timer nil)
(defvar minibuffer-monitor-log '())
(defvar minibuffer-last-message "")

(defun minibuffer-monitor-tick ()
  "Monitor minibuffer changes"
  (let ((current-msg (or (current-message) "")))
    (unless (string= current-msg minibuffer-last-message)
      (let ((timestamp (format-time-string "%H:%M:%S.%3N")))
        (push (list timestamp current-msg) minibuffer-monitor-log)
        (setq minibuffer-last-message current-msg)
        
        ;; Keep log size manageable
        (when (> (length minibuffer-monitor-log) 100)
          (setq minibuffer-monitor-log (seq-take minibuffer-monitor-log 100)))))))

(defun start-minibuffer-monitor ()
  "Start monitoring minibuffer"
  (interactive)
  (when minibuffer-monitor-timer
    (cancel-timer minibuffer-monitor-timer))
  
  (setq minibuffer-monitor-timer 
        (run-with-timer 0 0.1 'minibuffer-monitor-tick))
  (setq minibuffer-monitor-log '())
  (setq minibuffer-last-message (or (current-message) ""))
  (message "🔍 Minibuffer monitor started"))

(defun stop-minibuffer-monitor ()
  "Stop monitoring minibuffer"
  (interactive)
  (when minibuffer-monitor-timer
    (cancel-timer minibuffer-monitor-timer)
    (setq minibuffer-monitor-timer nil))
  (message "🛑 Minibuffer monitor stopped"))

(defun show-minibuffer-log ()
  "Show recent minibuffer activity"
  (interactive)
  (with-current-buffer (get-buffer-create "*MINIBUFFER-LOG*")
    (erase-buffer)
    (insert "🔍 MINIBUFFER ACTIVITY LOG\n")
    (insert "===========================\n\n")
    
    (if minibuffer-monitor-log
        (dolist (entry (reverse minibuffer-monitor-log))
          (insert (format "[%s] %s\n" (car entry) (cadr entry))))
      (insert "No activity logged yet.\n"))
    
    (goto-char (point-max))
    (pop-to-buffer (current-buffer))))

;; Start monitoring immediately
(start-minibuffer-monitor)

(provide 'minibuffer-monitor)