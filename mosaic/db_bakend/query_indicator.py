
from typing import Any, Dict

from influxdb_client import InfluxDBClient
from mosaic.config.mosaic_config import MosaicConfig
from mosaic.config.server_config import DbServerConfig
from pandas import DataFrame
from pydantic import BaseModel, Field


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

    def queryAsDataFrame(self, query):
        df: DataFrame = self.query_api.query_data_frame(query=query)
        df = df.rename(
            columns={"_time": "time"})
        df = df.drop(columns=["result", "table", "_measurement"])
        return df
