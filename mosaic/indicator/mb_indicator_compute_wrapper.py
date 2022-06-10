from typing import Dict
from mosaic.config.mosaic_config import MosaicConfig
from pydantic import BaseModel, Field
from ..indicator import Indicator
from .indicator_message import IndicatorMessage
from ..message_bus import MessageConsumer
from ..message_bus import MessageProducer
import logging
import numpy as np


class MbIndicatorComputeWrapper(BaseModel):

    indicator: Indicator = Field(None)

    message_producer: MessageProducer = Field(None)

    def __init__(self,  indicator: Indicator):
        super().__init__()
        self.indicator = indicator

        self.message_producer = MessageProducer(
            MosaicConfig().settings.server.message.write_topic)

    def start_listenning(self):
        # get all topics to listen to
        topics = []
        for source in self.indicator.sources.values():
            logging.info(
                f'Start listenning on topic {source.config.name} with tags {source.config.tags}')

            if source.config.name not in topics:
                topics.append(source.config.name)

        message_consumer = MessageConsumer(
            consumer_name=self.indicator.config.name, topics=topics,
            callback=self.treat_indicator_message)

        message_consumer.start_listening()

    def treat_indicator_message(self,  message, headers):
        indic_message = IndicatorMessage(message)
        logging.info(f'new message receive : ')
        logging.info(indic_message)
        for source in self.indicator.sources.values():
            if source.accept(indic_message):
                logging.info(f'Source {source.name} accept the new message')

                # if we have forward history, need to change time !

                sources_data = self.indicator.get_sources_data(
                    indic_message.time - source.get_history_fw()*self.indicator.period)

                value = self.indicator.compute(
                    sources_data, indic_message.time, indic_message.time)
                self.save_indicator(value, indic_message)
                break

    def save_indicator(self, values: Dict, indic_message: IndicatorMessage):

        if len(values) == 0:
            return

        for index, row in values.dropna(how='all').iterrows():
            newIndicator = IndicatorMessage()
            newIndicator.tags = self.indicator.config.tags
            newIndicator.fields = row.dropna().to_dict()
            newIndicator.measurement = self.indicator.config.name
            newIndicator.time = index

            logging.info(f'{index} : {newIndicator.to_line_protocol()}')

            self.message_producer.send_message(newIndicator.to_line_protocol(
            ), key=newIndicator.measurement, collection=self.indicator.config.collection)
