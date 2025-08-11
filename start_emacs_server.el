;;; start-emacs-server.el --- Fix Emacs server socket issue -*- lexical-binding: t; -*-

;;; Commentary:
;;
;; This fixes the emacsclient socket issue by properly starting the server
;; with the correct socket name for our Redis-Emacs integration.

;;; Code:

(defun start-redis-emacs-server ()
  "Start Emacs server with redis-tutorial socket name."
  (interactive)
  
  ;; Stop any existing server
  (when (and (boundp 'server-process) server-process)
    (server-force-delete))
  
  ;; Set server name for our Redis integration
  (setq server-name "redis-tutorial")
  
  ;; Start the server
  (server-start)
  
  (message "✅ Redis-Emacs server started with socket: %s" server-name)
  (message "✅ Now you can test with: python WORKING_DEMO.py"))

(defun check-redis-emacs-server ()
  "Check if the Redis-Emacs server is running."
  (interactive)
  (if (and (boundp 'server-process) server-process)
      (message "✅ Redis-Emacs server is running (socket: %s)" 
               (or server-name "default"))
    (message "❌ Redis-Emacs server is not running. Run M-x start-redis-emacs-server")))

;; Auto-start the server when this file is loaded
(start-redis-emacs-server)

(provide 'start-emacs-server)

;;; start-emacs-server.el ends here