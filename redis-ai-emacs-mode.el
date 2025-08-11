;;; redis-ai-emacs-mode.el --- Emacs minor mode for Redis AI workforce control

;;; Commentary:
;; This minor mode connects Emacs to the Redis AI workforce system,
;; allowing real-time control of autonomous AI agents from within Emacs.
;; Implements the composable event server pattern for homoiconic development.

;;; Code:

(require 'json)
(require 'cl-lib)

;; Load modular components
(require 'redis-ai-core)
(require 'redis-ai-events)
(require 'redis-ai-agents)
(require 'redis-ai-mcp)
(require 'redis-ai-integration)
(require 'redis-ai-natural-lang)
(require 'redis-ai-monitoring)
(require 'redis-ai-python-bridge)

(defgroup redis-ai nil
  "Redis AI workforce integration for Emacs"
  :group 'tools
  :prefix "redis-ai-")

(defvar redis-ai-mode nil
  "Non-nil if Redis AI mode is enabled.")

;;;; Mode Definition

(defvar redis-ai-mode-map
  (let ((map (make-sparse-keymap)))
    (define-key map (kbd "C-c r c") 'redis-ai-connect)
    (define-key map (kbd "C-c r d") 'redis-ai-disconnect)
    (define-key map (kbd "C-c r t") 'redis-ai-generate-tests-for-buffer)
    (define-key map (kbd "C-c r o") 'redis-ai-document-buffer)
    (define-key map (kbd "C-c r r") 'redis-ai-refactor-buffer)
    (define-key map (kbd "C-c r l") 'redis-ai-execute-lisp)
    (define-key map (kbd "C-c r s") 'redis-ai-store-lisp-code)
    (define-key map (kbd "C-c r e") 'redis-ai-execute-stored-lisp)
    (define-key map (kbd "C-c r n") 'redis-ai-natural-command)
    (define-key map (kbd "C-c r ?") 'redis-ai-explain-code)
    (define-key map (kbd "C-c r +") 'redis-ai-optimize-function)
    (define-key map (kbd "C-c r TAB") 'redis-ai-smart-completion)
    (define-key map (kbd "C-c r a") 'redis-ai-list-agents)
    (define-key map (kbd "C-c r D") 'redis-ai-show-dashboard)
    ;; New Python AI commands
    (define-key map (kbd "C-c r P c") 'redis-ai-classify-text)
    (define-key map (kbd "C-c r P h") 'redis-ai-demonstrate-homoiconicity)
    (define-key map (kbd "C-c r P m") 'redis-ai-demonstrate-ml-coordination)
    (define-key map (kbd "C-c r P i") 'redis-ai-demonstrate-intelligent-data-manipulation)
    (define-key map (kbd "C-c r P l") 'redis-ai-demonstrate-real-time-learning)
    map)
  "Keymap for Redis AI mode.")

;;;###autoload
(define-minor-mode redis-ai-mode
  "Minor mode for Redis AI workforce integration.
  
This mode connects Emacs to a Redis-based AI workforce system,
enabling real-time AI assistance, code generation, testing,
documentation, and homoiconic Lisp execution.

Key bindings:
\{redis-ai-mode-map}"
  :init-value nil
  :lighter " 🤖"
  :keymap redis-ai-mode-map
  :group 'redis-ai
  
  (if redis-ai-mode
      (progn
        (add-hook 'after-save-hook 'redis-ai-on-buffer-save nil t)
        (message "Redis AI mode enabled - Use C-c r c to connect"))
    (progn
      (remove-hook 'after-save-hook 'redis-ai-on-buffer-save t)
      (redis-ai-disconnect)
      (message "Redis AI mode disabled"))))

;;;###autoload
(defun redis-ai-global-mode-enable ()
  "Enable Redis AI mode globally."
  (interactive)
  (add-hook 'prog-mode-hook 'redis-ai-mode)
  (message "Redis AI mode enabled globally for programming modes"))

(provide 'redis-ai-emacs-mode)
;;; redis-ai-emacs-mode.el ends here