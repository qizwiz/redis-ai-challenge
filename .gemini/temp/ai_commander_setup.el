
(require 'term)

(setq ai-commander-buffer (get-buffer-create "*AI Commander*"))
(switch-to-buffer ai-commander-buffer)

(term "python" (format "%s/interactive_ai_commander.py" default-directory))

(setq-local term-prompt-regexp "^🤖 AI> ")
(setq-local term-send-raw-input-on-return t)
(setq-local term-send-raw-input-on-return-function (lambda () (interactive) (term-send-input)))
(setq-local term-local-map (make-sparse-keymap))
(define-key term-local-map (kbd "RET") (lambda () (interactive) (term-send-input)))

(message "AI Commander buffer created. Type commands directly.")
