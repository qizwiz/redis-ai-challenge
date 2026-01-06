# Project Overview

This project is a submission for the Redis AI Challenge 2025. It's an Emacs-centric intelligent development environment that uses Redis as a backbone for real-time AI-powered coding assistance. The project leverages several advanced Redis patterns, including StreamFlow AI for high-throughput event processing, MLQ for fault-tolerant job queues, and RedisAI for model serving. A key innovation is the use of Redis for "homoiconicity," where Lisp code is stored and manipulated as Redis data structures.

The system is designed to capture keystrokes in Emacs, process them in real-time through Redis streams, trigger AI models (including local, HuggingFace, and proprietary models), and then execute commands back in Emacs. It also features a sophisticated, multi-agent architecture for coordinating different AI models and development tasks.

**Key Technologies:**

*   **Language:** Python
*   **Database:** Redis
*   **AI/ML:** OpenAI, Azure Cognitive Services, scikit-learn, pandas, numpy
*   **Frameworks/Libraries:** FastMCP, MCP
*   **Integration:** Emacs Lisp

# Building and Running

The project is designed for easy setup and demonstration.

**Prerequisites:**

*   Python 3
*   Redis server running on `localhost:6379`

**Installation:**

```bash
pip install -r requirements.txt
```

**Running the Demos:**

There are several ways to run the demos, as outlined in the `README.md`:

1.  **Quick Setup and Standalone Demo:** This is the easiest way to see the project in action.

    ```bash
    ./QUICK_DEMO_SETUP.sh
    python standalone_redis_ai_demo.py
    ```

2.  **Production Integration Demo:** This showcases the more advanced, production-ready patterns.

    ```bash
    python streamflow_integrated_system.py
    ```

3.  **Redis Homoiconicity Demo:** This demonstrates the novel concept of storing and executing Lisp code in Redis.

    ```bash
    python redis_lisp_interpreter.py
    ```

4.  **Interactive Launcher:** This script provides a menu to run any of the demos.

    ```bash
    ./LAUNCH_SCRIPT.sh
    ```

**Testing:**

The project includes a `tests` directory, and it appears to use `pytest` for testing. To run the tests, you would likely use:

```bash
pytest
```

*(TODO: Confirm the exact test command if it differs from the standard `pytest` command.)*

# Development Conventions

Based on the code, the following conventions are in use:

*   **Typing:** The code uses Python type hints extensively.
*   **Logging:** The `logging` module is used for logging, with different log levels for different types of information.
*   **Modularity:** The project is broken down into many small, single-purpose Python files.
*   **Object-Oriented Programming:** The code makes heavy use of classes to represent different components of the system.
*   **Concurrency:** The project uses `asyncio` and `threading` for concurrent operations, especially in the `streamflow_integrated_system.py` file.
*   **Emacs Lisp:** Emacs Lisp files (`.el`) are used for the Emacs integration.
*   **Shell Scripts:** Shell scripts (`.sh`) are used for setup and to provide convenient launchers for the demos.
*   **Markdown:** Markdown files (`.md`) are used for documentation.
ACTIVITY TEST - Mon Aug 11 17:36:36 CDT 2025
