;;; composable-modes.el --- Composable AI Development Modes -*- lexical-binding: t; -*-

;; Copyright (C) 2025 Redis AI Challenge
;; Author: Autonomous AI Workforce
;; Version: 1.0.0
;; Package-Requires: ((emacs "27.1") (redis "0.1"))

;;; Commentary:
;;
;; Revolutionary composable minor modes for AI-assisted development.
;; Each mode is a Redis-coordinated microservice that can be combined
;; to create custom development environments.
;;
;; Instead of being locked into rigid IDEs, you compose exactly the
;; intelligence you need for your current task.

;;; Code:

(require 'redis)
(require 'json)

;;; Core Composable Mode Framework

(defvar redis-ai-connection nil
  "Redis connection for AI coordination.")

(defvar redis-ai-active-modes '()
  "List of currently active AI modes.")

(defvar redis-ai-mode-registry '()
  "Registry of available composable modes.")

(defvar redis-ai-intent-stream "reactive:intents"
  "Redis stream for user intents.")

(defvar redis-ai-response-stream "reactive:responses"
  "Redis stream for AI responses.")

;;; Mode Definition Framework

(defmacro define-redis-ai-mode (name &rest body)
  "Define a composable Redis AI mode.
NAME is the mode name, BODY contains mode configuration."
  (declare (indent 1))
  (let* ((mode-symbol (intern (format "redis-ai-%s-mode" name)))
         (activate-fn (intern (format "redis-ai-%s-activate" name)))
         (deactivate-fn (intern (format "redis-ai-%s-deactivate" name)))
         (config (plist-get body :config))
         (keybindings (plist-get body :keybindings))
         (hooks (plist-get body :hooks))
         (agents (plist-get body :agents)))
    
    `(progn
       ;; Register the mode
       (add-to-list 'redis-ai-mode-registry 
                    '(,name . ,(list :config config 
                                    :keybindings keybindings
                                    :hooks hooks
                                    :agents agents)))
       
       ;; Define activation function
       (defun ,activate-fn ()
         ,(format "Activate %s mode" name)
         (interactive)
         (redis-ai-activate-mode ',name))
       
       ;; Define deactivation function  
       (defun ,deactivate-fn ()
         ,(format "Deactivate %s mode" name)
         (interactive)
         (redis-ai-deactivate-mode ',name))
       
       ;; Define the minor mode
       (define-minor-mode ,mode-symbol
         ,(format "Redis AI %s mode" name)
         :lighter ,(format " AI-%s" (upcase (symbol-name name)))
         :keymap nil
         (if ,mode-symbol
             (,activate-fn)
           (,deactivate-fn))))))

;;; Core Mode Management

(defun redis-ai-connect ()
  "Connect to Redis for AI coordination."
  (interactive)
  (unless redis-ai-connection
    (setq redis-ai-connection (redis-connect "localhost" 6379))
    (message "✅ Connected to Redis AI coordination layer")))

(defun redis-ai-activate-mode (mode-name)
  "Activate a composable AI mode."
  (redis-ai-connect)
  
  (let ((mode-config (cdr (assoc mode-name redis-ai-mode-registry))))
    (when mode-config
      ;; Add to active modes
      (add-to-list 'redis-ai-active-modes mode-name)
      
      ;; Set up keybindings
      (when-let ((keybindings (plist-get mode-config :keybindings)))
        (redis-ai-setup-keybindings keybindings))
      
      ;; Install hooks
      (when-let ((hooks (plist-get mode-config :hooks)))
        (redis-ai-install-hooks hooks))
      
      ;; Notify Redis about mode activation
      (redis-ai-send-intent 'mode-switch 
                           (format "activate %s" mode-name)
                           `((mode . ,mode-name)
                             (config . ,(plist-get mode-config :config))))
      
      (message "🚀 Activated %s mode" mode-name))))

