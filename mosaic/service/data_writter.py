

from ..database import DbClient
from ..messaging import MessageProducer
from ..messaging import MessageConsumer
from pydantic import BaseModel, Field
import logging


class DataWritter(BaseModel):

    db_client: DbClient = Field(...)
    message_producer: MessageProducer = Field(...)
    message_consumer: MessageConsumer = Field(...)
    write_topic: str = Field("data-write")

    def new_message(self, message):
        logging.info(f'receive message to write : {message.value}')
        logging.info(f'{message.headers}')
        collection = message.headers[0][1].decode("utf8")
        measure = message.value.partition(',')[0]
        self.db_client.write(message=message.value, collection=collection)
        self.message_producer.send_message(
            message.value, topic=measure, key=message.key)

    def start(self):
        self.message_consumer.listen(self.new_message)
