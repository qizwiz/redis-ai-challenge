(defun get-python-env-info () "Get information about the Python environment Emacs is using." (interactive) (let* ((output-buffer (get-buffer-create "*Python Env Info*")) (which-python-cmd "which python3") (sys-path-python-code "import sys; print(sys.path)") (sys-path-cmd (format "python3 -c %s" (shell-quote-argument sys-path-python-code))) (redis-test-python-code "import redis; print('Redis found!')") (redis-test-cmd (format "python3 -c %s" (shell-quote-argument redis-test-python-code)))) (with-current-buffer output-buffer (erase-buffer) (insert "--- which python3 ---
") (insert (shell-command-to-string which-python-cmd)) (insert "
") (insert (format "--- python3 -c %s ---" (shell-quote-argument sys-path-python-code))) (insert "
") (insert (shell-command-to-string sys-path-cmd)) (insert "
") (insert (format "--- python3 -c %s ---" (shell-quote-argument redis-test-python-code))) (insert "
") (insert (shell-command-to-string redis-test-cmd)) (insert "
") (goto-char (point-min)) (message "Python environment info collected in *Python Env Info* buffer.")) (display-buffer output-buffer) (with-current-buffer output-buffer (buffer-string))))