# Claude Code live development test
import redis


def test_claude_can_code():
    # This was written by Claude directly in Emacs
    r = redis.Redis(decode_responses=True)
    r.set("claude_dev_test", "LIVE_CODING")
    return r.get("claude_dev_test")


if __name__ == "__main__":
    result = test_claude_can_code()
    print(f"Claude development test: {result}")
