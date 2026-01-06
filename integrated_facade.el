;;; integrated_facade.el --- Unified macOS + Emacs facade -*- lexical-binding: t; -*-

;; Complete homoiconic representation of entire system state in Redis
;; Like looking at the Mac from inside - every observable fact represented as data

;;; Code:

(require 'json)

(defvar facade-redis-key "facade:state:current"
  "Redis key for current integrated facade state.")

(defvar facade-stream "facade:stream"
  "Redis stream for facade history.")

(defun facade-redis (cmd)
  "Execute Redis CMD."
  (string-trim (shell-command-to-string (format "redis-cli %s" cmd))))

(defun facade-has-assistive-access ()
  "Check if we have assistive access."
  (not (string-match-p "error.*assistive"
                      (shell-command-to-string
                       "osascript -e 'tell application \"System Events\" to get name of first process' 2>&1"))))

(defun facade-capture-all ()
  "Capture EVERYTHING - complete system representation."
  (interactive)

  (let* ((has-access (facade-has-assistive-access))
         (timestamp (format-time-string "%s"))

         ;; Core system
         (system (list :hostname (string-trim (shell-command-to-string "hostname"))
                      :user (getenv "USER")
                      :uptime (string-trim (shell-command-to-string "uptime"))
                      :timestamp timestamp
                      :assistive-access has-access))

         ;; Display
         (display (let ((bounds (shell-command-to-string
                                "osascript -e 'tell application \"Finder\" to get bounds of window of desktop' 2>&1")))
                   (if (string-match-p "error" bounds)
                       (list :available nil)
                     (let ((parts (split-string (string-trim bounds) ", ")))
                       (list :width (- (string-to-number (nth 2 parts))
                                      (string-to-number (nth 0 parts)))
                             :height (- (string-to-number (nth 3 parts))
                                       (string-to-number (nth 1 parts)))
                             :total-pixels (* (- (string-to-number (nth 2 parts))
                                                (string-to-number (nth 0 parts)))
                                             (- (string-to-number (nth 3 parts))
                                                (string-to-number (nth 1 parts)))))))))

         ;; Applications
         (applications (let ((apps-str (shell-command-to-string
                                       "osascript -e 'tell application \"System Events\" to get name of every process whose background only is false' 2>&1")))
                        (if (string-match-p "error" apps-str)
                            (list :error apps-str)
                          (let ((apps (split-string (string-trim apps-str) ", ")))
                            (list :list apps
                                 :count (length apps))))))

         ;; Windows (if assistive access available)
         (windows (if has-access
                     (list :frontmost
                          (let ((result (shell-command-to-string
                                        "osascript -e 'tell application \"System Events\" to tell (first process whose frontmost is true) to get {name, name of window 1, position of window 1, size of window 1}' 2>&1")))
                            (if (string-match-p "error" result)
                                (list :error result)
                              (list :raw result))))
                   (list :unavailable "no assistive access")))

         ;; Processes
         (processes (list :total (string-to-number
                                 (string-trim (shell-command-to-string "ps aux | wc -l")))
                         :load (string-trim (shell-command-to-string "uptime | awk -F'load averages:' '{print $2}'"))))

         ;; Network
         (network (list :interfaces-count (length (split-string
                                                   (shell-command-to-string "ifconfig | grep '^[a-z]' | cut -d: -f1")
                                                   "\n" t))
                       :connections (string-to-number
                                    (string-trim (shell-command-to-string "netstat -an | grep ESTABLISHED | wc -l")))))

         ;; Emacs state
         (emacs (list :version emacs-version
                     :pid (emacs-pid)
                     :frames (length (frame-list))
                     :windows (length (window-list))
                     :buffers (length (buffer-list))
                     :current-buffer (buffer-name (current-buffer))
                     :point (point)
                     :mark (or (mark t) 0)
                     :mode major-mode
                     :redis-connected (condition-case nil
                                         (progn (facade-redis "PING") t)
                                       (error nil))))

         ;; Redis state (homoiconic!)
         (redis (let ((info (shell-command-to-string "redis-cli INFO server 2>&1")))
                 (if (string-match-p "error\\|Could not connect" info)
                     (list :available nil)
                   (list :available t
                        :keys (string-to-number (facade-redis "DBSIZE | cut -d: -f2"))
                        :streams (list :facade (string-to-number
                                               (or (facade-redis (format "XLEN %s" facade-stream))
                                                   "0")))))))

         ;; Complete state
         (state (list :meta (list :timestamp timestamp
                                 :has-assistive-access has-access
                                 :capture-version "2.0.0")
                     :system system
                     :display display
                     :applications applications
                     :windows windows
                     :processes processes
                     :network network
                     :emacs emacs
                     :redis redis)))

    ;; Store in Redis (homoiconic representation)
    (let* ((json-str (json-encode state))
           (escaped (replace-regexp-in-string "\"" "\\\\\""
                    (replace-regexp-in-string "\n" "\\\\n" json-str))))

      ;; Current state (always latest)
      (facade-redis (format "SET %s \"%s\"" facade-redis-key escaped))

      ;; History stream
      (facade-redis (format "XADD %s '*' ts %s state \"%s\""
                           facade-stream timestamp escaped))

      ;; Also store in a more queryable format
      (facade-redis (format "HSET facade:apps:current count %d"
                           (plist-get applications :count)))
      (facade-redis (format "HSET facade:emacs:current buffer \"%s\" point %d"
                           (buffer-name) (point))))

    (message "✅ Complete integrated facade captured")
    (message "   System: %s@%s" (plist-get system :user) (plist-get system :hostname))
    (message "   Display: %dx%d = %d pixels"
             (plist-get display :width)
             (plist-get display :height)
             (plist-get display :total-pixels))
    (message "   Apps: %d | Procs: %d | Network: %d connections"
             (plist-get applications :count)
             (plist-get processes :total)
             (plist-get network :connections))
    (message "   Emacs: %d buffers, %d windows (buffer: %s, point: %d)"
             (plist-get emacs :buffers)
             (plist-get emacs :windows)
             (plist-get emacs :current-buffer)
             (plist-get emacs :point))
    (message "   Assistive access: %s" (if has-access "YES" "NO"))
    (message "   Redis: GET %s" facade-redis-key)

    state))

(defun facade-view ()
  "View current facade state beautifully."
  (interactive)

  (let* ((json-str (facade-redis (format "GET %s" facade-redis-key)))
         (state (condition-case nil
                   (json-read-from-string json-str)
                 (error nil))))

    (if (not state)
        (message "No facade state in Redis yet. Run M-x facade-capture-all")

      (with-current-buffer (get-buffer-create "*Integrated Facade*")
        (erase-buffer)
        (insert "╔═══════════════════════════════════════════════════════════╗\n")
        (insert "║        COMPLETE SYSTEM FACADE - Homoiconic Vision        ║\n")
        (insert "╚═══════════════════════════════════════════════════════════╝\n\n")

        (let* ((meta (cdr (assq 'meta state)))
               (system (cdr (assq 'system state)))
               (display (cdr (assq 'display state)))
               (apps (cdr (assq 'applications state)))
               (emacs (cdr (assq 'emacs state)))
               (redis-state (cdr (assq 'redis state))))

          (insert (format "⏰ %s\n" (cdr (assq 'iso-time (cdr (assq 'time system))))))
          (insert (format "🖥️  %s@%s\n\n"
                         (cdr (assq 'user system))
                         (cdr (assq 'hostname system))))

          (insert "┌─ DISPLAY ───────────────────────────────────────────┐\n")
          (insert (format "│  Resolution: %dx%d (%s pixels)\n"
                         (cdr (assq 'width display))
                         (cdr (assq 'height display))
                         (cdr (assq 'total-pixels display))))
          (insert "└─────────────────────────────────────────────────────┘\n\n")

          (insert "┌─ APPLICATIONS ──────────────────────────────────────┐\n")
          (insert (format "│  Running: %d apps\n" (cdr (assq 'count apps))))
          (let* ((app-list (cdr (assq 'list apps)))
                 (app-vec (if (vectorp app-list) app-list (vconcat app-list))))
            (dotimes (i (min 8 (length app-vec)))
              (insert (format "│    • %s\n" (aref app-vec i))))
            (when (> (length app-vec) 8)
              (insert (format "│    ... and %d more\n" (- (length app-vec) 8)))))
          (insert "└─────────────────────────────────────────────────────┘\n\n")

          (insert "┌─ EMACS ─────────────────────────────────────────────┐\n")
          (insert (format "│  Version: %s (PID %d)\n"
                         (cdr (assq 'version emacs))
                         (cdr (assq 'pid emacs))))
          (insert (format "│  Buffers: %d | Windows: %d | Frames: %d\n"
                         (cdr (assq 'buffers emacs))
                         (cdr (assq 'windows emacs))
                         (cdr (assq 'frames emacs))))
          (insert (format "│  Current: %s (point: %d)\n"
                         (cdr (assq 'current-buffer emacs))
                         (cdr (assq 'point emacs))))
          (insert "└─────────────────────────────────────────────────────┘\n\n")

          (insert "┌─ REDIS (Homoiconic Storage) ────────────────────────┐\n")
          (if (cdr (assq 'available redis-state))
              (progn
                (insert (format "│  Status: Connected ✓\n"))
                (insert (format "│  Total keys: %d\n" (cdr (assq 'keys redis-state))))
                (insert (format "│  Facade stream: %d entries\n"
                               (cdr (assq 'facade (cdr (assq 'streams redis-state)))))))
            (insert "│  Status: Disconnected\n"))
          (insert "└─────────────────────────────────────────────────────┘\n\n")

          (insert (format "Stored in Redis: %s\n" facade-redis-key))
          (insert (format "History stream: %s\n" facade-stream)))

        (goto-char (point-min))
        (special-mode))

      (switch-to-buffer "*Integrated Facade*"))))

(defun facade-emacs-learning-stream ()
  "Log my Emacs learning to a dedicated stream."
  (let ((lesson (list :timestamp (format-time-string "%s")
                     :buffer (buffer-name)
                     :point (point)
                     :command this-command
                     :keys (this-command-keys-vector))))
    (facade-redis
     (format "XADD claude:learning '*' ts %s buffer \"%s\" point %d cmd \"%s\""
             (plist-get lesson :timestamp)
             (plist-get lesson :buffer)
             (plist-get lesson :point)
             (or this-command "nil")))))

;; Key bindings
(global-set-key (kbd "C-c C-f c") 'facade-capture-all)
(global-set-key (kbd "C-c C-f v") 'facade-view)

(provide 'integrated-facade)
;;; integrated_facade.el ends here
