
import logging
from typing import Any, List, Literal
from pydantic import BaseModel, Field
from kafka import KafkaConsumer, KafkaProducer


class MessageBase(BaseModel):

    host: str = Field(...)


class MessageConsumer(MessageBase):

    consumer_group_id: str = Field(...)
    topics: List[str] = Field([])
    auto_offset_reset: Literal["earliest", "latest"] = Field("earliest")

    def listen(self, callback, topics=None):

        if topics is None:
            topics = self.topics

        consumer = KafkaConsumer(*topics, group_id=self.consumer_group_id,
                                 bootstrap_servers=self.host,
                                 value_deserializer=(
                                     lambda m: m.decode('utf-8')),
                                 auto_offset_reset=self.auto_offset_reset)
        for message in consumer:
            callback(message)


class MessageProducer(MessageBase):

    topic: str = Field(None)
    producer: Any = None

    def _get_producer(self):
        if self.producer is None:
            self.producer = KafkaProducer(bootstrap_servers=self.host)
        return self.producer

    def send_message(self, message, topic=None, key=None, headers={}):

        if topic is None:
            topic = self.topic
        if key is not None and isinstance(key, str):
            key = key.encode('utf-8')

        headers_as_tuples = []

        if isinstance(headers, dict):
            for k, v in headers.items():
                headers_as_tuples.append((k, str.encode(v)))
        elif isinstance(headers, list):
            headers_as_tuples = headers

        self._get_producer().send(topic, value=message.encode(
            'utf-8'), key=key, headers=headers_as_tuples)

    def flush(self):
        self._get_producer().flush()
