#!/usr/bin/env python3
"""
Homoiconic Learning - My learning system expressed as Redis data structures

The insight: My learning process itself can be stored as executable Redis structures
- Lessons = Redis lists (homoiconic s-expressions)
- Improvements = Redis lists that modify other lists
- Meta-learning = Code that generates code in Redis
"""

import redis
import json
import time

class HomoiconicLearning:
    """Learning system where lessons and improvements are homoiconic Redis data"""

    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.session = f"homoiconic_learning_{int(time.time())}"

    def store_lesson_as_sexp(self, lesson_name, actions):
        """Store a lesson as executable Redis list (s-expression)"""
        # Example: (with-temp-buffer (insert "text") (buffer-string))
        # Becomes: ["with-temp-buffer", ["insert", "text"], ["buffer-string"]]

        lesson_key = f"{self.session}:lesson:{lesson_name}"

        # Store as Redis list (homoiconic!)
        self.redis.delete(lesson_key)
        for action in actions:
            self.redis.rpush(lesson_key, json.dumps(action))

        # Store metadata as hash
        meta_key = f"{lesson_key}:meta"
        self.redis.hset(meta_key, mapping={
            'type': 'lesson',
            'name': lesson_name,
            'action_count': len(actions),
            'created': time.time(),
            'executable': 'true'
        })

        return lesson_key

    def execute_lesson(self, lesson_key):
        """Execute lesson by evaluating Redis list as s-expression"""
        # Get the lesson (it's a Redis list)
        lesson_data = self.redis.lrange(lesson_key, 0, -1)
        actions = [json.loads(item) for item in lesson_data]

        results = []
        for action in actions:
            # Each action is itself an s-expression
            result = self._eval_sexp(action)
            results.append(result)

        return results

    def _eval_sexp(self, sexp):
        """Evaluate s-expression (homoiconic evaluation)"""
        if not isinstance(sexp, list) or len(sexp) == 0:
            return sexp

        # First element is function, rest are arguments
        fn = sexp[0]
        args = sexp[1:] if len(sexp) > 1 else []

        # Built-in operations
        if fn == 'log-to-redis':
            return self._log_to_redis(*args)
        elif fn == 'get-from-redis':
            return self._get_from_redis(*args)
        elif fn == 'compose':
            # Homoiconic composition: (compose f g x) = (f (g x))
            return self._compose(*args)
        elif fn == 'quote':
            # Return without evaluation
            return args[0] if args else None
        else:
            # Unknown function
            return {'error': f'Unknown function: {fn}', 'sexp': sexp}

    def _log_to_redis(self, stream, data):
        """Log data to Redis stream"""
        return self.redis.xadd(stream, {'data': json.dumps(data), 'timestamp': time.time()})

    def _get_from_redis(self, key):
        """Get data from Redis"""
        return self.redis.get(key)

    def _compose(self, *sexps):
        """Compose s-expressions (homoiconic function composition)"""
        # Execute from right to left
        result = None
        for sexp in reversed(sexps):
            if result is not None:
                # Replace last arg with previous result
                sexp = sexp[:-1] + [result] if len(sexp) > 1 else sexp
            result = self._eval_sexp(sexp)
        return result

    def store_improvement_as_code(self, improvement_name, transform):
        """Store improvement as code that modifies other code (meta-homoiconicity)"""
        # An improvement is code that transforms lessons (code that modifies code)

        improvement_key = f"{self.session}:improvement:{improvement_name}"

        # Store transformation as executable list
        self.redis.delete(improvement_key)
        for step in transform:
            self.redis.rpush(improvement_key, json.dumps(step))

        self.redis.hset(f"{improvement_key}:meta", mapping={
            'type': 'improvement',
            'name': improvement_name,
            'is_code_that_modifies_code': 'true',
            'meta_level': '2'  # Code about code
        })

        return improvement_key

    def apply_improvement_to_lesson(self, improvement_key, lesson_key):
        """Apply improvement (code) to lesson (code) - meta-homoiconicity!"""
        # Get improvement transformation
        improvement = [json.loads(x) for x in self.redis.lrange(improvement_key, 0, -1)]

        # Get original lesson
        lesson = [json.loads(x) for x in self.redis.lrange(lesson_key, 0, -1)]

        # Apply transformation (code modifying code)
        improved_lesson = self._apply_transform(improvement, lesson)

        # Store improved lesson
        improved_key = f"{lesson_key}:improved"
        self.redis.delete(improved_key)
        for action in improved_lesson:
            self.redis.rpush(improved_key, json.dumps(action))

        return improved_key

    def _apply_transform(self, transform, code):
        """Apply transformation to code (meta-programming)"""
        # Example transforms:
        # ['prepend', action] - add action at beginning
        # ['append', action] - add action at end
        # ['wrap', before, after] - wrap code

        result = list(code)  # Copy

        for t in transform:
            if not isinstance(t, list) or len(t) == 0:
                continue

            op = t[0]
            if op == 'prepend' and len(t) > 1:
                result.insert(0, t[1])
            elif op == 'append' and len(t) > 1:
                result.append(t[1])
            elif op == 'wrap' and len(t) > 2:
                result = [t[1]] + result + [t[2]]

        return result

