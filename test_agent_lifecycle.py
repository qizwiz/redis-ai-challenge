import asyncio
import redis
import logging

from redis_coordination_protocol import StreamManager, EventType
from code_analyzer_agent import AdvancedCodeAnalyzerAgent

# Setup logging for this script
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting isolated agent lifecycle test...")

    redis_client = redis.Redis(decode_responses=True)

    try:
        redis_client.ping()
        logger.info("Redis connection established.")
    except redis.ConnectionError:
        logger.error("Could not connect to Redis. Make sure Redis is running.")
        return

    # Destroy consumer group for a clean start
    try:
        redis_client.xgroup_destroy(
            StreamManager.STREAMS[EventType.CONTENT_CHANGE], "ai_agents"
        )
        logger.info(
            f"Destroyed consumer group 'ai_agents' for {StreamManager.STREAMS[EventType.CONTENT_CHANGE]}"
        )
    except redis.ResponseError as e:
        if "NOGROUP" in str(e):
            logger.info(
                f"Consumer group 'ai_agents' for {StreamManager.STREAMS[EventType.CONTENT_CHANGE]} did not exist."
            )
        else:
            logger.error(f"Error destroying consumer group: {e}")

    # Create and start the AdvancedCodeAnalyzerAgent
    agent = AdvancedCodeAnalyzerAgent(redis_client)
    await agent.start()
    logger.info(f"Agent {agent.agent_id} started. Consumer name: {agent.consumer_name}")

    # Keep the main event loop running indefinitely
    logger.info(
        "Agent is running. Manually publish messages to 'emacs:content' stream using redis-cli."
    )
    logger.info(
        'Example: redis-cli XADD emacs:content * event_type content_change source manual data "{\\"buffer_name\\": \\"manual_test\\", \\"content\\": \\"This is a manual test.\\", \\"position\\": 0}""'
    )
    logger.info("Press Ctrl+C to stop the script.")

    try:
        await asyncio.Event().wait()  # Keep event loop running indefinitely
    except asyncio.CancelledError:
        logger.info("Script stopped by user.")
    finally:
        await agent.stop()
        logger.info("Agent stopped.")


if __name__ == "__main__":
    asyncio.run(main())
