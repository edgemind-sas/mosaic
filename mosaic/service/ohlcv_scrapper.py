
from mosaic.indicator.indicator_message import IndicatorMessage
from ..exchange import Exchange
from ..messaging import MessageProducer
from pydantic import BaseModel, Field


class OHLCVScrapper(BaseModel):

    exchange: Exchange = Field(...)
    message_producer: MessageProducer = Field(...)
    write_topic: str = Field("data-write")
    collection: str = Field(...)

    def callback(self, messages):
        headers = [("collection", self.collection.encode('utf-8'))]
        for message in messages:
            self.message_producer.send_message(
                message=message, topic=self.write_topic, headers=headers, key=self.get_key(message))

    def get_key(self, message):
        im = IndicatorMessage.from_line_protocol(message)
        key = f'{self.collection}.{im.measurement}'

        for tag in sorted(im.tags.keys()):
            key += f'.{tag}:{im.tags.get(tag)}'

        return key

    def start(self):
        self.exchange.download_new_ohlcv(
            callback=self.callback, line_protocol=True)
