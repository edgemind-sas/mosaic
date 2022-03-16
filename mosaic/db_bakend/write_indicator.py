from typing import Any, Dict
from pydantic import BaseModel, Field
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS


class InfluxIndicatorWriter(BaseModel):

    config: Dict = Field(None)
    bucket: str = Field(None)
    influx_client: Any = Field(None)
    write_api: Any = Field(None)

    def __init__(self, db_config: Dict):
        super().__init__()
        self.config = db_config
        self.influx_client = InfluxDBClient(
            url=db_config["url"], token=db_config["token"], org=db_config["org"], debug=False)
        self.write_api = self.influx_client.write_api(
            write_options=SYNCHRONOUS)
        self.bucket = db_config["bucket"]

    def write(self, message):
        self.write_api.write(record=message, bucket=self.bucket)
