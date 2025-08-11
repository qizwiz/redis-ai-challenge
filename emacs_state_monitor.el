;; -*- lexical-binding: t; -*-
;; Emacs State Monitor - Continuously sync all Emacs state to Redis

(defvar emacs-state-monitor-active nil
  "Whether state monitoring is active")

(defvar emacs-state-last-update 0
  "Timestamp of last state update")

(defun emacs-state-start-monitoring ()
  "Start continuous Emacs state monitoring to Redis"
  (interactive)
  (setq emacs-state-monitor-active t)
  (message "🔍 Starting Emacs state monitoring to Redis")
  (emacs-state-update-loop))

(defun emacs-state-update-loop ()
  "Continuous loop to update Redis with current Emacs state"
  (when emacs-state-monitor-active
    (condition-case err
        (emacs-state-sync-to-redis)
      (error 
       (message "State sync error: %s" err)))
    ;; Update every 2 seconds
    (run-with-timer 2.0 nil #'emacs-state-update-loop)))

(defun emacs-state-sync-to-redis ()
  "Sync current Emacs state to Redis - ALL frames and windows"
  (let* ((current-time (format-time-string "%s"))
         ;; Get ALL frames and their focused windows
         (all-frames-info (mapcar (lambda (frame)
                                    (let* ((focused-window (frame-selected-window frame))
                                           (focused-buffer (window-buffer focused-window)))
                                      (list 'frame frame
                                            'buffer (buffer-name focused-buffer)
                                            'point (with-current-buffer focused-buffer (point))
                                            'line (with-current-buffer focused-buffer (line-number-at-pos))
                                            'column (with-current-buffer focused-buffer (current-column))
                                            'visible (frame-visible-p frame))))
                                  (frame-list)))
         ;; Find the most likely "current" frame (visible GUI frame)
         (gui-frame-info (seq-find (lambda (info) 
                                     (and (plist-get info 'visible)
                                          (not (string-match-p "daemon\\|server" 
                                                              (or (plist-get info 'buffer) "")))))
                                   all-frames-info))
         ;; Use GUI frame if found, otherwise use selected frame
         (active-frame-info (or gui-frame-info (car all-frames-info)))
         (buffer-name (plist-get active-frame-info 'buffer))
         (point-pos (plist-get active-frame-info 'point))
         (line-num (plist-get active-frame-info 'line))
         (column-num (plist-get active-frame-info 'column))
         (buffer-list-names (mapcar 'buffer-name (buffer-list))))
    
    ;; Update current buffer info with multi-frame tracking
    (shell-command-to-string 
     (format "redis-cli HSET emacs:current:buffer name '%s' point %d line %d column %d timestamp %s"
             (or buffer-name "unknown") (or point-pos 0) (or line-num 0) (or column-num 0) current-time))
    
    ;; Store ALL frame information for debugging
    (shell-command-to-string
     (format "redis-cli SET emacs:all:frames '%s'"
             (replace-regexp-in-string "'" "\\\\'" 
                                       (format "%S" all-frames-info))))
    
    ;; Update buffer list
    (shell-command-to-string
     (format "redis-cli SET emacs:current:buffers '%s'"
             (mapconcat 'identity buffer-list-names ",")))
    
    ;; Set current buffer as top priority key
    (shell-command-to-string
     (format "redis-cli SET emacs:current '%s'"
             (or buffer-name "unknown")))
    
    ;; Log state update
    (shell-command-to-string
     (format "redis-cli XADD emacs:state:log '*' action state_updated buffer '%s' point %d line %d timestamp %s"
             (or buffer-name "unknown") (or point-pos 0) (or line-num 0) current-time))
    
    (setq emacs-state-last-update (string-to-number current-time))))

(defun emacs-state-stop-monitoring ()
  "Stop state monitoring"
  (interactive)
  (setq emacs-state-monitor-active nil)
  (message "⏹️ Stopped Emacs state monitoring"))

(defun emacs-state-force-update ()
  "Force immediate state update to Redis"
  (interactive)
  (emacs-state-sync-to-redis)
  (message "🔄 State synced to Redis"))

;; Start monitoring automatically
(emacs-state-start-monitoring)

(provide 'emacs-state-monitor)