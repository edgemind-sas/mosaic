import logging
from operator import index
from typing import Any, Dict, List

from pandas import Timedelta, Timestamp
from pandas.tseries.frequencies import to_offset
from pydantic import BaseModel, Field, PrivateAttr

from ..indicator.indicator import Indicator
from ..database import InfluxDataSource
from ..database.query_builder import build_query_for_period
from ..database.df_utils import reindex_dataframe


class IndicatorWrapper(BaseModel):

    name: str = Field(...)

    description: str = Field(None)

    tags: Dict[str, str] = Field(None)

    collection: str = Field(None)

    indicator: Indicator = Field(None)

    sources: Dict[str, InfluxDataSource] = Field({})

    def __init__(self, **data):

        # instanciate manually indicator base on class_name attribute
        indicatorConfig = data.pop("indicator")
        super().__init__(**data)

        self.indicator = Indicator.from_config(**indicatorConfig)

    def get_sources_data(self,  time: Timestamp):
        return self.get_sources_data_for_period(time, time)

    def get_sources_data_for_period(self, start: Timestamp, stop: Timestamp):

        sourceData: Dict[str, Any] = {}

        for source in self.sources.values():
            query = build_query_for_period(
                source=source, collection=source.collection, start=start, stop=stop)
            result = self.query_client.query_as_dataframe(query=query)

            result = reindex_dataframe(result, source, start, stop)

            sourceData.update({source.name: result})

        return sourceData

    def get_history_bw(self, source: InfluxDataSource):
        return source.get_history_bw()

    def get_history_fw(self, source: InfluxDataSource):
        return source.get_history_fw()


'''



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
'''