def demonstrate_homoiconic_learning():
    """Demonstrate homoiconic learning system"""
    hl = HomoiconicLearning()

    print("🎯 Demonstrating Homoiconic Learning with Redis")
    print()

    # 1. Store a lesson as executable s-expression
    print("1. Storing lesson as Redis list (s-expression)...")
    lesson = [
        ['log-to-redis', 'emacs:homoiconic', {'action': 'buffer-created'}],
        ['log-to-redis', 'emacs:homoiconic', {'action': 'text-inserted'}],
    ]
    lesson_key = hl.store_lesson_as_sexp('basic-buffer-ops', lesson)
    print(f"   ✅ Stored at: {lesson_key}")
    print(f"   Redis list contains: {hl.redis.lrange(lesson_key, 0, -1)}")
    print()

    # 2. Execute the lesson (evaluate the s-expression)
    print("2. Executing lesson (evaluating s-expression)...")
    results = hl.execute_lesson(lesson_key)
    print(f"   ✅ Execution results: {results}")
    print()

    # 3. Store an improvement as code-that-modifies-code
    print("3. Storing improvement as transformation (meta-level)...")
    improvement = [
        ['prepend', ['log-to-redis', 'emacs:homoiconic', {'meta': 'lesson-starting'}]],
        ['append', ['log-to-redis', 'emacs:homoiconic', {'meta': 'lesson-complete'}]]
    ]
    imp_key = hl.store_improvement_as_code('add-logging', improvement)
    print(f"   ✅ Improvement stored at: {imp_key}")
    print()

    # 4. Apply improvement to lesson (code modifying code!)
    print("4. Applying improvement to lesson (code → code transformation)...")
    improved_key = hl.apply_improvement_to_lesson(imp_key, lesson_key)
    print(f"   ✅ Improved lesson at: {improved_key}")

    # Compare original vs improved
    original = hl.redis.lrange(lesson_key, 0, -1)
    improved = hl.redis.lrange(improved_key, 0, -1)
    print(f"   Original: {len(original)} actions")
    print(f"   Improved: {len(improved)} actions")
    print()

    # 5. Execute improved lesson
    print("5. Executing improved lesson...")
    improved_results = hl.execute_lesson(improved_key)
    print(f"   ✅ Results: {improved_results}")
    print()

    # 6. Show homoiconic property
    print("6. Demonstrating homoiconicity...")
    print("   Data (Redis list):")
    print(f"     {hl.redis.lrange(improved_key, 0, 2)}")
    print("   IS ALSO")
    print("   Code (executable s-expression):")
    print(f"     (lesson basic-buffer-ops ...)")
    print()
    print("   ✅ Same representation = Homoiconic!")
    print()

    # 7. Check Redis streams
    stream_len = hl.redis.xlen('emacs:homoiconic')
    print(f"7. Verified in Redis: {stream_len} entries logged")
    print()

    print("🎯 Homoiconic Learning Complete!")
    print()
    print("Key insight: Lessons, improvements, and meta-learning are ALL")
    print("represented as Redis data structures that are also executable code.")
    print()
    print("This means:")
    print("  - Lessons can modify themselves")
    print("  - Improvements can improve improvements")
    print("  - Meta-learning is just code at a higher level")
    print("  - Everything is queryable in Redis")

if __name__ == '__main__':
    demonstrate_homoiconic_learning()
