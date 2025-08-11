;; Test loading claude-repl.el

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

(defun claude-repl-test ()
  "Test function to verify basic loading works."
  (interactive)
  (message "Claude REPL test loaded successfully!"))

(provide 'test-claude-repl)