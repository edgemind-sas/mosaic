
from typing import Any, Dict

from influxdb_client import InfluxDBClient
from mosaic.config.mosaic_config import MosaicConfig
from mosaic.config.server_config import DbServerConfig
from pandas import DataFrame
from pydantic import BaseModel, Field
import logging


class InfluxIndicatorDeleteClient(BaseModel):

    influx_client: Any = Field(None)
    delete_api: Any = Field(None)

    def __init__(self):
        super().__init__()

        db_config: DbServerConfig = MosaicConfig().settings.server.db

        self.influx_client = InfluxDBClient(
            url=db_config.url, token=db_config.token,
            org=db_config.org, debug=False, enable_gzip=True, timeout=10000000)
        self.delete_api = self.influx_client.delete_api()

    def delete_indicator(self, collection, indicator_name, start="2010-01-01T00:00:00Z", stop="2023-01-01T00:00:00Z"):

        logging.info(
            f'Deleting indicator {indicator_name} from collection {collection}')

        org = MosaicConfig().settings.server.db.org

        self.delete_api.delete(
            start, stop, f'_measurement="{indicator_name}"', bucket=collection, org=org)


def delete_indicator(collection, indicator_name):

    client = InfluxIndicatorDeleteClient()
    client.delete_indicator(collection, indicator_name)
