from typing import Any, Dict
from mosaic.config.mosaic_config import MosaicConfig
from mosaic.config.server_config import DbServerConfig
from pydantic import BaseModel, Field
from influxdb_client import InfluxDBClient, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS, PointSettings


class InfluxIndicatorWriter(BaseModel):

    bucket: str = Field(None)
    influx_client: Any = Field(None)
    write_api: Any = Field(None)

    def __init__(self, fixtags={}):
        super().__init__()
        db_config: DbServerConfig = MosaicConfig().settings.server.db

        write_options = WriteOptions(batch_size=500,
                                     flush_interval=10_000,
                                     jitter_interval=2_000,
                                     retry_interval=5_000,
                                     max_retries=5,
                                     max_retry_delay=30_000,
                                     exponential_base=2,
                                     write_type=SYNCHRONOUS)

        self.influx_client = InfluxDBClient(
            url=db_config.url, token=db_config.token, org=db_config.org, debug=False)
        self.write_api = self.influx_client.write_api(
            write_options=write_options, point_settings=PointSettings(**fixtags))
        self.bucket = db_config.bucket

    def write(self, message):
        self.write_api.write(record=message, bucket=self.bucket)

    def write_df(self, dataframe, data_frame_measurement_name):

        self.write_api.write(record=dataframe, bucket=self.bucket,
                             data_frame_measurement_name=data_frame_measurement_name)
