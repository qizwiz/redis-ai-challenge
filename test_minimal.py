# Testing my "mean it when I say minimal" improvement
# Claim: 3 lines that prove something works
# Reality: Let's actually build 3 lines

import redis
r = redis.Redis(decode_responses=True)
print("Minimal test:", r.ping())