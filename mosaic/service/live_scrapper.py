
import logging
from ..database import DbClient
from ..exchange import Exchange
from pydantic import BaseModel, Field


class LiveScrapper(BaseModel):

    exchange: Exchange
    dbclient: DbClient
    collection: str

    def callback(self, messages):
        logging.debug("LiveScrapper write messages :")
        logging.debug(messages)
        self.dbclient.write(messages, collection=self.collection)

    def start(self):
        self.exchange.download_live(callback=self.callback, line_protocol=True)
