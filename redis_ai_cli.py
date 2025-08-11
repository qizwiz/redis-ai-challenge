#!/usr/bin/env python3

import sys
import json
import logging
from standalone_redis_ai_demo import StandaloneRedisAIDemo

# Disable logging when running as a CLI tool
logging.basicConfig(level=logging.CRITICAL)


def main():
    demo = StandaloneRedisAIDemo()

    if len(sys.argv) < 2:
        print("Usage: python redis_ai_cli.py <command> [args]")
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "classify_text":
        if not args:
            print("Usage: python redis_ai_cli.py classify_text <text>")
            sys.exit(1)
        text_to_classify = args[0]
        result = demo.classify_with_free_ai(text_to_classify)
        print(json.dumps(result))
    elif command == "demonstrate_homoiconicity":
        result = demo.demonstrate_redis_homoiconicity()
        print(json.dumps({"success": result}))
    elif command == "demonstrate_ml_coordination":
        result = demo.demonstrate_ml_coordination()
        print(json.dumps({"success": result}))
    elif command == "demonstrate_intelligent_data_manipulation":
        result = demo.demonstrate_intelligent_data_manipulation()
        print(json.dumps({"success": result}))
    elif command == "demonstrate_real_time_learning":
        result = demo.demonstrate_real_time_learning()
        print(json.dumps({"success": result}))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
