;;; emacs_dream_interface.el --- The Ultimate Dream Interface in Emacs
;;; Using async-shell-command to call headless Claude Code with MCP

(defvar dream-interface-active nil "Whether dream interface is active")
(defvar dream-conversation-buffer "*Dream Interface*" "Buffer for dream conversations")

(defun dream-interface-start ()
  "Start the ultimate dream interface in Emacs"
  (interactive)
  (setq dream-interface-active t)
  
  ;; Create or switch to dream interface buffer
  (switch-to-buffer dream-conversation-buffer)
  (erase-buffer)
  
  ;; Setup the magical workspace
  (insert "✨ ULTIMATE DREAM INTERFACE ✨\n\n")
  (insert "🚀 Claude Code Headless + MCP Subagents + Emacs Async = MAGIC!\n\n")
  (insert "Just type naturally and press C-c C-d to send to AI...\n\n")
  (insert "🔮 Examples:\n")
  (insert "  • 'split the screen please'\n")
  (insert "  • 'show me the workspace'\n") 
  (insert "  • 'help me write some code'\n")
  (insert "  • 'create something amazing'\n\n")
  (insert "---\n\n")
  
  ;; Enable dream mode
  (dream-mode)
  (message "🌟 Dream Interface ACTIVE! Type naturally and press C-c C-d"))

(defun dream-send-to-ai (prompt)
  "Send prompt to Claude Code headless with MCP integration"
  (interactive "sWhat would you like to do? ")
  
  (let ((command (format "echo '%s' | claude -p 'Use the subagent-coordinator MCP to handle this naturally: ' --mcp-config .mcp.json" 
                        (shell-quote-argument prompt))))
    
    ;; Insert user input into conversation
    (with-current-buffer dream-conversation-buffer
      (goto-char (point-max))
      (insert (format "💭 You: %s\n\n" prompt))
      
      ;; Show thinking indicator
      (insert "🤖 AI is thinking...\n")
      (redisplay))
    
    ;; Call Claude async and handle response
    (async-shell-command command "*Dream AI Response*")
    
    ;; Set up response handling
    (with-current-buffer "*Dream AI Response*"
      (add-hook 'comint-output-filter-functions 'dream-handle-ai-response nil t))))

(defun dream-handle-ai-response (output)
  "Handle AI response and integrate into conversation"
  (when (get-buffer "*Dream AI Response*")
    (with-current-buffer "*Dream AI Response*"
      (let ((response (buffer-string)))
        (when (and response (not (string-empty-p (string-trim response))))
          
          ;; Add response to conversation buffer
          (with-current-buffer dream-conversation-buffer
            (goto-char (point-max))
            ;; Remove thinking indicator
            (when (search-backward "🤖 AI is thinking..." nil t)
              (delete-region (point) (point-max)))
            
            ;; Add AI response
            (insert (format "🤖 AI: %s\n\n" (string-trim response)))
            (insert "---\n\n")
            (goto-char (point-max))
            (redisplay))
          
          ;; Kill the response buffer
          (kill-buffer "*Dream AI Response*"))))))

(defun dream-quick-command ()
  "Quick command input for dream interface"
  (interactive)
  (let ((prompt (read-string "💭 Dream command: ")))
    (dream-send-to-ai prompt)))

(defun dream-workspace-setup ()
  "Setup magical AI workspace"
  (interactive)
  (dream-send-to-ai "start magical session"))

(defun dream-split-and-chat ()
  "Split window and start dream interface"
  (interactive)
  (split-window-right)
  (other-window 1)
  (dream-interface-start))

;; Dream mode keymap
(defvar dream-mode-map
  (let ((map (make-sparse-keymap)))
    (define-key map (kbd "C-c C-d") 'dream-quick-command)
    (define-key map (kbd "C-c C-w") 'dream-workspace-setup)
    (define-key map (kbd "C-c C-s") 'dream-split-and-chat)
    (define-key map (kbd "C-c C-q") 'dream-interface-quit)
    map)
  "Keymap for dream interface mode")

(define-minor-mode dream-mode
  "Minor mode for the ultimate dream interface"
  :lighter " 🌟Dream"
  :keymap dream-mode-map
  (if dream-mode
      (message "🌟 Dream mode active! C-c C-d to send commands")
    (message "Dream mode deactivated")))

(defun dream-interface-quit ()
  "Quit dream interface"
  (interactive)
  (setq dream-interface-active nil)
  (dream-mode -1)
  (message "✨ Dream interface deactivated. Sweet dreams!"))

;; Magic aliases for quick access
(defalias 'dream 'dream-interface-start)
(defalias 'magic 'dream-interface-start)
(defalias 'ai-chat 'dream-interface-start)

(provide 'emacs-dream-interface)

;; Usage:
;; (load "emacs_dream_interface.el")
;; M-x dream
;; Type naturally, press C-c C-d
;; MAGIC! ✨