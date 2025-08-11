;;; clean_ai_pair_programmer.el --- Clean AI pair programming integration

(defvar ai-pair-session-id nil "Current AI pair programming session")
(defvar ai-pair-enabled nil "Whether AI pair programming is active")
(defvar ai-pair-last-command nil "Last command to avoid spam")
(defvar ai-pair-command-count 0 "Commands since last AI update")

(defun ai-pair-start ()
  "Start clean AI pair programming mode"
  (interactive)
  (setq ai-pair-session-id (format "pair_%d_%d" (emacs-pid) (time-convert nil 'integer)))
  (setq ai-pair-enabled t)
  (setq ai-pair-command-count 0)
  
  ;; Only hook significant events, not every keystroke
  (add-hook 'after-save-hook #'ai-pair-on-save)
  (add-hook 'post-command-hook #'ai-pair-on-significant-command)
  
  ;; Send session start signal
  (ai-pair-send-event "session_start" 
                      `((buffer . ,(buffer-name))
                        (file . ,(buffer-file-name))
                        (major-mode . ,(symbol-name major-mode))))
  
  (message "🤖 AI Pair Programmer started (session: %s)" ai-pair-session-id))

(defun ai-pair-stop ()
  "Stop AI pair programming mode"
  (interactive)
  (setq ai-pair-enabled nil)
  (remove-hook 'after-save-hook #'ai-pair-on-save)
  (remove-hook 'post-command-hook #'ai-pair-on-significant-command)
  
  (when ai-pair-session-id
    (ai-pair-send-event "session_end" '()))
  
  (message "🤖 AI Pair Programmer stopped"))

(defun ai-pair-on-significant-command ()
  "Only send AI updates for significant commands, not every keystroke"
  (when (and ai-pair-enabled
             (not (eq this-command ai-pair-last-command)))
    
    (setq ai-pair-command-count (1+ ai-pair-command-count))
    (setq ai-pair-last-command this-command)
    
    ;; Only send updates for meaningful commands or every 10th command
    (when (or (>= ai-pair-command-count 10)
              (memq this-command '(newline
                                   yank
                                   kill-line
                                   beginning-of-line
                                   end-of-line
                                   forward-paragraph
                                   backward-paragraph)))
      
      (setq ai-pair-command-count 0)
      (ai-pair-send-context-update))))

(defun ai-pair-on-save ()
  "Send file save event to AI"
  (when ai-pair-enabled
    (ai-pair-send-event "file_saved" 
                        `((file . ,(buffer-file-name))
                          (buffer . ,(buffer-name))
                          (size . ,(buffer-size))))))

(defun ai-pair-send-context-update ()
  "Send current context to AI (non-spammy)"
  (ai-pair-send-event "context_update"
                      `((point . ,(point))
                        (line . ,(line-number-at-pos))
                        (buffer . ,(buffer-name))
                        (file . ,(buffer-file-name))
                        (command . ,(symbol-name this-command))
                        (region-active . ,(use-region-p))
                        (current-line . ,(thing-at-point 'line t)))))

(defun ai-pair-send-event (event-type data)
  "Send event to Redis for AI processing"
  (let ((event-data (append `((event_type . ,event-type)
                              (session . ,ai-pair-session-id)
                              (timestamp . ,(time-convert nil 'integer)))
                            data)))
    
    (start-process "redis-ai-event" nil "redis-cli" "XADD" "ai:pair_programming" "*"
                   "event" event-type
                   "session" ai-pair-session-id
                   "data" (json-encode event-data))))

(defun ai-pair-request-help (prompt)
  "Request AI assistance with specific prompt"
  (interactive "sWhat do you need help with? ")
  (ai-pair-send-event "help_request"
                      `((prompt . ,prompt)
                        (context . ,(buffer-substring-no-properties 
                                   (max (point-min) (- (point) 500))
                                   (min (point-max) (+ (point) 500)))))))

(defun ai-pair-show-suggestions ()
  "Show AI suggestions in separate buffer"
  (interactive)
  (let ((suggestions-buffer (get-buffer-create "*AI Suggestions*")))
    (with-current-buffer suggestions-buffer
      (erase-buffer)
      (insert "🤖 AI Pair Programming Suggestions\n")
      (insert "=====================================\n\n")
      (insert "Checking Redis for AI suggestions...\n"))
    (display-buffer suggestions-buffer)))

;; Key bindings for AI pair programming
(global-set-key (kbd "C-c a s") 'ai-pair-start)
(global-set-key (kbd "C-c a q") 'ai-pair-stop)
(global-set-key (kbd "C-c a h") 'ai-pair-request-help)
(global-set-key (kbd "C-c a ?") 'ai-pair-show-suggestions)

(provide 'clean_ai_pair_programmer)