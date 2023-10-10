

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
    write_error_topic: str = Field("data-write-error")

    def new_message(self, message):
        logging.debug(f'receive message to write :\n{message.value}')
        logging.debug(f'headers:\n{message.headers}')
        collection = message.headers[0][1].decode("utf8")
        measure = message.value.partition(',')[0]
        try:
            self.db_client.write(message=message.value, collection=collection)
            self.message_producer.send_message(
                message.value, topic=measure, key=message.key)
        except Exception as exc:
            logging.error(f'Error when writing message \n{message} \n{exc}')
            # send message to data-write-erro topic
            self.message_producer.send_message(
                message.value, topic=self.write_error_topic, key=message.key, headers=message.headers)

    def start(self):
        self.message_consumer.listen(
            self.new_message, topics=[self.write_topic])
