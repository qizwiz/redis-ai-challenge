;; -*- lexical-binding: t; -*-
;; Claude REPL - A conversational interface to Claude via Redis-MCP

(require 'json)

(defvar claude-repl-buffer "*Claude-REPL*")
(defvar claude-repl-history '())
(defvar claude-repl-history-index 0)
(defvar claude-repl-prompt "Claude> ")
(defvar claude-repl-user-prompt "You> ")

(defface claude-repl-prompt-face
  '((t :foreground "blue" :weight bold))
  "Face for Claude REPL prompts.")

(defface claude-repl-user-face
  '((t :foreground "green" :weight bold))
  "Face for user input in Claude REPL.")

(defface claude-repl-claude-face
  '((t :foreground "purple"))
  "Face for Claude responses.")

(defun claude-repl-create-buffer ()
  "Create and setup the Claude REPL buffer."
  (with-current-buffer (get-buffer-create claude-repl-buffer)
    (erase-buffer)
    (insert (propertize "=== Claude REPL ===" 'face 'claude-repl-prompt-face))
    (insert "\n")
    (insert (propertize "Integrated with Redis-MCP coordination system\n" 'face 'claude-repl-claude-face))
    (insert (propertize "Type your message and press RET to send to Claude\n" 'face 'claude-repl-claude-face))
    (insert (propertize "Use C-c C-c to clear buffer, C-c C-h for help\n\n" 'face 'claude-repl-claude-face))
    
    ;; Set up the buffer for interaction
    (claude-repl-mode)
    (goto-char (point-max))
    (claude-repl-insert-prompt)
    (current-buffer)))

(defun claude-repl-insert-prompt ()
  "Insert the user input prompt."
  (insert (propertize claude-repl-user-prompt 'face 'claude-repl-user-face)))

(defun claude-repl-send-message ()
  "Send the current input to Claude via Redis-MCP."
  (interactive)
  (let* ((prompt-start (save-excursion 
                         (beginning-of-line)
                         (when (looking-at (regexp-quote claude-repl-user-prompt))
                           (match-end 0))))
         (input (when prompt-start
                  (buffer-substring-no-properties prompt-start (point-max)))))
    
    (when (and input (not (string-empty-p (string-trim input))))
      ;; Add to history
      (push input claude-repl-history)
      (setq claude-repl-history-index 0)
      
      ;; Move to end and add newline
      (goto-char (point-max))
      (insert "\n")
      
      ;; Send to Claude via Redis
      (claude-repl-send-to-redis input)
      
      ;; Show "thinking" message
      (insert (propertize "Claude is thinking...\n\n" 'face 'claude-repl-claude-face))
      
      ;; Insert new prompt
      (claude-repl-insert-prompt))))

(defun claude-repl-send-to-redis (message)
  "Send message to Claude via Redis bridge."
  (let ((timestamp (format-time-string "%s")))
    
    ;; Store message in Redis stream for bridge to pick up
    (shell-command-to-string
     (format "redis-cli XADD claude:messages '*' message %s user %s timestamp %s"
             (shell-quote-argument message)
             (shell-quote-argument (user-login-name))
             (shell-quote-argument timestamp)))
    
    ;; Start checking for responses from bridge
    (run-with-timer 3.0 nil #'claude-repl-check-bridge-responses)))

(defun claude-repl-check-bridge-responses ()
  "Check Redis for responses from Claude bridge."
  (let ((responses (shell-command-to-string "redis-cli XRANGE claude:responses - + COUNT 10")))
    (when (and responses 
               (not (string-empty-p responses))
               (not (string-match-p "^(empty" responses)))
      ;; Parse and display responses
      (claude-repl-parse-and-display-responses responses)
      ;; Clear processed responses  
      (shell-command-to-string "redis-cli DEL claude:responses"))
    
    ;; Keep checking for more responses
    (run-with-timer 2.0 nil #'claude-repl-check-bridge-responses)))

(defun claude-repl-parse-and-display-responses (responses-data)
  "Parse Redis stream responses and display them."
  (let ((lines (split-string responses-data "\n")))
    (dolist (line lines)
      (when (string-match "response" line)
        ;; Extract response text (this is simplified parsing)
        (let ((response-start (string-match "response" line)))
          (when response-start
            (let ((response-text (substring line (+ response-start 8))))
              (when (> (length response-text) 0)
                (claude-repl-display-bridge-response response-text)))))))))

(defun claude-repl-check-response ()
  "Check Redis for response from claude-code."
  (let ((response (shell-command-to-string "redis-cli GET claude:response")))
    (when (and response 
               (not (string-empty-p response))
               (not (string-match-p "^(nil)" response)))
      (claude-repl-display-bridge-response (string-trim response))
      ;; Clear the response
      (shell-command-to-string "redis-cli DEL claude:response claude:response_timestamp"))))

(defun claude-repl-display-bridge-response (response)
  "Display response from claude-code bridge."
  (with-current-buffer claude-repl-buffer
    (goto-char (point-max))
    (forward-line -1)  ; Go before the current prompt
    (insert (propertize "Claude (via bridge): " 'face 'claude-repl-prompt-face))
    (insert (propertize response 'face 'claude-repl-claude-face))
    (insert "\n\n")
    (goto-char (point-max))))

(defun claude-repl-clear-buffer ()
  "Clear the Claude REPL buffer."
  (interactive)
  (erase-buffer)
  (claude-repl-create-buffer))

(defun claude-repl-help ()
  "Show help for Claude REPL."
  (interactive)
  (message "Claude REPL: RET=send, C-c C-c=clear, C-c C-h=help"))

(define-derived-mode claude-repl-mode fundamental-mode "Claude-REPL"
  "Major mode for Claude REPL interaction."
  ;; Key bindings
  (define-key claude-repl-mode-map (kbd "RET") #'claude-repl-send-message)
  (define-key claude-repl-mode-map (kbd "C-c C-c") #'claude-repl-clear-buffer)
  (define-key claude-repl-mode-map (kbd "C-c C-h") #'claude-repl-help))

;;;###autoload
(defun claude-repl ()
  "Start or switch to the Claude REPL."
  (interactive)
  (let ((buffer (claude-repl-create-buffer)))
    (pop-to-buffer buffer)
    (goto-char (point-max))
    (message "Claude REPL ready! Type your message and press RET.")))

(provide 'claude-repl)

;;; claude-repl.el ends here