(defun redis-ai-deactivate-mode (mode-name)
  "Deactivate a composable AI mode."
  (setq redis-ai-active-modes (remove mode-name redis-ai-active-modes))
  
  ;; Notify Redis about deactivation
  (redis-ai-send-intent 'mode-switch 
                       (format "deactivate %s" mode-name)
                       `((mode . ,mode-name)))
  
  (message "🛑 Deactivated %s mode" mode-name))

;;; Intent Capture System

(defun redis-ai-send-intent (type content context)
  "Send user intent to Redis for AI processing."
  (when redis-ai-connection
    (let ((intent `((id . ,(format "emacs_%d" (time-convert nil 'integer)))
                    (type . ,(symbol-name type))
                    (content . ,content)
                    (context . ,context)
                    (timestamp . ,(time-convert nil 'integer))
                    (source . "emacs"))))
      
      (redis-xadd redis-ai-connection 
                  redis-ai-intent-stream
                  "*"
                  (mapcar (lambda (pair)
                            (list (symbol-name (car pair))
                                  (if (stringp (cdr pair))
                                      (cdr pair)
                                    (json-encode (cdr pair)))))
                          intent)))))

(defun redis-ai-capture-keystroke ()
  "Capture and analyze keystrokes for intelligent prediction."
  (interactive)
  (let ((context `((buffer . ,(buffer-name))
                   (point . ,(point))
                   (line . ,(line-number-at-pos))
                   (column . ,(current-column))
                   (major-mode . ,(symbol-name major-mode))
                   (last-char . ,(char-before))
                   (word-at-point . ,(thing-at-point 'word))
                   (line-content . ,(thing-at-point 'line)))))
    
    (redis-ai-send-intent 'keystroke 
                         (string last-command-event)
                         context)))

(defun redis-ai-natural-command (command)
  "Send natural language command for AI processing."
  (interactive "sAI Command: ")
  (let ((context `((buffer . ,(buffer-name))
                   (point . ,(point))
                   (selection . ,(when (region-active-p)
                                   (buffer-substring-no-properties 
                                    (region-beginning) 
                                    (region-end))))
                   (major-mode . ,(symbol-name major-mode))
                   (file . ,(buffer-file-name)))))
    
    (redis-ai-send-intent 'command command context)
    (message "🤖 Processing: %s" command)))

;;; Response Processing

(defun redis-ai-start-response-listener ()
  "Start listening for AI responses from Redis."
  (interactive)
  (run-with-timer 0 1 'redis-ai-check-responses))

(defun redis-ai-check-responses ()
  "Check for new AI responses and process them."
  (when redis-ai-connection
    (condition-case err
        (let ((responses (redis-xread redis-ai-connection 
                                    `((,redis-ai-response-stream . "$"))
                                    :count 10
                                    :block 100)))
          (dolist (response responses)
            (redis-ai-process-response response)))
      (error 
       (message "Redis AI response error: %s" (error-message-string err))))))

(defun redis-ai-process-response (response)
  "Process an AI response and execute actions."
  (let* ((content (alist-get 'content response))
         (actions (json-read-from-string (alist-get 'actions response "")))
         (confidence (string-to-number (alist-get 'confidence response "0"))))
    
    ;; Display response if high confidence
    (when (> confidence 0.7)
      (message "🤖 %s" content))
    
    ;; Execute actions
    (when actions
      (redis-ai-execute-actions actions))))

(defun redis-ai-execute-actions (actions)
  "Execute a list of AI-generated actions."
  (dolist (action actions)
    (let ((action-type (alist-get 'type action)))
      (cond
       ((string= action-type "insert-text")
        (insert (alist-get 'text action)))
       
       ((string= action-type "replace-region")
        (when (region-active-p)
          (delete-region (region-beginning) (region-end))
          (insert (alist-get 'text action))))
       
       ((string= action-type "move-cursor")
        (goto-char (alist-get 'position action)))
       
       ((string= action-type "run-command")
        (call-interactively (intern (alist-get 'command action))))
       
       (t 
        (message "Unknown action type: %s" action-type))))))

;;; Predefined Composable Modes

(define-redis-ai-mode architect
  :config ((focus . long-form-thinking)
           (ai-agents . (claude-3.5-sonnet gpt-4-architect))
           (tools . (system-diagram workflow-synthesis)))
  :keybindings (("C-c a d" . redis-ai-architect-diagram)
                ("C-c a p" . redis-ai-architect-patterns))
  :hooks ((before-save-hook . redis-ai-architect-review)))

(define-redis-ai-mode implementation  
  :config ((focus . rapid-iteration)
           (ai-agents . (cursor copilot local-codellama))
           (tools . (test-generation real-time-docs)))
  :keybindings (("C-c i t" . redis-ai-generate-tests)
                ("C-c i d" . redis-ai-generate-docs)
                ("C-c i r" . redis-ai-refactor-selection))
  :hooks ((post-command-hook . redis-ai-capture-keystroke)))

(define-redis-ai-mode reviewer
  :config ((focus . excellence)
           (ai-agents . (claude-reviewer static-analysis))
           (tools . (quality-metrics refactoring-suggestions)))
  :keybindings (("C-c r r" . redis-ai-review-code)
                ("C-c r s" . redis-ai-suggest-improvements))
  :hooks ((before-save-hook . redis-ai-quality-check)))

(define-redis-ai-mode documentation
  :config ((focus . clarity)
           (ai-agents . (claude-documenter))
           (tools . (docstring-generation api-docs)))
  :keybindings (("C-c d f" . redis-ai-document-function)
                ("C-c d m" . redis-ai-document-module))
  :hooks ((after-save-hook . redis-ai-update-docs)))

;;; Interactive Commands

(defun redis-ai-compose-modes (modes)
  "Compose multiple AI modes for custom environment."
  (interactive "sModes (space-separated): ")
  (let ((mode-list (split-string modes)))
    (dolist (mode mode-list)
      (redis-ai-activate-mode (intern mode)))
    (message "🎼 Composed modes: %s" modes)))

(defun redis-ai-status ()
  "Show current AI mode status."
  (interactive)
  (if redis-ai-active-modes
      (message "Active AI modes: %s" 
               (mapconcat (lambda (m) (symbol-name m)) 
                         redis-ai-active-modes ", "))
    (message "No AI modes active")))

(defun redis-ai-toggle-reactive ()
  "Toggle reactive keystroke capture."
  (interactive)
  (if (member 'redis-ai-capture-keystroke post-command-hook)
      (progn
        (remove-hook 'post-command-hook 'redis-ai-capture-keystroke)
        (message "🛑 Reactive capture disabled"))
    (progn
      (add-hook 'post-command-hook 'redis-ai-capture-keystroke)
      (message "🚀 Reactive capture enabled"))))

;;; Global Minor Mode

(define-minor-mode redis-ai-mode
  "Global Redis AI coordination mode."
  :global t
  :lighter " Redis-AI"
  :keymap (let ((map (make-sparse-keymap)))
            (define-key map (kbd "C-c C-a") 'redis-ai-natural-command)
            (define-key map (kbd "C-c C-s") 'redis-ai-status)
            (define-key map (kbd "C-c C-c") 'redis-ai-compose-modes)
            (define-key map (kbd "C-c C-r") 'redis-ai-toggle-reactive)
            map)
  
  (if redis-ai-mode
      (progn
        (redis-ai-connect)
        (redis-ai-start-response-listener)
        (message "🚀 Redis AI mode activated - C-c C-a for commands"))
    (progn
      (setq redis-ai-active-modes '())
      (message "🛑 Redis AI mode deactivated"))))

;;; Utility Functions

(defun redis-ai-setup-keybindings (keybindings)
  "Set up keybindings for a mode."
  (dolist (binding keybindings)
    (global-set-key (kbd (car binding)) (cdr binding))))

(defun redis-ai-install-hooks (hooks)
  "Install hooks for a mode."
  (dolist (hook hooks)
    (add-hook (car hook) (cdr hook))))

;;; Demo Functions

(defun redis-ai-demo ()
  "Run a quick demo of the composable AI system."
  (interactive)
  (message "🎭 Redis AI Composable Modes Demo")
  
  ;; Activate Redis AI mode
  (redis-ai-mode 1)
  
  ;; Compose implementation mode
  (redis-ai-activate-mode 'implementation)
  
  (message "Try: C-c C-a 'generate tests for this function'"))

(provide 'composable-modes)

;;; composable-modes.el ends here