
from typing import Any, Dict

from influxdb_client import InfluxDBClient
from pandas import DataFrame
from pydantic import BaseModel, Field


class InfluxIndicatorQueryClient(BaseModel):

    config: Dict = Field(None)
    influx_client: Any = Field(None)
    query_api: Any = Field(None)

    def __init__(self, db_config: Dict):
        super().__init__()
        self.config = db_config
        self.influx_client = InfluxDBClient(
            url=db_config["url"], token=db_config["token"],
            org=db_config["org"], debug=False)
        self.query_api = self.influx_client.query_api()

    def queryAsDataFrame(self, query):
        df: DataFrame = self.query_api.query_data_frame(query=query)
        df = df.rename(
            columns={"_time": "time"})
        df = df.drop(columns=["result", "table", "_measurement"])
        return df
