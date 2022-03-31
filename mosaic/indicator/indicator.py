import logging
from operator import index
from typing import Any, Dict, List
from mosaic.config.mosaic_config import MosaicConfig
from pandas import DataFrame, Timedelta, Timestamp
from pydantic import BaseModel, Field
import pandas as pd

from ..db_bakend.query_indicator import InfluxIndicatorQueryClient
from .query.query_builder import QueryBuilder

from .indicator_source import IndicatorSource
from ..config.indicator_config import IndicatorConfig


class Indicator(BaseModel):

    config: IndicatorConfig = Field(None)

    sources: Dict[str, IndicatorSource] = Field({})

    query_client: InfluxIndicatorQueryClient = Field(None)

    query_builder: QueryBuilder = Field(None)

    period: Timedelta = Field(None)

    def __init__(self, indicator_config: IndicatorConfig):

        super().__init__()

        self.config = indicator_config

        # for each source in config, create a source with callback
        for name in self.config.source:
            sourceConfig = self.config.source.get(name)
            self.sources.update(
                {name: IndicatorSource(name=name, config=sourceConfig)})
            period_string = sourceConfig.tags.get("period")
            period = pd.to_timedelta(period_string)
            if self.period is None or self.period > period:
                self.period = period

        self.query_client = InfluxIndicatorQueryClient()
        self.query_builder = QueryBuilder()

    def get_sources_data(self,  time: Timestamp):

        sourceData: Dict[str, Any] = {}

        bucket_name = MosaicConfig().settings.server.db.bucket

        for source in self.sources.values():
            query = self.query_builder.build_query(
                source=source, bucket=bucket_name, time=time)
            result = self.query_client.query_as_dataframe(query=query)
            sourceData.update({source.name: result})

        return sourceData

    def get_sources_data_for_period(self, start: Timestamp, stop: Timestamp):

        sourceData: Dict[str, Any] = {}

        bucket_name = MosaicConfig().settings.server.db.bucket

        for source in self.sources.values():
            query = self.query_builder.build_query_for_period(
                source=source, bucket=bucket_name, start=start, stop=stop)
            result = self.query_client.query_as_dataframe(query=query)
            sourceData.update({source.name: result})

        return sourceData

    def compute_indicator(self, sourceData: Dict[str, Any]):
        logging.error(
            "Generic indicator type doesn't have a compute indicator implementation")
        return {}

    def compute_indicator_batch(self, sourceData: Dict[str, DataFrame], start: Timestamp, stop: Timestamp):

        sub_source_data: Dict[str, DataFrame] = {}

        steps = int((stop - start)/self.period)

        result: List = []

        columns = None

        periods = {}

        for source in self.sources.values():
            period_string = source.config.tags.get("period")
            period = pd.to_timedelta(period_string)
            periods.update({source.name: period})

        for i in range(0, steps+1):
            t = start + self.period * i
            for source in self.sources.values():
                period = periods.get(source.name)
                start_time: pd.Timestamp = t - \
                    (period * source.config.history_bw)
                stop_time: pd.Timestamp = t + \
                    (period * source.config.history_fw)

                subdata = sourceData.get(source.name).loc[start_time:stop_time]

                sub_source_data.update({source.name: subdata})
            value: Dict = self.compute_indicator(sub_source_data)
            if columns is None and len(value) > 0:
                columns = [*value.keys()]
            t = start + self.period * i

            result.append([t] + [*value.values()])

        result_dataframe = DataFrame(result,
                                     columns=["time"] + columns)

        result_dataframe.set_index("time", inplace=True)
        return result_dataframe
