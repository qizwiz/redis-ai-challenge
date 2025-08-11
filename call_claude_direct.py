import asyncio
import subprocess
import os


async def call_claude_directly(prompt: str):
    claude_path = "/Users/jonathanhill/.bun/bin/claude"

    # Set up environment variables as seen in claude_api_integration.py
    env = os.environ.copy()
    env["PATH"] = (
        "/Users/jonathanhill/.bun/bin:/Users/jonathanhill/.opencode/bin:/Users/jonathanhill/.codeium/windsurf/bin:/Users/jonathanhill/.pyenv/shims:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin"
    )

    try:
        process = await asyncio.create_subprocess_exec(
            claude_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        stdout, stderr = await process.communicate(input=prompt.encode("utf-8"))

        if process.returncode == 0:
            print("Claude Response (stdout):")
            print(stdout.decode("utf-8"))
        else:
            print("Claude Error (stderr):")
            print(stderr.decode("utf-8"))
            print(f"Claude process exited with code: {process.returncode}")

    except FileNotFoundError:
        print(f"Error: Claude executable not found at {claude_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


async def main():
    simple_prompt = (
        "Hello Claude, please tell me a short, interesting fact about the universe."
    )
    await call_claude_directly(simple_prompt)


if __name__ == "__main__":
    asyncio.run(main())
