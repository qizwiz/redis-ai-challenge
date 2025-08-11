;;; cleanup_minibuffer.el --- Clean up minibuffer pollution using supervision DSL patterns

;; -*- lexical-binding: t -*-

(require 'cl-lib)

;; Supervision DSL for Elisp - inspired by the Python version
(defvar supervision-registry (make-hash-table :test 'equal)
  "Registry of all supervised processes")

(defvar supervision-cleanup-hooks '()
  "Hooks to run during cleanup")

(cl-defstruct supervisor
  name
  strategy
  max-restarts
  restart-window
  processes
  restart-counts
  last-restart-times
  running)

(cl-defstruct supervised-process
  name
  timer
  function
  restart-strategy
  health-check
  dependencies
  metadata)

;; Beautiful DSL for Elisp supervision
(defmacro defsupervisor (name &rest body)
  "DSL: Define a supervisor with beautiful syntax"
  `(let ((supervisor (make-supervisor :name ,(symbol-name name)
                                      :strategy 'one-for-one
                                      :max-restarts 5
                                      :restart-window 60
                                      :processes (make-hash-table :test 'equal)
                                      :restart-counts (make-hash-table :test 'equal)
                                      :last-restart-times (make-hash-table :test 'equal)
                                      :running nil)))
     ,@body
     (puthash ,(symbol-name name) supervisor supervision-registry)
     supervisor))

(defmacro defprocess (name supervisor-name &rest body)
  "DSL: Define a supervised process"
  `(let ((process (make-supervised-process :name ,(symbol-name name)
                                          :timer nil
                                          :function nil
                                          :restart-strategy 'permanent
                                          :health-check nil
                                          :dependencies '()
                                          :metadata (make-hash-table :test 'equal))))
     ,@body
     (let ((supervisor (gethash ,(symbol-name supervisor-name) supervision-registry)))
       (when supervisor
         (puthash ,(symbol-name name) process (supervisor-processes supervisor))))
     process))

;; Process configuration methods
(defun process-handler (process func)
  "Set process handler function"
  (setf (supervised-process-function process) func)
  process)

(defun process-restart-strategy (process strategy)
  "Set restart strategy"
  (setf (supervised-process-restart-strategy process) strategy)
  process)

(defun process-health-check (process func)
  "Set health check function"
  (setf (supervised-process-health-check process) func)
  process)

(defun process-depends-on (process &rest dependencies)
  "Set process dependencies"
  (setf (supervised-process-dependencies process) dependencies)
  process)

;; Cleanup DSL Implementation
(defsupervisor minibuffer-cleanup-supervisor
  (setf (supervisor-strategy supervisor) 'one-for-all)
  (setf (supervisor-max-restarts supervisor) 3))

(defprocess timer-killer minibuffer-cleanup-supervisor
  (process-handler process #'kill-rogue-timers)
  (process-health-check process (lambda () t)))

(defprocess message-cleaner minibuffer-cleanup-supervisor
  (process-handler process #'clean-minibuffer-messages)
  (process-depends-on process "timer-killer"))

(defprocess state-validator minibuffer-cleanup-supervisor
  (process-handler process #'validate-emacs-state)
  (process-depends-on process "timer-killer" "message-cleaner"))

;; Cleanup functions
(defun kill-rogue-timers ()
  "Kill timers that might be polluting minibuffer"
  (let ((killed-count 0))
    (dolist (timer timer-list)
      (when timer
        (let ((func (timer--function timer)))
          (when (and func 
                     (or (string-match-p "msg-" (format "%s" func))
                         (string-match-p "message" (format "%s" func))
                         (string-match-p "facade" (format "%s" func))
                         (string-match-p "claude" (format "%s" func))
                         (string-match-p "supervision" (format "%s" func))))
            (cancel-timer timer)
            (setq killed-count (1+ killed-count))))))
    
    ;; Kill specific timer variables
    (dolist (var '(msg-timers message-timers message-delivery-timers 
                   supervision-monitor-timer claude-status-timer 
                   actor-message-timer minibuffer-monitor-timer))
      (when (boundp var)
        (let ((timer-val (symbol-value var)))
          (cond
           ((timerp timer-val)
            (cancel-timer timer-val)
            (set var nil)
            (setq killed-count (1+ killed-count)))
           ((hash-table-p timer-val)
            (maphash (lambda (_key timer)
                       (when (timerp timer)
                         (cancel-timer timer)
                         (setq killed-count (1+ killed-count))))
                     timer-val)
            (clrhash timer-val))))))
    
    (when (> killed-count 0)
      (message "🧹 Killed %d rogue timers" killed-count))
    killed-count))

(defun clean-minibuffer-messages ()
  "Clear minibuffer and message log"
  (message "")  ; Clear current message
  (clear-message-buffer)
  
  ;; Clear any leftover minibuffer state
  (when (active-minibuffer-window)
    (with-selected-window (active-minibuffer-window)
      (erase-buffer)))
  
  (message "🧹 Minibuffer cleaned"))

(defun clear-message-buffer ()
  "Clear the *Messages* buffer"
  (when (get-buffer "*Messages*")
    (with-current-buffer "*Messages*"
      (let ((inhibit-read-only t))
        (erase-buffer))))
  
  ;; Clear other potential message buffers
  (dolist (buf-name '("*MINIBUFFER-LOG*" "*MINIBUFFER-DEBUG*" 
                      "*claude-status-log*" "*supervision-logs*"))
    (when (get-buffer buf-name)
      (with-current-buffer buf-name
        (erase-buffer)))))

(defun validate-emacs-state ()
  "Validate that Emacs is in a clean state"
  (let ((issues '()))
    
    ;; Check for active timers
    (let ((timer-count (length (cl-remove-if-not #'identity timer-list))))
      (when (> timer-count 10)  ; Arbitrary threshold
        (push (format "%d active timers (might be excessive)" timer-count) issues)))
    
    ;; Check minibuffer state
    (when (active-minibuffer-window)
      (push "Minibuffer is active" issues))
    
    ;; Check for message pollution patterns
    (let ((current-msg (current-message)))
      (when (and current-msg 
                 (or (string-match-p "📨\\|🔄\\|💥\\|🏓\\|📥\\|❌" current-msg)
                     (string-match-p "MSG\\|PING\\|PONG\\|FACADE" current-msg)))
        (push (format "Polluted message: %s" current-msg) issues)))
    
    (if issues
        (progn
          (message "⚠️ State issues: %s" (string-join issues "; "))
          nil)
      (progn
        (message "✅ Emacs state validated")
        t))))

;; Supervision engine
(defun start-supervisor (supervisor-name)
  "Start a supervisor and all its processes"
  (let ((supervisor (gethash supervisor-name supervision-registry)))
    (when supervisor
      (setf (supervisor-running supervisor) t)
      (message "🚀 Starting supervisor: %s" supervisor-name)
      
      ;; Start all processes in dependency order
      (maphash (lambda (_name process)
                 (start-supervised-process supervisor process))
               (supervisor-processes supervisor))
      
      supervisor)))

(defun start-supervised-process (supervisor process)
  "Start a single supervised process"
  (let ((name (supervised-process-name process))
        (func (supervised-process-function process)))
    
    (when func
      ;; Check dependencies first
      (let ((deps-ready t))
        (dolist (dep (supervised-process-dependencies process))
          (unless (process-dependency-ready-p supervisor dep)
            (setq deps-ready nil)))
        
        (when deps-ready
          ;; Stop existing timer if any
          (when (supervised-process-timer process)
            (cancel-timer (supervised-process-timer process)))
          
          ;; Start new timer
          (let ((timer (run-with-timer 0 nil func)))
            (setf (supervised-process-timer process) timer)
            (message "📋 Started process: %s" name)))))))

(defun process-dependency-ready-p (supervisor dep-name)
  "Check if process dependency is ready"
  (let ((dep-process (gethash dep-name (supervisor-processes supervisor))))
    (and dep-process
         (supervised-process-timer dep-process)
         (if (supervised-process-health-check dep-process)
             (funcall (supervised-process-health-check dep-process))
           t))))

(defun stop-supervisor (supervisor-name)
  "Stop supervisor and all processes"
  (let ((supervisor (gethash supervisor-name supervision-registry)))
    (when supervisor
      (setf (supervisor-running supervisor) nil)
      (message "🛑 Stopping supervisor: %s" supervisor-name)
      
      (maphash (lambda (_name process)
                 (when (supervised-process-timer process)
                   (cancel-timer (supervised-process-timer process))
                   (setf (supervised-process-timer process) nil)))
               (supervisor-processes supervisor)))))

;; Main cleanup command
(defun cleanup-minibuffer-supervised ()
  "Clean up minibuffer using supervision DSL"
  (interactive)
  
  (message "🧹 Starting supervised minibuffer cleanup...")
  
  ;; Start the cleanup supervisor
  (start-supervisor "minibuffer-cleanup-supervisor")
  
  ;; Wait a moment for cleanup to complete
  (run-with-timer 2 nil
                  (lambda ()
                    (stop-supervisor "minibuffer-cleanup-supervisor")
                    (message "✅ Supervised cleanup complete"))))

;; Emergency cleanup - immediate action
(defun emergency-cleanup-minibuffer ()
  "Emergency minibuffer cleanup - immediate execution"
  (interactive)
  
  (message "🚨 Emergency cleanup started...")
  
  ;; Kill everything immediately
  (kill-rogue-timers)
  (clean-minibuffer-messages)
  
  ;; Clear any supervision state
  (clrhash supervision-registry)
  
  ;; Force garbage collection
  (garbage-collect)
  
  (message "🚨 Emergency cleanup complete"))

;; Status checker
(defun supervision-status ()
  "Show supervision system status"
  (interactive)
  
  (with-current-buffer (get-buffer-create "*SUPERVISION-STATUS*")
    (erase-buffer)
    (insert "🎭 SUPERVISION SYSTEM STATUS\n")
    (insert "============================\n\n")
    
    (insert (format "Registered supervisors: %d\n" (hash-table-count supervision-registry)))
    (insert (format "Active timers: %d\n" (length (cl-remove-if-not #'identity timer-list))))
    (insert (format "Current message: %s\n" (or (current-message) "none")))
    (insert (format "Minibuffer active: %s\n" (if (active-minibuffer-window) "YES" "NO")))
    
    (insert "\nSUPERVISORS:\n")
    (maphash (lambda (name supervisor)
               (insert (format "  %s: %s (%d processes)\n" 
                              name
                              (if (supervisor-running supervisor) "RUNNING" "STOPPED")
                              (hash-table-count (supervisor-processes supervisor)))))
             supervision-registry)
    
    (goto-char (point-min))
    (pop-to-buffer (current-buffer))))

;; Auto-cleanup on load
(add-hook 'after-init-hook #'cleanup-minibuffer-supervised)

(provide 'cleanup-minibuffer)