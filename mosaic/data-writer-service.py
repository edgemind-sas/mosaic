import os
import sys
import yaml
import json
import logging
from mosaic.message_bus import MessageConsumer, MessageProducer
from mosaic.db_bakend import InfluxIndicatorWriter
from mosaic.indicator import IndicatorMessage

logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO)


app_config = {}
app_config["server_config_filename"] = os.path.join(os.path.dirname(__file__),
                                                    "server-config.yaml")

# -------------------------------------
# Loading configuration
# -------------------------------------
with open(app_config["server_config_filename"], 'r', encoding="utf-8") as yaml_file:
    try:
        server_config = yaml.load(yaml_file,
                                  Loader=yaml.FullLoader)
        app_config.update(server_config)
    except yaml.YAMLError as exc:
        logging.error(exc)

logging.info(app_config)

message_server_config = app_config["message_server_config"]
db_server_config = app_config["db_server_config"]

producer = MessageProducer(message_server_config, None)
datawritter = InfluxIndicatorWriter(db_server_config)


def data_write_new_message(indic_message):

    logging.debug(f'receive message to write : {indic_message}')
    datawritter.write(indic_message)
    measure = indic_message.partition(',')[0]
    producer.send_message(
        indic_message, topic=measure)


if __name__ == '__main__':

    consumer = MessageConsumer(
        message_server_config, "data-write-service",
        [message_server_config["write-topic"]],
        data_write_new_message)

    consumer.start_listening()
