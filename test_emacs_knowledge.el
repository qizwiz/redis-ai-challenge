;;; test_emacs_knowledge.el --- Test what Claude learned about Emacs

;; I learned through Redis that:
;; 1. point-min returns beginning of buffer (verified: returns 1)
;; 2. forward-line moves by lines (verified: moved from point 1 to 8)
;; 3. buffer-substring extracts text (verified: got " text" from region)

;; Now let me apply this knowledge to solve a real problem:
;; Parse and analyze the structure of an Elisp file using what I learned

(defun claude-learned-parse-defun ()
  "Parse defun at point using syntax-ppss knowledge from Redis lessons."
  (interactive)
  (save-excursion
    ;; Use learned knowledge: goto-char + point-min
    (goto-char (point-min))

    ;; Use learned knowledge: search-forward
    (let ((defuns '()))
      (while (search-forward "(defun " nil t)
        ;; Use learned knowledge: forward-word + buffer-substring
        (let ((name-start (point)))
          (forward-word 1)
          (let ((name (buffer-substring name-start (point))))
            (push name defuns))))

      ;; Store result in Redis for verification
      (shell-command-to-string
       (format "redis-cli XADD 'emacs:learned-skill' '*' skill 'parse-defuns' result '%s' timestamp '%s'"
               (mapconcat 'identity (reverse defuns) ",")
               (format-time-string "%s")))

      (message "📚 Found %d defuns: %s"
               (length defuns)
               (string-join (reverse defuns) ", "))
      defuns)))

;; Run this on the learning file itself
(find-file "~/src/learn_emacs_redis.el")
(claude-learned-parse-defun)

;; Now verify in Redis that I actually learned something
(shell-command-to-string "redis-cli XREAD COUNT 1 STREAMS 'emacs:learned-skill' 0")

(provide 'test-emacs-knowledge)
