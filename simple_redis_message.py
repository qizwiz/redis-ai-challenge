#!/usr/bin/env python3
import redis

r = redis.Redis(decode_responses=True)

# Just send the message structure that the system expects
r.xadd("emacs:commands", {"action": "delete-other-windows"})

print("Message sent")
