(defun launch-reactive-monitor ()
  "Launch the reactive_monitor.py script in a dedicated buffer.
   Its output will appear in the *Reactive Monitor Output* buffer."
  (interactive)
  (unless (process-live-p reactive-monitor-process)
    (let* ((script-path "/Users/jonathanhill/src/redis-ai-challenge/reactive_monitor.py")
           ;; Use the specific pyenv python executable
           (python-executable "/Users/jonathanhill/.pyenv/versions/3.12.2/bin/python3") 
           (command (format "%s %s" (shell-quote-argument python-executable) (shell-quote-argument script-path)))
           (buffer (get-buffer-create "*Reactive Monitor Output*")))
      (message "Launching reactive_monitor.py...")
      (setq reactive-monitor-process
            (start-process-shell-command
             "reactive-monitor" ; Process name
             buffer             ; Buffer to send output to
             command))
      (display-buffer buffer)
      (message "reactive_monitor.py launched. Process ID: %s" (process-id reactive-monitor-process))))
  (unless (process-live-p reactive-monitor-process)
    (message "Failed to launch reactive_monitor.py. Check path and permissions.")))

(defun stop-reactive-monitor ()
  "Stop the reactive_monitor.py script."
  (interactive)
  (when (process-live-p reactive-monitor-process)
    (message "Stopping reactive_monitor.py (PID: %s)..." (process-id reactive-monitor-process))
    (kill-process reactive-monitor-process)
    (setq reactive-monitor-process nil)
    (message "reactive_monitor.py stopped."))
  (unless (process-live-p reactive-monitor-process)
    (message "reactive_monitor.py is not running.")))

(provide 'launch-reactive-monitor)
