from typing import Any, Dict, Union

from influxdb_client import InfluxDBClient, WriteOptions
from influxdb_client.client.write_api import PointSettings, WriteType, SYNCHRONOUS
from .datasource import InfluxDataSource
from .query_builder import build_query_for_period
from pandas import DataFrame, Timestamp
import pandas as pd
from pydantic import BaseModel, Field
from .df_utils import reindex_dataframe
import logging


class DbClient(BaseModel):

    org: str = Field(None)
    url: str = Field(None)
    token: str = Field(None)
    fixtags: Dict = Field({})

    influx_client: Any = Field(None)

    query_api: Any = Field(None)
    delete_api: Any = Field(None)
    write_api: Any = Field(None)

    def __init__(self,  **data):
        super().__init__(**data)

        self.influx_client = InfluxDBClient(
            url=self.url, token=self.token,
            org=self.org, debug=False, enable_gzip=False)

        self.write_api = self.influx_client.write_api(
            write_options=SYNCHRONOUS, point_settings=PointSettings(**self.fixtags))
        self.query_api = self.influx_client.query_api()
        self.delete_api = self.influx_client.delete_api()

    def query_with_flux(self, query):
        df: DataFrame = self.query_api.query_data_frame(query=query)

        if not df.empty:
            df = df.rename(columns={"_time": "time"})
            df = df.drop(columns=["result", "table", "_measurement"])
            df.set_index("time", inplace=True)
        logging.debug(f'{df}')
        return df

    def parse_date(self, date: Union[Timestamp, str]):

        if isinstance(date, str):
            return pd.to_datetime(
                date, utc=True, unit='ns')
        elif isinstance(date, Timestamp):
            return pd.to_datetime(
                date, utc=True, unit='ns')

    def get_data(self, source: InfluxDataSource,
                 start: Union[Timestamp, str],
                 stop: Union[Timestamp, str] = None,
                 fill_with_NaN=True):

        # if stop is not set, consider one point data @ start
        if stop is None:
            stop = start

        start_date_ts = self.parse_date(start)
        stop_date_ts = self.parse_date(stop)

        flux_query = build_query_for_period(
            source, start_date_ts, stop_date_ts)
        df = self.query_with_flux(flux_query)

        # reorder columns base on source definition if values is set
        if source.values is not None:
            df = df.reindex(source.values, axis="columns")

        if fill_with_NaN:
            df = reindex_dataframe(
                df, start_date_ts,  stop_date_ts, source.period)
          
            # check if there is some NaN
            count = len(df[df.isnull().any(axis='columns')])
            logging.warning(f'There is {count} missing data in source {source.get_str_info()}')

        return df

    def write(self, message, collection):
        self.write_api.write(record=message, bucket=collection)

    def write_df(self, dataframe: DataFrame, datasource: InfluxDataSource):

        self.write_api._point_settings = PointSettings(
            **datasource.tags)

        self.write_api.write(record=dataframe, bucket=datasource.collection,
                             data_frame_measurement_name=datasource.name)

    def delete_indicator(self, datasource: InfluxDataSource, start="2010-01-01T00:00:00Z",
                         stop="2023-01-01T00:00:00Z", with_tags=True):

        logging.info(
            f'Deleting indicator {datasource.name} from collection {datasource.collection}')

        predicate = f'_measurement="{datasource.name}"'

        if with_tags:
            for idx, tag in enumerate(datasource.tags.keys()):
                predicate += f' AND {tag}="{datasource.tags.get(tag)}"'
            logging.info(predicate)

        self.delete_api.delete(
            start, stop, predicate, bucket=datasource.collection,
            org=self.org)

    def close(self):
        self.write_api.close()
        self.query_api.close()
        self.delete_api.close()
        self.influx_client.close()
