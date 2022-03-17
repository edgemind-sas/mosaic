from typing import Callable, List
from mosaic.config.mosaic_config import MosaicConfig
from pydantic import BaseModel, Field
from kafka import KafkaConsumer


class MessageConsumer(BaseModel):

    topics: List[str] = Field(None)
    callback: Callable = Field(None)
    consumer_name: str = Field(None)

    def __init__(self, consumer_name: str, topics: List[str],
                 callback: Callable):
        super().__init__()
        self.topics = topics
        self.callback = callback
        self.consumer_name = consumer_name

    def start_listening(self):

        host = MosaicConfig().settings.server.message.host
        # auto_offset_reset='earliest' allow th indicator to re-read all messages !
        consumer = KafkaConsumer(*self.topics, group_id=self.consumer_name,
                                 bootstrap_servers=host,
                                 value_deserializer=self.get_value_serializer(),
                                 auto_offset_reset='earliest')
        for message in consumer:
            self.callback(message.value)

    def get_value_serializer(self):
        return lambda m: m.decode('utf-8')
