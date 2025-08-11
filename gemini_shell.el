;;; gemini_shell.el --- An interactive shell for Gemini

;;; Commentary:

;; This file provides an interactive shell environment for the Gemini AI.
;; It uses the process supervision framework from real_process_monitor.el
;; to create and manage a persistent shell process.

;;; Code:

(require 'real-process-monitor)

(defvar gemini-shell-process-name "gemini-shell"
  "The name of the Gemini shell process.")

(defun gemini-shell-start ()
  "Start the Gemini interactive shell."
  (interactive)
  (unless (gethash gemini-shell-process-name process-registry)
    (supervisor-register-process gemini-shell-process-name
                                 "/bin/bash"
                                 '("-i")
                                 'permanent
                                 nil))
  (supervisor-start-process gemini-shell-process-name)
  (switch-to-buffer (format "*%s*" gemini-shell-process-name)))

(defun gemini-shell-send-command (command)
  "Send a COMMAND string to the Gemini shell."
  (interactive "sCommand: ")
  (let ((process (process-info-process (gethash gemini-shell-process-name process-registry))))
    (if (and process (process-live-p process))
        (progn
          (process-send-string process (concat command "\n"))
          (message "Sent to %s: %s" gemini-shell-process-name command))
      (message "Gemini shell not running. Start it with 'gemini-shell-start'."))))

(defun gemini-shell-start-mcp-servers ()
  "Start all MCP servers using a shell script."
  (interactive)
  (message "Starting MCP servers via shell script...")
  (start-process "mcp-server-launcher" nil "bash" "/Users/jonathanhill/src/redis-ai-challenge/start_mcp_servers.sh")
  (message "MCP server launcher started. Check /Users/jonathanhill/src/redis-ai-challenge/tmp_logs/*.log files for output."))

(provide 'gemini-shell)

;;; gemini_shell.el ends here