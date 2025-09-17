# MDSAPP/core/managers/pubsub_manager.py

import logging
import os
import json
import asyncio
from typing import Dict, Any

from google.cloud import pubsub_v1
from google.api_core import exceptions
from google.api_core.client_options import ClientOptions

logger = logging.getLogger(__name__)

class PubSubManager:
    """
    Manages publishing and subscribing to Google Cloud Pub/Sub.
    """
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            logger.warning("GOOGLE_CLOUD_PROJECT environment variable not set. Pub/Sub will be disabled.")
            self.publisher = None
            self.subscriber = None
        else:
            try:
                client_options = ClientOptions(api_endpoint="pubsub.googleapis.com:443")
                self.publisher = pubsub_v1.PublisherClient(client_options=client_options)
                self.subscriber = pubsub_v1.SubscriberClient(client_options=client_options)
                logger.info("PubSubManager initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Pub/Sub clients: {e}", exc_info=True)
                self.publisher = None
                self.subscriber = None

    async def publish_message(self, topic_id: str, message_data: Dict[str, Any]):
        """
        Publishes a message to a Pub/Sub topic.
        """
        if not self.publisher:
            logger.debug(f"Pub/Sub is disabled. Skipping message publication to topic '{topic_id}'.")
            return

        topic_path = self.publisher.topic_path(self.project_id, topic_id)

        try:
            # Ensure the topic exists, creating it if necessary.
            try:
                await asyncio.to_thread(self.publisher.get_topic, topic=topic_path)
            except exceptions.NotFound:
                logger.info(f"Topic '{topic_path}' not found, creating it...")
                await asyncio.to_thread(self.publisher.create_topic, name=topic_path)

            message_json = json.dumps(message_data, default=str)
            message_bytes = message_json.encode("utf-8")
            
            logger.debug(f"Attempting to publish to topic '{topic_id}'. Payload: {message_json}")

            future = self.publisher.publish(topic_path, message_bytes)
            message_id = await asyncio.to_thread(future.result)
            
            logger.info(f"Successfully published message {message_id} to topic {topic_id}.")
        except Exception as e:
            logger.error(f"CRITICAL: Failed to publish message to topic {topic_id}. Error: {e}", exc_info=True)

    async def subscribe_to_topic(self, topic_id: str) -> str | None:
        """
        Creates a new subscription to a topic, creating the topic if it doesn't exist.
        """
        if not self.subscriber or not self.publisher:
            logger.warning("Pub/Sub clients not initialized. Cannot subscribe.")
            return None

        topic_path = self.publisher.topic_path(self.project_id, topic_id)
        subscription_id = f"{topic_id}-sub-{os.urandom(4).hex()}"
        subscription_path = self.subscriber.subscription_path(self.project_id, subscription_id)

        try:
            # 1. Ensure the topic exists, create it if not.
            try:
                await asyncio.to_thread(self.publisher.get_topic, topic=topic_path)
                logger.info(f"Topic {topic_path} already exists.")
            except exceptions.NotFound:
                logger.info(f"Topic {topic_path} not found, creating it...")
                await asyncio.to_thread(self.publisher.create_topic, name=topic_path)
                logger.info(f"Topic {topic_path} created.")

            # 2. Create the subscription.
            await asyncio.to_thread(
                self.subscriber.create_subscription,
                name=subscription_path, 
                topic=topic_path
            )
            logger.info(f"Created subscription: {subscription_path}")
            return subscription_path
        except exceptions.AlreadyExists:
            logger.info(f"Subscription already exists: {subscription_path}. This is unexpected but safe.")
            return subscription_path
        except Exception as e:
            logger.error(f"Failed to create subscription for topic {topic_id}: {e}", exc_info=True)
            return None

    async def pull_message(self, subscription_path: str):
        """
        Pulls a single message from a subscription in a non-blocking manner.
        """
        if not self.subscriber:
            return None

        try:
            # Run the blocking pull method in a separate thread
            response = await asyncio.to_thread(
                self.subscriber.pull,
                subscription=subscription_path,
                max_messages=1,
                return_immediately=True,  # To avoid long waits
            )
            if response.received_messages:
                # The message object itself is what we need
                return response.received_messages[0]
            return None
        except Exception as e:
            logger.error(f"Failed to pull message from subscription {subscription_path}: {e}", exc_info=True)
            return None

    async def ack_message(self, subscription_path: str, ack_id: str):
        """Acknowledges a message that has been received."""
        if not self.subscriber:
            return
        try:
            await asyncio.to_thread(self.subscriber.acknowledge, subscription=subscription_path, ack_ids=[ack_id])
        except Exception as e:
            logger.error(f"Failed to acknowledge message ID {ack_id} for subscription {subscription_path}: {e}", exc_info=True)

    async def delete_subscription(self, subscription_path: str):
        """
        Deletes a subscription in a non-blocking manner.
        """
        if not self.subscriber:
            return

        try:
            # Run the blocking delete_subscription method in a separate thread
            await asyncio.to_thread(
                self.subscriber.delete_subscription, 
                subscription=subscription_path
            )
            logger.info(f"Deleted subscription: {subscription_path}")
        except Exception as e:
            logger.error(f"Failed to delete subscription {subscription_path}: {e}", exc_info=True)

    async def create_named_subscription(self, topic_id: str, subscription_id: str):
        """Creates a subscription with a specific name to a topic."""
        if not self.subscriber or not self.publisher:
            logger.warning("Pub/Sub clients not initialized. Cannot create subscription.")
            return None

        topic_path = self.publisher.topic_path(self.project_id, topic_id)
        subscription_path = self.subscriber.subscription_path(self.project_id, subscription_id)

        try:
            await asyncio.to_thread(
                self.subscriber.create_subscription,
                name=subscription_path, 
                topic=topic_path
            )
            logger.info(f"Created subscription: {subscription_path}")
            return subscription_path
        except exceptions.AlreadyExists:
            logger.info(f"Subscription {subscription_path} already exists.")
            return subscription_path
        except Exception as e:
            logger.error(f"Failed to create subscription {subscription_path}: {e}", exc_info=True)
            return None
