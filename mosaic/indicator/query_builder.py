
import logging
import pandas as pd
from pydantic import BaseModel, Field

from .indicator_source import IndicatorSource


class QueryBuilder(BaseModel):

    def build_query(self, source: IndicatorSource, collection: str, time: pd.Timestamp):
        return self.build_query_for_period(source, collection, time, time)

    def build_query_for_period(self, source: IndicatorSource, collection: str,
                               start: pd.Timestamp, stop: pd.Timestamp):

        query = f'''
from(bucket: "{collection}")
    |> range({self.build_range_from_period(source, start, stop)})
    |> filter(fn: (r) => r["_measurement"] == "{source.config.name}")
    |> filter(fn: (r) => {self.build_tags_filter_string(source)})
    |> filter(fn: (r) => {self.build_fields_filter_string(source)})
    |> keep(columns: ["_measurement","_time","_field","_value"])
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'''

        logging.debug(f'query :{query}')

        return query

    def build_fields_filter_string(self, source: IndicatorSource):
        # r["_field"] == "open" or r["_field"] == "close"

        if len(source.config.values) == 0:
            return "true"

        field_concat_str = ""
        for idx, field in enumerate(source.config.values):
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

    def build_range_from_period(self, source: IndicatorSource,
                                start: pd.Timestamp, stop: pd.Timestamp):

        start_time: pd.Timestamp = start - \
            (source.period * source.config.history_bw)

        # we add 1ns to include last value
        stop_time: pd.Timestamp = stop + \
            (source.period * source.config.history_fw) + pd.to_timedelta("1ns")

        return f'start: time(v:{start_time.value}), stop: time(v:{stop_time.value})'
