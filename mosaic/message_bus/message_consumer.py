import json
from typing import Callable, Dict, List
from xmlrpc.client import boolean
from pydantic import BaseModel, Field
from kafka import KafkaConsumer
import msgpack


class MessageConsumer(BaseModel):

    message_server_config: Dict = Field(None)
    topics: List[str] = Field(None)
    callback: Callable = Field(None)
    consumer_name: str = Field(None)
    bynary_encoded: boolean = False

    def __init__(self, message_server_config: Dict, consumer_name: str, topics: List[str],
                 callback: Callable, bynary_encoded: boolean = False):
        super().__init__()
        self.message_server_config = message_server_config
        self.topics = topics
        self.callback = callback
        self.consumer_name = consumer_name

    def start_listening(self):
        # auto_offset_reset='earliest' allow th indicator to re-read all messages !
        consumer = KafkaConsumer(*self.topics, group_id=self.consumer_name,
                                 bootstrap_servers=self.message_server_config["host"],
                                 value_deserializer=self.get_value_serializer(),
                                 auto_offset_reset='earliest')
        for message in consumer:
            self.callback(message.value)

    def get_value_serializer(self):
        return lambda m: m.decode('utf-8')
