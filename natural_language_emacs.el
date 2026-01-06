;;; natural_language_emacs.el --- Talk to Emacs in natural language -*- lexical-binding: t; -*-

;; Natural language interface using Redis as communication layer

;;; Code:

(require 'json)

(defvar nl-emacs-redis-stream "nl:emacs:commands"
  "Redis stream for natural language commands.")

(defvar nl-emacs-results-stream "nl:emacs:results"
  "Redis stream for execution results.")

(defun nl-emacs-redis-exec (cmd)
  "Execute Redis CMD."
  (string-trim
   (shell-command-to-string
    (format "redis-cli %s" cmd))))

(defun nl-emacs-understand (text)
  "Parse natural language TEXT into Emacs command."
  (let* ((text-lower (downcase text))
         (intent 'unknown)
         (params '()))

    ;; Pattern matching for intents
    (cond
     ;; INSERT
     ((or (string-match-p "insert\\|type\\|write\\|add" text-lower))
      (setq intent 'insert)
      (when (string-match "insert\\|type\\|write\\|add \\(.+\\)" text-lower)
        (setq params (list :text (match-string 1 text)))))

     ;; MOVE
     ((string-match-p "go\\|move\\|jump" text-lower)
      (setq intent 'move)
      (cond
       ((string-match-p "beginning\\|start" text-lower)
        (setq params (list :where 'beginning)))
       ((string-match-p "end" text-lower)
        (setq params (list :where 'end)))
       ((string-match "line \\([0-9]+\\)" text-lower)
        (setq params (list :line (string-to-number (match-string 1 text-lower)))))))

     ;; DELETE
     ((string-match-p "delete\\|remove\\|kill" text-lower)
      (setq intent 'delete)
      (cond
       ((string-match-p "line" text-lower)
        (setq params (list :what 'line)))
       ((string-match-p "word" text-lower)
        (setq params (list :what 'word)))
       (t
        (setq params (list :what 'char)))))

     ;; STATUS
     ((string-match-p "what\\|where\\|status\\|show" text-lower)
      (setq intent 'status))

     ;; SAVE
     ((string-match-p "save" text-lower)
      (setq intent 'save))

     ;; SEARCH
     ((string-match-p "search\\|find" text-lower)
      (setq intent 'search)
      (when (string-match "search \\(.+\\)" text-lower)
        (setq params (list :text (match-string 1 text))))))

    (list :intent intent :params params :raw text)))

(defun nl-emacs-execute (understanding)
  "Execute UNDERSTANDING as Emacs command."
  (let ((intent (plist-get understanding :intent))
        (params (plist-get understanding :params))
        (result nil))

    (pcase intent
      ('insert
       (let ((text (plist-get params :text)))
         (insert text)
         (setq result (format "Inserted: %s" text))))

      ('move
       (let ((where (plist-get params :where))
             (line (plist-get params :line)))
         (cond
          ((eq where 'beginning)
           (goto-char (point-min))
           (setq result "Moved to beginning"))
          ((eq where 'end)
           (goto-char (point-max))
           (setq result "Moved to end"))
          (line
           (goto-line line)
           (setq result (format "Moved to line %d" line))))))

      ('delete
       (let ((what (plist-get params :what)))
         (pcase what
           ('line
            (kill-line)
            (setq result "Deleted line"))
           ('word
            (kill-word 1)
            (setq result "Deleted word"))
           ('char
            (delete-char 1)
            (setq result "Deleted character")))))

      ('status
       (setq result (format "Buffer: %s, Point: %d, Line: %d"
                           (buffer-name)
                           (point)
                           (line-number-at-pos))))

      ('save
       (save-buffer)
       (setq result (format "Saved buffer: %s" (buffer-name))))

      ('search
       (let ((text (plist-get params :text)))
         (if (search-forward text nil t)
             (setq result (format "Found: %s at point %d" text (point)))
           (setq result (format "Not found: %s" text)))))

      (_
       (setq result (format "Unknown command: %s"
                           (plist-get understanding :raw)))))

    result))

(defun nl-emacs-talk (command)
  "Main interface: talk to Emacs with COMMAND in natural language."
  (interactive "sCommand: ")

  (message "💬 You: %s" command)

  ;; Understand
  (let* ((understanding (nl-emacs-understand command))
         (intent (plist-get understanding :intent)))

    (message "🧠 Intent: %s" intent)

    ;; Log to Redis
    (nl-emacs-redis-exec
     (format "XADD %s '*' command \"%s\" intent \"%s\" timestamp %s"
             nl-emacs-redis-stream
             (replace-regexp-in-string "\"" "\\\\\"" command)
             intent
             (format-time-string "%s")))

    ;; Execute
    (let ((result (nl-emacs-execute understanding)))
      (message "✅ Result: %s" result)

      ;; Log result to Redis
      (nl-emacs-redis-exec
       (format "XADD %s '*' result \"%s\" timestamp %s"
               nl-emacs-results-stream
               (replace-regexp-in-string "\"" "\\\\\"" result)
               (format-time-string "%s")))

      result)))

(defun nl-emacs-demo ()
  "Demonstrate natural language interface."
  (interactive)

  (with-temp-buffer
    (message "🎯 Natural Language Emacs Demo")
    (sit-for 1)

    ;; Demo commands
    (nl-emacs-talk "insert Hello from natural language!")
    (sit-for 1)

    (nl-emacs-talk "go to the beginning")
    (sit-for 1)

    (nl-emacs-talk "what's my status?")
    (sit-for 1)

    (nl-emacs-talk "move to the end")
    (sit-for 1)

    (nl-emacs-talk "insert More text here.")
    (sit-for 1)

    (message "")
    (message "✅ Demo complete!")
    (message "Buffer contents: %s" (buffer-string))
    (message "")
    (message "Check Redis:")
    (message "  redis-cli XREAD STREAMS %s 0" nl-emacs-redis-stream)
    (message "  redis-cli XREAD STREAMS %s 0" nl-emacs-results-stream)))

;; Key bindings
(global-set-key (kbd "C-c n t") 'nl-emacs-talk)
(global-set-key (kbd "C-c n d") 'nl-emacs-demo)

(provide 'natural-language-emacs)
;;; natural_language_emacs.el ends here
