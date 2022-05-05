
import logging
import pandas as pd
from pydantic import BaseModel, Field

from ..indicator_source import IndicatorSource


class QueryBuilder(BaseModel):

    def build_query(self, source: IndicatorSource, bucket: str, time: pd.Timestamp):

        period_string = source.config.tags.get("period")

        query = f'''
from(bucket: "{bucket}")
    |> range({self.build_range_from_ts(source, time)})
    |> filter(fn: (r) => r["_measurement"] == "{source.config.id}")
    |> filter(fn: (r) => {self.build_tags_filter_string(source)})
    |> filter(fn: (r) => {self.build_fields_filter_string(source)})
    |> aggregateWindow(every: {period_string}, fn: last, createEmpty: true)
    |> keep(columns: ["_measurement","_time","_field","_value"])
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'''

        logging.debug(f'query :{query}')

        return query

    def build_query_for_period(self, source: IndicatorSource, bucket: str,
                               start: pd.Timestamp, stop: pd.Timestamp):

        period_string = source.config.tags.get("period")

        query = f'''
from(bucket: "{bucket}")
    |> range({self.build_range_from_period(source, start, stop)})
    |> filter(fn: (r) => r["_measurement"] == "{source.config.id}")
    |> filter(fn: (r) => {self.build_tags_filter_string(source)})
    |> filter(fn: (r) => {self.build_fields_filter_string(source)})
    |> aggregateWindow(every: {period_string}, fn: last, createEmpty: true)
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

        # TODO: we remove 1ns because aggregateWindow aggregate the extrem values
        start_time: pd.Timestamp = time - \
            (source.period * source.config.history_bw) - pd.to_timedelta("1ns")

        stop_time: pd.Timestamp = time + \
            (source.period * source.config.history_fw)

        return self.build_range_string(start_time, stop_time)

    def build_range_from_period(self, source: IndicatorSource,
                                start: pd.Timestamp, stop: pd.Timestamp):

        # TODO: we remove 1ns because aggregateWindow aggregate the extrem values
        start_time: pd.Timestamp = start - \
            (source.period * source.config.history_bw) - pd.to_timedelta("1ns")

        stop_time: pd.Timestamp = stop + \
            (source.period * source.config.history_fw)

        return self.build_range_string(start_time, stop_time)

    def build_range_string(self, start: pd.Timestamp, stop: pd.Timestamp):
        return f'start: time(v:{start.value}), stop: time(v:{stop.value})'
