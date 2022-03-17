import os
import sys
from mosaic.config.mosaic_config import MosaicConfig
import yaml
import json
import logging
from mosaic.message_bus import MessageConsumer, MessageProducer
from mosaic.db_bakend import InfluxIndicatorWriter

logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO)


# -------------------------------------
# Loading configuration
# -------------------------------------

config_filename = os.path.join(os.path.dirname(
    __file__),  "./config.yaml")

MosaicConfig().from_yaml_filename(config_filename)

producer = MessageProducer()
datawritter = InfluxIndicatorWriter()


def data_write_new_message(indic_message):

    logging.debug(f'receive message to write : {indic_message}')
    datawritter.write(indic_message)
    measure = indic_message.partition(',')[0]
    producer.send_message(
        indic_message, topic=measure)


if __name__ == '__main__':

    consumer = MessageConsumer("data-write-service", 
    [MosaicConfig().settings.server.message.write_topic],
        data_write_new_message)

    consumer.start_listening()
