

import logging
from ..exchange import Exchange
from pydantic import BaseModel, Field


class OHLCVScrapper(BaseModel):

    exchange: Exchange
    collection: str

    def callback(self, messages):
        logging.info(messages)

    def start(self):
        self.exchange.download_new_ohlcv(
            callback=self.callback, line_protocol=True)
