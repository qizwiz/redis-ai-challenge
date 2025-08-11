#!/usr/bin/env python3
"""Direct call to redis-emacs-fastmcp emacs_command tool"""

import sys
import os

sys.path.append(os.path.dirname(__file__))

from redis_emacs_fastmcp_server import redis_emacs

# Execute the command directly
result = redis_emacs.execute_elisp_sequence(["(delete-other-windows)"])

if result["success"]:
    print("✅ Windows deleted successfully")
else:
    print(f"❌ Failed: {result['error']}")
