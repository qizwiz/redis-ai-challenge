# AI Pair Programming Demo
# Let's build a Redis-coordinated function together


def redis_counter():
    """A simple counter using Redis"""
    import redis

    r = redis.Redis()

    # TODO: Add implementation here

    # AI suggestion: Let's implement the counter logic
    count = r.get("counter") or 0
    count = int(count) + 1
    r.set("counter", count)
    return count


# Now let's add a test function
def test_counter():
    """Test the Redis counter"""
    print(f"Count: {redis_counter()}")
    print(f"Count: {redis_counter()}")
    print(f"Count: {redis_counter()}")


if __name__ == "__main__":
    # AI pair programming in action!
    print("🤖 AI and human coding together")
    test_counter()
