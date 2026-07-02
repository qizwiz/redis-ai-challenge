
        (defun test-redis-write ()
          (let ((redis-cli "redis-cli"))
            (uiop:run-program (list redis-cli "SET" "lisp_test_key" "success"))))
        (test-redis-write)
        