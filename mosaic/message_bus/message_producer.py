from typing import Any, Dict
from xmlrpc.client import boolean
from pydantic import BaseModel, Field
from kafka import KafkaProducer


class MessageProducer(BaseModel):

    message_server_config: Dict = Field(None)
    producer: Any = Field(None)
    topic: str = Field(None)
    bynary_encoded: boolean = False

    def __init__(self, message_server_config: Dict, topic: str):
        super().__init__()
        self.topic = topic
        self.message_server_config = message_server_config
        self.producer = KafkaProducer(
            bootstrap_servers=self.message_server_config["host"])

    def send_message(self, message, topic=None, key=None):
        if topic is None:
            topic = self.topic
        if key is None:
            key = message.partition(",")[0]  # give measurement as key
        self.producer.send(topic, value=message.encode(
            'utf-8'), key=key.encode('utf-8'))
