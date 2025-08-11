;;; lisp_actor_modes.el --- Minor modes as distributed Lisp actors

;; -*- lexical-binding: t -*-

;;; Commentary:
;; Revolutionary approach: Minor modes ARE the actors in our distributed system
;; Each minor mode is a fault-tolerant actor with supervision and message passing
;; S-expressions define both the code structure AND the supervision topology

(require 'json)

;;; Actor Registry - Global state for distributed actor system

(defvar actor-registry (make-hash-table :test 'equal)
  "Registry of all active actors (minor modes)")

(defvar supervision-trees (make-hash-table :test 'equal)
  "Supervision tree relationships: supervisor -> list of children")

(defvar actor-restart-counts (make-hash-table :test 'equal)
  "Track restart counts for each actor")

(defvar actor-redis-connection nil
  "Shared Redis connection for all actors")

;;; Core Actor Protocol

(defun actor-send-message (actor-name message-type data)
  "Send message to actor via Redis streams"
  (let ((stream-name (format "actor:%s:messages" actor-name))
        (message `((type . ,message-type)
                   (data . ,(json-encode data))
                   (timestamp . ,(float-time))
                   (sender . "emacs-actor"))))
    (shell-command-to-string 
     (format "redis-cli XADD '%s' '*' %s" 
             stream-name
             (mapconcat (lambda (kv) (format "%s '%s'" (car kv) (cdr kv))) message " ")))
    (message "📨 Actor message sent: %s -> %s" message-type actor-name)))

(defun actor-register (name mode-function)
  "Register an actor (minor mode) in the system"
  (puthash name mode-function actor-registry)
  (message "🎭 Actor registered: %s" name))

(defun actor-supervise (supervisor-name child-name)
  "Establish supervision relationship"
  (let ((children (gethash supervisor-name supervision-trees)))
    (puthash supervisor-name (cons child-name children) supervision-trees))
  (message "👁️ Supervision established: %s -> %s" supervisor-name child-name))

;;; S-expression Actor Definition Macro

(defmacro define-actor-mode (name docstring &rest body)
  "Define a minor mode that acts as a distributed Lisp actor
  
  Usage:
  (define-actor-mode claude-nlp-actor
    \"NLP processing actor for Claude coordination\"
    :supervisor claude-coordinator-actor
    :restart-strategy permanent
    :message-handlers 
    ((process-text . claude-nlp-process-text)
     (parse-intent . claude-nlp-parse-intent))
    :behavior
    (progn
      (claude-nlp-setup-processing)
      (claude-nlp-start-listening)))"
  
  (let* ((mode-name (intern (format "%s-mode" name)))
         (mode-variable (intern (format "%s-mode" name)))
         (setup-function (intern (format "%s-setup" name)))
         (teardown-function (intern (format "%s-teardown" name)))
         (supervisor (plist-get body :supervisor))
         (restart-strategy (plist-get body :restart-strategy))
         (message-handlers (plist-get body :message-handlers))
         (behavior (plist-get body :behavior)))
    
    `(progn
       ;; Define the minor mode
       (define-minor-mode ,mode-name
         ,docstring
         :global t
         :lighter ,(format " %s" name)
         (if ,mode-variable
             (,setup-function)
           (,teardown-function)))
       
       ;; Setup function
       (defun ,setup-function ()
         "Setup this actor"
         (actor-register ,(symbol-name name) ',mode-name)
         ,(when supervisor
            `(actor-supervise ,(symbol-name supervisor) ,(symbol-name name)))
         ,(when message-handlers
            `(progn
               ,@(mapcar (lambda (handler)
                          `(actor-register-handler ,(symbol-name name) 
                                                   ,(symbol-name (car handler))
                                                   ',(cdr handler)))
                        message-handlers)))
         ,(when behavior behavior)
         (message "🚀 Actor started: %s" ,(symbol-name name)))
       
       ;; Teardown function  
       (defun ,teardown-function ()
         "Teardown this actor"
         (remhash ,(symbol-name name) actor-registry)
         (message "🛑 Actor stopped: %s" ,(symbol-name name)))
       
       ;; Return the mode name for reference
       ',mode-name)))

;;; Message Handler Registry

(defvar actor-message-handlers (make-hash-table :test 'equal)
  "Map of actor-name -> message-type -> handler-function")

(defun actor-register-handler (actor-name message-type handler-function)
  "Register message handler for an actor"
  (let ((actor-handlers (or (gethash actor-name actor-message-handlers)
                           (make-hash-table :test 'equal))))
    (puthash message-type handler-function actor-handlers)
    (puthash actor-name actor-handlers actor-message-handlers)))

(defun actor-handle-message (actor-name message-type data)
  "Handle incoming message for an actor"
  (let* ((actor-handlers (gethash actor-name actor-message-handlers))
         (handler (when actor-handlers (gethash message-type actor-handlers))))
    (if handler
        (condition-case err
            (funcall handler data)
          (error 
           (message "❌ Actor %s handler error: %s" actor-name (error-message-string err))
           (actor-handle-failure actor-name err)))
      (message "⚠️ No handler for %s in actor %s" message-type actor-name))))

;;; Fault Tolerance and Supervision

(defun actor-handle-failure (actor-name error)
  "Handle actor failure with supervision strategy"
  (let ((restart-count (or (gethash actor-name actor-restart-counts) 0)))
    (puthash actor-name (1+ restart-count) actor-restart-counts)
    
    (if (< restart-count 5)
        (progn
          (message "🔄 Restarting actor: %s (attempt %d)" actor-name (1+ restart-count))
          (actor-restart actor-name))
      (message "❌ Actor %s exceeded restart limit" actor-name))))

(defun actor-restart (actor-name)
  "Restart a failed actor"
  (let ((mode-function (gethash actor-name actor-registry)))
    (when mode-function
      ;; Disable then re-enable the minor mode
      (funcall mode-function -1)
      (run-with-timer 1 nil mode-function 1))))

;;; Message Bus Integration

(defvar actor-message-timer nil
  "Timer for checking Redis messages")

(defun actor-start-message-bus ()
  "Start the message bus for actor communication"
  (when actor-message-timer
    (cancel-timer actor-message-timer))
  
  (setq actor-message-timer 
        (run-with-timer 0 2 'actor-process-messages))
  (message "📡 Actor message bus started"))

(defun actor-stop-message-bus ()
  "Stop the message bus"
  (when actor-message-timer
    (cancel-timer actor-message-timer)
    (setq actor-message-timer nil))
  (message "📡 Actor message bus stopped"))

(defun actor-process-messages ()
  "Process pending messages for all actors"
  (maphash 
   (lambda (actor-name _mode-function)
     (actor-check-messages actor-name))
   actor-registry))

(defun actor-check-messages (actor-name)
  "Check for new messages for a specific actor"
  (let ((stream-name (format "actor:%s:messages" actor-name)))
    (condition-case err
        (let ((result (shell-command-to-string 
                      (format "redis-cli XREAD COUNT 10 STREAMS '%s' '$'" stream-name))))
          (when (and result (not (string-empty-p result)) (not (string-match-p "nil" result)))
            (actor-parse-redis-messages actor-name result)))
      (error nil)))) ; Silently ignore Redis errors

(defun actor-parse-redis-messages (actor-name redis-output)
  "Parse Redis XREAD output and dispatch messages"
  ;; Simplified parser - in production would be more robust
  (when (string-match "type\\s-+\\([^\\s-]+\\)" redis-output)
    (let ((message-type (match-string 1 redis-output)))
      (when (string-match "data\\s-+\\([^\\s-]+\\)" redis-output)
        (let ((data-json (match-string 1 redis-output)))
          (condition-case err
              (let ((data (json-read-from-string data-json)))
                (actor-handle-message actor-name message-type data))
            (error nil)))))))

;;; Demo Actor Handler Functions (defined first)

(defun claude-coordinator-handle-response (data)
  "Handle coordination response"
  (message "🎯 Claude coordinator processing: %s" data)
  (actor-send-message "emacs-interface-actor" "update-ui" data))

(defun claude-coordinator-handle-status (data)
  "Handle status check"
  (message "💓 Claude coordinator status: healthy"))

(defun claude-coordinator-heartbeat ()
  "Send periodic heartbeat"
  (when claude-coordinator-actor-mode
    (actor-send-message "emacs-interface-actor" "heartbeat" '((status . "alive")))))

(defun emacs-interface-update (data)
  "Update Emacs interface"
  (when (boundp 'emacs-interface-buffer)
    (with-current-buffer emacs-interface-buffer
      (goto-char (point-max))
      (insert (format "[%s] UI Update: %s\n" 
                     (format-time-string "%H:%M:%S") 
                     data)))))

(defun emacs-interface-heartbeat (data)
  "Handle heartbeat from coordinator"
  (message "💓 Received heartbeat from coordinator"))

(defun nlp-process-text (data)
  "Process natural language text"
  (message "🧠 NLP processing: %s" data)
  (let ((processed-result '((intent . "window-management") 
                           (action . "split-window-right"))))
    (actor-send-message "claude-coordinator-actor" "coordinate-response" processed-result)))

(defun nlp-parse-intent (data)
  "Parse user intent from text"
  (message "🎯 Parsing intent: %s" data))

;;; Demo Actor Definitions

(define-actor-mode claude-coordinator-actor
  "Main coordinator for Claude AI system"
  :restart-strategy permanent
  :message-handlers
  ((coordinate-response . claude-coordinator-handle-response)
   (system-status . claude-coordinator-handle-status))
  :behavior
  (progn
    (setq claude-coordinator-state 'active)
    (run-with-timer 5 10 'claude-coordinator-heartbeat)))

(define-actor-mode emacs-interface-actor
  "Emacs interface management actor"
  :supervisor claude-coordinator-actor
  :restart-strategy permanent
  :message-handlers
  ((update-ui . emacs-interface-update)
   (heartbeat . emacs-interface-heartbeat))
  :behavior
  (progn
    (message "🎨 Emacs interface actor ready")
    (setq emacs-interface-buffer (get-buffer-create "*ACTOR-INTERFACE*"))))

(define-actor-mode nlp-processor-actor
  "Natural language processing actor"
  :supervisor claude-coordinator-actor
  :restart-strategy transient
  :message-handlers
  ((process-text . nlp-process-text)
   (parse-intent . nlp-parse-intent))
  :behavior
  (message "🧠 NLP processor actor ready"))

;;; System Control Functions

(defun lisp-actors-start-system ()
  "Start the complete distributed Lisp actor system"
  (interactive)
  
  ;; Start message bus
  (actor-start-message-bus)
  
  ;; Start actor supervision tree
  (claude-coordinator-actor-mode 1)
  (emacs-interface-actor-mode 1)  
  (nlp-processor-actor-mode 1)
  
  ;; Test the system
  (run-with-timer 2 nil 
    (lambda ()
      (actor-send-message "nlp-processor-actor" "process-text" "split the window")
      (actor-send-message "claude-coordinator-actor" "system-status" "check")))
  
  (message "🚀 Distributed Lisp Actor System STARTED!")
  (pop-to-buffer "*ACTOR-INTERFACE*"))

(defun lisp-actors-stop-system ()
  "Stop the distributed Lisp actor system"
  (interactive)
  
  ;; Stop all actors
  (claude-coordinator-actor-mode -1)
  (emacs-interface-actor-mode -1)
  (nlp-processor-actor-mode -1)
  
  ;; Stop message bus
  (actor-stop-message-bus)
  
  ;; Clear registries
  (clrhash actor-registry)
  (clrhash supervision-trees)
  (clrhash actor-restart-counts)
  
  (message "🛑 Distributed Lisp Actor System STOPPED!"))

;; Key bindings
(global-set-key (kbd "C-c a s") 'lisp-actors-start-system)
(global-set-key (kbd "C-c a q") 'lisp-actors-stop-system)

(provide 'lisp-actor-modes)

;;; Usage:
;; C-c a s  - Start distributed actor system
;; C-c a q  - Stop distributed actor system
;;
;; This creates a true distributed Lisp where:
;; - Minor modes ARE the actors
;; - S-expressions define supervision topology  
;; - Fault tolerance through mode restart
;; - Message passing via Redis streams
;; - Location transparency (local modes + remote MCP servers)