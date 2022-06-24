from typing import Dict, List
from pydantic import BaseModel, Field
from ..indicator import Indicator
from .indicator_message import IndicatorMessage
from .message_bus.message_consumer import MessageConsumer
from .message_bus.message_producer import MessageProducer
import logging
import numpy as np
import uuid


class MbIndicatorComputeWrapper(BaseModel):

    indicators: List[Indicator] = Field(None)

    message_producer: MessageProducer = Field(None)

    def __init__(self,  indicators: List[Indicator]):
        super().__init__()
        self.indicators = indicators

        self.message_producer = MessageProducer(
            MosaicConfig().settings.server.message.write_topic)

    def start_listenning(self):
        # get all topics to listen to
        topics = []
        for indicator in self.indicators:
            for source in indicator.sources.values():
                logging.info(
                    f'Start listenning on topic {source.config.name} with tags {source.config.tags}')

                if source.config.name not in topics:
                    topics.append(source.config.name)

        unique_consumer_name = MosaicConfig().settings.server.message.consumer_id
        if unique_consumer_name is None or unique_consumer_name == "":
            unique_consumer_name = str(uuid.uuid4())

        message_consumer = MessageConsumer(
            consumer_name=unique_consumer_name, topics=topics,
            callback=self.treat_indicator_message)

        message_consumer.start_listening()

    def treat_indicator_message(self,  message, headers):
        indic_message = IndicatorMessage(message)
        logging.info(f'new message receive : ')
        logging.info(indic_message)

        for indicator in self.indicators:
            for source in indicator.sources.values():
                if source.accept(indic_message):
                    logging.info(
                        f'Source {source.name} accept the new message')

                    # if we have forward history, need to change time !

                    sources_data = indicator.get_sources_data(
                        indic_message.time - source.get_history_fw()*indicator.period)

                    value = indicator.compute(
                        sources_data, indic_message.time, indic_message.time)
                    self.save_indicator(value, indic_message, indicator)
                    continue

    def save_indicator(self, values: Dict, indic_message: IndicatorMessage, indicator):

        if len(values) == 0:
            return

        for index, row in values.dropna(how='all').iterrows():
            newIndicator = IndicatorMessage()
            newIndicator.tags = indicator.config.tags
            newIndicator.fields = row.dropna().to_dict()
            newIndicator.measurement = indicator.config.name
            newIndicator.time = index

            logging.info(f'{index} : {newIndicator.to_line_protocol()}')

            self.message_producer.send_message(newIndicator.to_line_protocol(
            ), key=newIndicator.measurement, collection=indicator.config.collection)
