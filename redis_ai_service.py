import redis
import json
import time
import os
import logging
from standalone_redis_ai_demo import StandaloneRedisAIDemo

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RedisAIService:
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_client = redis.Redis(
            host=self.redis_host, port=self.redis_port, decode_responses=True
        )
        self.demo = StandaloneRedisAIDemo()
        logger.info("RedisAIService initialized.")

    def listen_for_commands(self):
        logger.info("Listening for AI commands on Redis stream 'ai:commands'...")
        while True:
            try:
                # XREADGROUP BLOCK indefinitely, waiting for new messages
                # Using a consumer group to allow multiple consumers if needed
                response = self.redis_client.xreadgroup(
                    groupname="ai_group",
                    consumername="ai_consumer",
                    streams={"ai:commands": ">"},
                    count=1,
                    block=0,  # Block indefinitely
                )

                if response:
                    for stream, messages in response:
                        for message_id, message_data in messages:
                            command_str = message_data.get("command")
                            command_id = message_data.get("id")
                            logger.info(
                                f"Received command: {command_str} (ID: {command_id})"
                            )

                            result = {}
                            try:
                                # Parse command and execute corresponding function
                                parsed_command = json.loads(command_str)
                                func_name = parsed_command.get("function")
                                func_args = parsed_command.get("args", [])

                                if hasattr(self.demo, func_name):
                                    func = getattr(self.demo, func_name)
                                    # Dynamically call the function with its arguments
                                    if func_name == "classify_with_free_ai":
                                        ai_result = func(*func_args)
                                    else:
                                        ai_result = func()
                                    result = {"status": "success", "data": ai_result}
                                else:
                                    result = {
                                        "status": "error",
                                        "message": f"Unknown function: {func_name}",
                                    }
                            except Exception as e:
                                logger.error(f"Error processing command: {e}")
                                result = {"status": "error", "message": str(e)}

                            # Publish result to a response stream
                            self.redis_client.xadd(
                                "ai:results",
                                {
                                    "command_id": command_id,
                                    "result": json.dumps(result),
                                },
                            )
                            logger.info(f"Published result for command ID {command_id}")

                            # Acknowledge message processing
                            self.redis_client.xack(
                                "ai:commands", "ai_group", message_id
                            )

            except redis.exceptions.ConnectionError as e:
                logger.error(
                    f"Redis connection lost: {e}. Reconnecting in 5 seconds..."
                )
                time.sleep(5)
                self.redis_client = redis.Redis(
                    host=self.redis_host, port=self.redis_port, decode_responses=True
                )
                # Recreate consumer group on reconnect
                try:
                    self.redis_client.xgroup_create(
                        "ai:commands", "ai_group", id="0", mkstream=True
                    )
                except redis.exceptions.DataError:
                    logger.warning("Consumer group 'ai_group' already exists.")
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
                time.sleep(1)

    def setup_consumer_group(self):
        try:
            self.redis_client.xgroup_create(
                "ai:commands", "ai_group", id="0", mkstream=True
            )
            logger.info("Consumer group 'ai_group' created for stream 'ai:commands'.")
        except redis.exceptions.DataError:
            logger.info("Consumer group 'ai_group' already exists.")
        except Exception as e:
            logger.error(f"Error setting up consumer group: {e}")


if __name__ == "__main__":
    service = RedisAIService()
    service.setup_consumer_group()
    service.listen_for_commands()
