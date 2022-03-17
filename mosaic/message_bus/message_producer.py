from typing import Any, Dict
from xmlrpc.client import boolean
from mosaic.config.mosaic_config import MosaicConfig
from pydantic import BaseModel, Field
from kafka import KafkaProducer


class MessageProducer(BaseModel):

    producer: Any = Field(None)
    topic: str = Field(None)
    bynary_encoded: boolean = False

    def __init__(self, topic: str = None):
        super().__init__()
        self.topic = topic

        host = MosaicConfig().settings.server.message.host
        
        self.producer = KafkaProducer(
            bootstrap_servers=host)

    def send_message(self, message, topic=None, key=None):
        if topic is None:
            topic = self.topic
        if key is None:
            key = message.partition(",")[0]  # give measurement as key
        self.producer.send(topic, value=message.encode(
            'utf-8'), key=key.encode('utf-8'))
