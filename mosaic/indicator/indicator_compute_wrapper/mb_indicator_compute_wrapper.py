from typing import Dict
from pydantic import BaseModel, Field
from ..indicator import Indicator
from ..indicator_message import IndicatorMessage
from ...message_bus import MessageConsumer
from ...message_bus import MessageProducer
import logging


class MbIndicatorComputeWrapper(BaseModel):

    indicator: Indicator = Field(None)
    servers_config: Dict = Field(None)

    message_producer: MessageProducer = Field(None)

    def __init__(self,  indicator: Indicator, servers_config: Dict):
        super().__init__()
        self.indicator = indicator
        self.servers_config = servers_config

        self.message_producer = MessageProducer(
            self.servers_config["message_server_config"],
            self.servers_config["message_server_config"]["write-topic"])

    def start_listenning(self):
        # get all topics to listen to
        topics = []
        for source in self.indicator.sources.values():
            logging.info(
                f'Start listenning on topic {source.config.id} with tags {source.config.tags}')

            if source.config.id not in topics:
                topics.append(source.config.id)

        message_consumer = MessageConsumer(
            message_server_config=self.servers_config["message_server_config"],
            consumer_name=self.indicator.config.name, topics=topics,
            callback=self.treat_indicator_message)

        message_consumer.start_listening()

    def treat_indicator_message(self,  message):
        indic_message = IndicatorMessage(message)
        logging.info(f'new message receive : ')
        logging.info(indic_message)
        for source in self.indicator.sources.values():
            if source.accept(indic_message):
                logging.info(f'Source {source.name} accept the new message')

                # if we have forward history, need to change time !

                sources_data = self.indicator.get_sources_data(
                    indic_message.time)
                value = self.indicator.compute_indicator(sources_data)
                self.save_indicator(value, indic_message)
                break

    def save_indicator(self, value: Dict, indic_message: IndicatorMessage):

        logging.info(f'save indicator with value {value}')
        if len(value) == 0:
            return

        logging.info("save indicator")
        newIndicator = IndicatorMessage()

        newIndicator.tags = self.indicator.config.tags
        newIndicator.fields = value
        newIndicator.measurement = self.indicator.config.name
        newIndicator.time = indic_message.time

        self.message_producer.send_message(
            newIndicator.to_line_protocol(), key=newIndicator.measurement)
