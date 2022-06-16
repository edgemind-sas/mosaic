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

    @classmethod
    def from_dict(basecls, **config):
        cls_sub_dict = {
            cls.__name__: cls for cls in __class__.__subclasses__()}

        logging.info(cls_sub_dict)

        clsname = config.pop("class_name")
        cls = cls_sub_dict.get(clsname)

        if cls is None:
            raise ValueError(
                f"{clsname} is not a subclass of {__class__.__name__}")

        return cls(**config)

    def compute_point(self, date_time: Timestamp, *data):
        logging.error(
            "Generic indicator type doesn't have a compute indicator implementation")
        return {}

    def compute(self, *data):

        logging.error(
            "Generic indicator type doesn't have a compute indicator implementation")
        return {}

        # result: List = []
        # columns = None

        # for t in pd.date_range(start=start, end=stop, freq=to_offset(self.period)):

        #     sub_source_data: Dict[str, DataFrame] = {}
        #     for source in self.sources.values():
        #         start_time: pd.Timestamp = t - \
        #             (source.period * self.get_history_bw(source))
        #         stop_time: pd.Timestamp = t + \
        #             (source.period * self.get_history_fw(source))

        #         subdata = sourceData.get(source.name).loc[start_time:stop_time]

        #         sub_source_data.update({source.name: subdata})
        #     value: Dict = self.compute_point(sub_source_data, t)

        #     # dataframe columns name based on result dict
        #     if columns is None and len(value) > 0:
        #         columns = [*value.keys()]

        #     result.append([t] + [*value.values()])

        # result_dataframe = DataFrame(result,
        #                              columns=["time"] + columns)

        # result_dataframe.set_index("time", inplace=True)
        # return result_dataframe
