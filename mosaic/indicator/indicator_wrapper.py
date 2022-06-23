import logging
from operator import index
from typing import Any, Dict, List
from mosaic.config.mosaic_config import MosaicConfig
from pandas import DataFrame, Timedelta, Timestamp
from pydantic import BaseModel, Field
import pandas as pd

from ..db_bakend.query_indicator import InfluxIndicatorQueryClient
from .query_builder import QueryBuilder

from .indicator_source import IndicatorSource
from ..config.indicator_config import IndicatorConfig
from pandas.tseries.frequencies import to_offset
from .tools import reindex_dataframe


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

        return self.get_sources_data_for_period(time, time)

    def get_sources_data_for_period(self, start: Timestamp, stop: Timestamp):

        sourceData: Dict[str, Any] = {}

        for source in self.sources.values():
            query = self.query_builder.build_query_for_period(
                source=source, collection=source.collection, start=start, stop=stop)
            result = self.query_client.query_as_dataframe(query=query)

            result = reindex_dataframe(result, source, start, stop)

            sourceData.update({source.name: result})

        return sourceData

    def compute_point(self, sourceData: Dict[str, DataFrame], date_time: Timestamp):
        logging.error(
            "Generic indicator type doesn't have a compute indicator implementation")
        return {}

    def compute(self, sourceData: Dict[str, DataFrame], start: Timestamp,
                stop: Timestamp):

        result: List = []
        columns = None

        for t in pd.date_range(start=start, end=stop, freq=to_offset(self.period)):

            sub_source_data: Dict[str, DataFrame] = {}
            for source in self.sources.values():
                start_time: pd.Timestamp = t - \
                    (source.period * self.get_history_bw(source))
                stop_time: pd.Timestamp = t + \
                    (source.period * self.get_history_fw(source))

                subdata = sourceData.get(source.name).loc[start_time:stop_time]

                sub_source_data.update({source.name: subdata})
            value: Dict = self.compute_point(sub_source_data, t)

            # dataframe columns name based on result dict
            if columns is None and len(value) > 0:
                columns = [*value.keys()]

            result.append([t] + [*value.values()])

        result_dataframe = DataFrame(result,
                                     columns=["time"] + columns)

        result_dataframe.set_index("time", inplace=True)
        return result_dataframe

    def get_history_bw(self, source: IndicatorSource):
        return source.get_history_bw()

    def get_history_fw(self, source: IndicatorSource):
        return source.get_history_fw()

    @classmethod
    def from_dict(basecls, config: IndicatorConfig):
        cls_sub_dict = {
            cls.__name__: cls for cls in __class__.__subclasses__()}

        logging.info(cls_sub_dict)

        clsname = config.class_name
        cls = cls_sub_dict.get(clsname)

        if cls is None:
            raise ValueError(
                f"{clsname} is not a subclass of {__class__.__name__}")

        return cls(config)