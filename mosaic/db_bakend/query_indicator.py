
from typing import Any, Dict

from influxdb_client import InfluxDBClient
from mosaic.config.mosaic_config import MosaicConfig
from mosaic.config.server_config import DbServerConfig
from pandas import DataFrame, DatetimeIndex
from pydantic import BaseModel, Field
import logging


class InfluxIndicatorQueryClient(BaseModel):

    influx_client: Any = Field(None)
    query_api: Any = Field(None)

    def __init__(self):
        super().__init__()

        db_config: DbServerConfig = MosaicConfig().settings.server.db

        self.influx_client = InfluxDBClient(
            url=db_config.url, token=db_config.token,
            org=db_config.org, debug=False)
        self.query_api = self.influx_client.query_api()

    def query_as_dataframe(self, query):
        df: DataFrame = self.query_api.query_data_frame(query=query)

        if not df.empty:
            df = df.rename(columns={"_time": "time"})
            df = df.drop(columns=["result", "table", "_measurement"])
            df.set_index("time", inplace=True)

        logging.debug(f'{df}')
        return df
