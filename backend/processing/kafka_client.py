"""Kafka client for producing and consuming messages."""

from typing import Optional, AsyncIterator, Dict, Any
import json
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError

from backend.common.config import settings
from backend.common.logging import get_logger

logger = get_logger(__name__)


class KafkaClient:
    """Kafka client wrapper."""
    
    def __init__(self):
        """Initialize Kafka client."""
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
    
    async def start_producer(self) -> None:
        """Start Kafka producer."""
        if self.producer is None:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
            )
            await self.producer.start()
            logger.info("Kafka producer started")
    
    async def stop_producer(self) -> None:
        """Stop Kafka producer."""
        if self.producer:
            await self.producer.stop()
            self.producer = None
            logger.info("Kafka producer stopped")
    
    async def send_message(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None
    ) -> None:
        """
        Send message to Kafka topic.
        
        Args:
            topic: Topic name
            value: Message value (dict)
            key: Optional message key
        """
        if self.producer is None:
            await self.start_producer()
        
        try:
            await self.producer.send_and_wait(topic, value=value, key=key)
            logger.debug(f"Message sent to topic {topic}")
        except KafkaError as e:
            logger.error(f"Error sending message to Kafka: {e}")
            raise
    
    async def create_consumer(
        self,
        topic: str,
        group_id: str,
        auto_offset_reset: str = "latest"
    ) -> AIOKafkaConsumer:
        """
        Create Kafka consumer.
        
        Args:
            topic: Topic name
            group_id: Consumer group ID
            auto_offset_reset: Offset reset policy
        
        Returns:
            Kafka consumer
        """
        if topic in self.consumers:
            return self.consumers[topic]
        
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
        )
        
        await consumer.start()
        self.consumers[topic] = consumer
        logger.info(f"Kafka consumer started for topic {topic}, group {group_id}")
        
        return consumer
    
    async def stop_consumer(self, topic: str) -> None:
        """Stop Kafka consumer."""
        if topic in self.consumers:
            await self.consumers[topic].stop()
            del self.consumers[topic]
            logger.info(f"Kafka consumer stopped for topic {topic}")
    
    async def stop_all_consumers(self) -> None:
        """Stop all Kafka consumers."""
        for topic in list(self.consumers.keys()):
            await self.stop_consumer(topic)


# Global Kafka client instance
kafka_client = KafkaClient()
