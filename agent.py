import os
import json
import paho.mqtt.client as mqtt
import logging
from dotenv import load_dotenv
import time
import structlog


from houseagent.agent_listener import AgentListener


load_dotenv()
logger = structlog.get_logger(__name__)


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("Connected to MQTT broker")
        # Correctly read MESSAGE_BUNDLE_TOPIC from the .env file
        topic = os.getenv('MESSAGE_BUNDLE_TOPIC')
        if topic:
            client.subscribe(topic)
            logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(
                "MESSAGE_BUNDLE_TOPIC not found in .env file. Please check your configuration."
            )
            client.disconnect()
    else:
        logger.error(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    logger.info("Received message bundle")
    agent_client.on_message(client, userdata, msg)


def on_disconnect(client, userdata, *args):
    logger.info(f"Disconnected from MQTT broker with args: {args}")
    if args and args[0] != 0:
        logger.error(f"Unexpected disconnection. Reason code: {args[0]}")


# Use the modern V2 API
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "agent")
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect


broker_address = os.getenv('MQTT_BROKER_ADDRESS', 'localhost')
port_number = int(os.getenv('MQTT_PORT', 1883))
keep_alive_interval = int(os.getenv('MQTT_KEEP_ALIVE_INTERVAL', 60))


try:
    client.connect(broker_address, port_number, keep_alive_interval)
except Exception as e:
    logger.error(f"Failed to connect to MQTT broker: {e}")
    exit(1)


agent_client = AgentListener(client)
client.loop_start()


try:
    while not agent_client.stopped:
        time.sleep(1)
except KeyboardInterrupt:
    logging.info("Shutting down agent...")
    agent_client.stop()


client.loop_stop()
client.disconnect()
logger.info("Agent shut down successfully.")
