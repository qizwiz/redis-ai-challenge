;;; real_process_monitor.el --- Actually working process supervision

;; -*- lexical-binding: t -*-

(require 'real-redis-parser)
(require 'cl-lib)

(defvar process-registry (make-hash-table :test 'equal)
  "Registry of supervised processes: name -> process-info")

(defvar supervision-monitor-timer nil
  "Timer for checking process health")

(cl-defstruct process-info
  name
  command
  args
  process          ; actual Emacs process object
  restart-strategy ; permanent, transient, temporary
  restart-count
  max-restarts
  supervisor       ; parent supervisor name
  children         ; list of child process names
  last-restart
  status)          ; running, crashed, stopped

(defun supervisor-register-process (name command args restart-strategy supervisor)
  "Register a process for supervision
  
  Returns the process-info object"
  (let ((info (make-process-info
               :name name
               :command command
               :args args
               :restart-strategy restart-strategy
               :restart-count 0
               :max-restarts 5
               :supervisor supervisor
               :children '()
               :status 'stopped)))
    
    (puthash name info process-registry)
    
    ;; Add to supervisor's children list
    (when supervisor
      (let ((supervisor-info (gethash supervisor process-registry)))
        (when supervisor-info
          (push name (process-info-children supervisor-info)))))
    
    (message "📋 Process registered: %s" name)
    info))

(defun supervisor-start-process (name)
  "Start a supervised process
  
  Returns t on success, nil on failure"
  (let ((info (gethash name process-registry)))
    (if (not info)
        (progn
          (message "❌ Process not registered: %s" name)
          nil)
      
      (when (and (process-info-process info)
                 (process-live-p (process-info-process info)))
        (message "⚠️ Process already running: %s" name)
        (return t))
      
      (condition-case err
          (let* ((command (process-info-command info))
                 (args (process-info-args info))
                 (process (apply #'start-process 
                                name 
                                (format "*%s*" name)
                                command 
                                args)))
            
            (setf (process-info-process info) process)
            (setf (process-info-status info) 'running)
            
            ;; Set up process sentinel for monitoring  
            (set-process-sentinel process
                                  `(lambda (proc event)
                                     (supervisor-handle-process-event ,name proc event)))
            
            (message "🚀 Process started: %s (PID: %s)" name (process-id process))
            
            ;; Notify Redis
            (redis-send-stream-message "supervisor:events"
                                      `((event . "process_started")
                                        (process . ,name)
                                        (pid . ,(process-id process))
                                        (timestamp . ,(float-time))))
            t)
        
        (error
         (message "❌ Failed to start process %s: %s" name (error-message-string err))
         (setf (process-info-status info) 'crashed)
         nil)))))

(defun supervisor-stop-process (name &optional force)
  "Stop a supervised process
  
  If force is t, kill immediately. Otherwise, terminate gracefully."
  (let ((info (gethash name process-registry)))
    (when info
      (let ((process (process-info-process info)))
        (when (and process (process-live-p process))
          (if force
              (kill-process process)
            (interrupt-process process))
          
          (setf (process-info-status info) 'stopped)
          (message "🛑 Process stopped: %s" name)
          
          ;; Notify Redis
          (redis-send-stream-message "supervisor:events"
                                    `((event . "process_stopped")
                                      (process . ,name)
                                      (timestamp . ,(float-time))))
          t)))))

(defun supervisor-handle-process-event (name process event)
  "Handle process state changes (sentinel function)"
  (let ((info (gethash name process-registry)))
    (when info
      (cond
       ((string-match "finished" event)
        (message "✅ Process finished normally: %s" name)
        (setf (process-info-status info) 'finished)
        (supervisor-maybe-restart name 'normal))
       
       ((string-match "killed\\|terminated" event)
        (message "💀 Process died: %s (%s)" name (string-trim event))
        (setf (process-info-status info) 'crashed)
        (supervisor-maybe-restart name 'abnormal))
       
       (t
        (message "⚠️ Process event: %s - %s" name (string-trim event)))))))

(defun supervisor-maybe-restart (name exit-type)
  "Decide whether to restart a process based on strategy and exit type"
  (let ((info (gethash name process-registry)))
    (when info
      (let ((strategy (process-info-restart-strategy info))
            (restart-count (process-info-restart-count info))
            (max-restarts (process-info-max-restarts info)))
        
        (cond
         ;; Never restart temporary processes
         ((eq strategy 'temporary)
          (message "⏹️ Temporary process %s will not restart" name))
         
         ;; Only restart transient processes if they crashed
         ((and (eq strategy 'transient) (eq exit-type 'normal))
          (message "⏹️ Transient process %s finished normally, not restarting" name))
         
         ;; Check restart limits
         ((>= restart-count max-restarts)
          (message "❌ Process %s exceeded restart limit (%d)" name max-restarts)
          (supervisor-handle-restart-failure name))
         
         ;; Restart the process
         (t
          (message "🔄 Restarting process: %s (attempt %d)" name (1+ restart-count))
          (setf (process-info-restart-count info) (1+ restart-count))
          (setf (process-info-last-restart info) (float-time))
          
          ;; Wait a bit before restarting
          (run-with-timer 2 nil
                         `(lambda ()
                           (supervisor-start-process ,name)))))))))

(defun supervisor-handle-restart-failure (name)
  "Handle when a process can't be restarted"
  (let ((info (gethash name process-registry)))
    (when info
      (let ((supervisor-name (process-info-supervisor info)))
        (message "💥 Process %s failed permanently" name)
        
        ;; Notify Redis
        (redis-send-stream-message "supervisor:events"
                                  `((event . "process_failed")
                                    (process . ,name)
                                    (timestamp . ,(float-time))))
        
        ;; Escalate to supervisor if we have one
        (when supervisor-name
          (message "⬆️ Escalating failure to supervisor: %s" supervisor-name)
          (supervisor-handle-child-failure supervisor-name name))))))

(defun supervisor-handle-child-failure (supervisor-name failed-child)
  "Handle when a supervised child fails permanently"
  (let ((supervisor-info (gethash supervisor-name process-registry)))
    (when supervisor-info
      ;; For now, just restart the supervisor
      ;; In a real implementation, we'd have different strategies
      (message "🔄 Supervisor %s restarting due to child failure: %s" 
               supervisor-name failed-child)
      (supervisor-restart-all-children supervisor-name))))

(defun supervisor-restart-all-children (supervisor-name)
  "Restart all children of a supervisor"
  (let ((supervisor-info (gethash supervisor-name process-registry)))
    (when supervisor-info
      (dolist (child-name (process-info-children supervisor-info))
        (message "🔄 Restarting child: %s" child-name)
        (supervisor-stop-process child-name t)
        (run-with-timer 1 nil 
                       `(lambda ()
                         (supervisor-start-process ,child-name)))))))

(defun supervisor-start-monitoring ()
  "Start the supervision monitoring system"
  (when supervision-monitor-timer
    (cancel-timer supervision-monitor-timer))
  
  (setq supervision-monitor-timer
        (run-with-timer 0 5 #'supervisor-check-all-processes))
  
  (message "👁️ Process supervision monitoring started"))

(defun supervisor-stop-monitoring ()
  "Stop the supervision monitoring system"
  (when supervision-monitor-timer
    (cancel-timer supervision-monitor-timer)
    (setq supervision-monitor-timer nil))
  
  (message "👁️ Process supervision monitoring stopped"))

(defun supervisor-check-all-processes ()
  "Check health of all supervised processes"
  (maphash
   (lambda (name info)
     (let ((process (process-info-process info))
           (status (process-info-status info)))
       
       ;; Check if process that should be running is actually dead
       (when (and (eq status 'running)
                  (or (not process) (not (process-live-p process))))
         (message "💀 Detected dead process: %s" name)
         (setf (process-info-status info) 'crashed)
         (supervisor-maybe-restart name 'abnormal))))
   process-registry))

(defun supervisor-status ()
  "Show status of all supervised processes"
  (interactive)
  
  (with-current-buffer (get-buffer-create "*Process-Supervision*")
    (erase-buffer)
    (insert "🔍 PROCESS SUPERVISION STATUS\n")
    (insert "==============================\n\n")
    
    (if (= 0 (hash-table-count process-registry))
        (insert "No supervised processes registered.\n")
      
      (maphash
       (lambda (name info)
         (let ((process (process-info-process info))
               (status (process-info-status info))
               (restart-count (process-info-restart-count info)))
           
           (insert (format "Process: %s\n" name))
           (insert (format "  Status: %s\n" status))
           (insert (format "  Strategy: %s\n" (process-info-restart-strategy info)))
           (insert (format "  Restarts: %d/%d\n" restart-count (process-info-max-restarts info)))
           (insert (format "  Command: %s %s\n" 
                          (process-info-command info)
                          (string-join (process-info-args info) " ")))
           
           (when process
             (insert (format "  PID: %s\n" (process-id process)))
             (insert (format "  Live: %s\n" (process-live-p process))))
           
           (when (process-info-supervisor info)
             (insert (format "  Supervisor: %s\n" (process-info-supervisor info))))
           
           (when (process-info-children info)
             (insert (format "  Children: %s\n" 
                            (string-join (process-info-children info) ", "))))
           
           (insert "\n")))
       process-registry))
    
    (goto-char (point-min))
    (pop-to-buffer (current-buffer))))

;; Test supervision system
(defun supervisor-test-system ()
  "Test the supervision system with a real crashing process"
  (interactive)
  
  ;; Register a process that will crash
  (supervisor-register-process "test-crasher"
                              "python3"
                              '("-c" "import time; time.sleep(2); exit(1)")
                              'permanent
                              nil)
  
  ;; Register a stable process
  (supervisor-register-process "test-stable"
                              "python3" 
                              '("-c" "import time; [print(f'stable {i}') or time.sleep(1) for i in range(60)]")
                              'permanent
                              nil)
  
  ;; Start monitoring
  (supervisor-start-monitoring)
  
  ;; Start processes
  (supervisor-start-process "test-crasher")
  (supervisor-start-process "test-stable")
  
  (message "🧪 Supervision test started - check *Process-Supervision* buffer")
  (run-with-timer 1 nil #'supervisor-status))

(provide 'real-process-monitor)