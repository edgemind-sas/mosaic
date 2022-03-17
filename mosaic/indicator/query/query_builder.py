
import logging
from datetime import datetime
import pandas as pd
from pydantic import BaseModel, Field

from ..indicator_source import IndicatorSource


class QueryBuilder(BaseModel):

    def buildQuery(self, source: IndicatorSource, bucket: str, time: datetime):

        query = f'''
from(bucket: "{bucket}")
    |> range({self.build_range_from_ts(source, time)})
    |> filter(fn: (r) => r["_measurement"] == "{source.config.id}")
    |> filter(fn: (r) => {self.build_tags_filter_string(source)})
    |> filter(fn: (r) => {self.build_fields_filter_string(source)})
    |> keep(columns: ["_measurement","_time","_field","_value"])
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'''

        logging.debug(f'query :{query}')

        return query

    def build_fields_filter_string(self, source: IndicatorSource):
        # r["_field"] == "open" or r["_field"] == "close"
        field_concat_str = ""
        for idx, field in enumerate(source.config.value):
            if idx > 0:
                field_concat_str += " or "
            field_concat_str += f'r["_field"] == "{field}"'
        # in case we don't have field filter
        if field_concat_str == "":
            field_concat_str = "true"
        return field_concat_str

    def build_tags_filter_string(self, source: IndicatorSource):
        # r["interval"] == "3m" and r["symbol"] == "BTC-USDT"
        tags_concat_str = ""
        for idx, tag in enumerate(source.config.tags.keys()):
            if idx > 0:
                tags_concat_str += " and "
            tags_concat_str += f'r["{tag}"] == "{source.config.tags.get(tag)}"'

        # in case we don't have tags filter
        if tags_concat_str == "":
            tags_concat_str = "true"

        return tags_concat_str

    def build_range_from_ts(self, source: IndicatorSource, time: pd.Timestamp):

        period_string = source.config.tags.get("period")
        period = pd.to_timedelta(period_string)

        start_time: pd.Timestamp = time - (period * source.config.history_bw)

        # we had 1ns because range resquest exclude the pooint @ stop
        stop_time: pd.Timestamp = time + \
            (period * source.config.history_fw) + pd.to_timedelta("1ns")

        return self.build_range_string(start_time, stop_time)

    def build_range_string(self, start: pd.Timestamp, stop: pd.Timestamp):
        return f'start: time(v:{start.value}), stop: time(v:{stop.value})'
