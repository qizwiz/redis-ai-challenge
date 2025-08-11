;;; check_minibuffer_state.el --- Check what's happening in minibuffer

;; -*- lexical-binding: t -*-

(defun check-minibuffer-state ()
  "Check current minibuffer and timer state"
  (interactive)
  
  (with-current-buffer (get-buffer-create "*MINIBUFFER-DEBUG*")
    (erase-buffer)
    (insert "🔍 MINIBUFFER STATE DEBUG\n")
    (insert "========================\n\n")
    
    ;; Current message
    (insert (format "Current message: '%s'\n" (or (current-message) "none")))
    (insert (format "Last message: '%s'\n\n" (or (and (boundp 'last-message) last-message) "none")))
    
    ;; Active timers
    (insert "ACTIVE TIMERS:\n")
    (let ((timer-count 0))
      (dolist (timer timer-list)
        (when timer
          (setq timer-count (1+ timer-count))
          (insert (format "Timer %d: %s (repeats: %s)\n" 
                         timer-count
                         (timer--function timer)
                         (timer--repeat-delay timer)))))
      (insert (format "Total active timers: %d\n\n" timer-count)))
    
    ;; Check for our message delivery timers specifically
    (insert "MESSAGE DELIVERY TIMERS:\n")
    (when (boundp 'msg-timers)
      (let ((msg-timer-count 0))
        (maphash (lambda (key timer)
                   (setq msg-timer-count (1+ msg-timer-count))
                   (insert (format "- %s: %s\n" key timer)))
                 msg-timers)
        (insert (format "MSG timers: %d\n" msg-timer-count))))
    
    ;; Check for other timer variables
    (insert "\nOTHER TIMER VARIABLES:\n")
    (dolist (var '(message-delivery-timers supervision-monitor-timer 
                   claude-status-timer actor-message-timer))
      (when (boundp var)
        (let ((val (symbol-value var)))
          (insert (format "- %s: %s\n" var val)))))
    
    ;; Current buffers with message patterns
    (insert "\nBUFFERS WITH MESSAGE ACTIVITY:\n")
    (dolist (buf (buffer-list))
      (when (string-match-p "\\*.*\\(message\\|log\\|error\\|status\\).*\\*" (buffer-name buf))
        (insert (format "- %s (%d chars)\n" 
                       (buffer-name buf)
                       (buffer-size buf)))))
    
    ;; Redis processes
    (insert "\nREDIS PROCESSES:\n")
    (dolist (proc (process-list))
      (when (string-match-p "redis" (process-name proc))
        (insert (format "- %s: %s\n" 
                       (process-name proc)
                       (process-status proc)))))
    
    (goto-char (point-min))
    (pop-to-buffer (current-buffer))))

(defun kill-all-message-timers ()
  "Kill all message delivery related timers"
  (interactive)
  
  ;; Kill our specific timers
  (when (boundp 'msg-timers)
    (maphash (lambda (_key timer)
               (when timer (cancel-timer timer)))
             msg-timers)
    (clrhash msg-timers))
  
  ;; Kill other timer variables
  (dolist (var '(message-delivery-timers supervision-monitor-timer 
                 claude-status-timer actor-message-timer))
    (when (boundp var)
      (let ((timer (symbol-value var)))
        (when timer 
          (if (listp timer)
              (dolist (t timer) (when t (cancel-timer t)))
            (cancel-timer timer))
          (set var nil)))))
  
  ;; Kill any timers with message-related functions
  (dolist (timer timer-list)
    (when timer
      (let ((func (timer--function timer)))
        (when (and func 
                   (or (string-match-p "msg-" (format "%s" func))
                       (string-match-p "message" (format "%s" func))
                       (string-match-p "claude" (format "%s" func))))
          (cancel-timer timer)))))
  
  (message "🛑 Killed all message timers"))

;; Run the check immediately
(check-minibuffer-state)

(provide 'check-minibuffer-state)