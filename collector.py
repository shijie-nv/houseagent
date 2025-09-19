import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import structlog
import time


from houseagent.message_batcher import MessageBatcher


# Load configuration from .env file
load_dotenv()


logger = structlog.get_logger(__name__)


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("Connected to MQTT broker")
        # Correctly read INPUT_TOPIC from the .env file
        topic = os.getenv('INPUT_TOPIC')
        if topic:
            client.subscribe(topic)
            logger.info(f"Subscribed to input topic: {topic}")
        else:
            logger.error(
                "INPUT_TOPIC not found in .env file. Please check your configuration."
            )
            client.disconnect()
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")


def on_message(client, userdata, msg):
    logger.info(f"Received raw message on topic '{msg.topic}'")
    message_batcher.on_message(client, userdata, msg)


def on_disconnect(client, userdata, *args):
    logger.info(f"Disconnected from MQTT broker with args: {args}")
    if args and args[0] != 0:
        logger.error(f"Unexpected disconnection. Reason code: {args[0]}")


# Use the modern V2 API, which matches agent.py
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "collector")
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect


broker_address = os.getenv('MQTT_BROKER_ADDRESS', 'localhost')
port_number = int(os.getenv('MQTT_PORT', 1883))
keep_alive_interval = int(os.getenv('MQTT_KEEP_ALIVE_INTERVAL', 60))


try:
    client.connect(broker_address, port_number, keep_alive_interval)
    logger.debug(f"Connecting to MQTT broker at {broker_address}:{port_number}")
except Exception as e:
    logger.error(f"Failed to connect to MQTT broker: {e}")
    exit(1)


# The interval is now read from .env for the batcher
bundle_interval = int(os.getenv('BUNDLE_INTERVAL', 30))
message_batcher = MessageBatcher(client, bundle_interval)


client.loop_start()


try:
    logger.info("Starting message collector...")
    message_batcher.run()
except KeyboardInterrupt:
    logger.info("Shutting down collector...")
    message_batcher.stop()


client.loop_stop()
client.disconnect()


logger.info("Collector shut down successfully.")
