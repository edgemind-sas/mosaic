
import logging
import pandas as pd
from .datasource import InfluxDataSource


def __build_fields_filter_string(source: InfluxDataSource):
    # r["_field"] == "open" or r["_field"] == "close"

    if source.values is None or len(source.values) == 0:
        return "true"

    field_concat_str = ""
    for idx, field in enumerate(source.values):
        if idx > 0:
            field_concat_str += " or "
        field_concat_str += f'r["_field"] == "{field}"'
    # in case we don't have field filter
    if field_concat_str == "":
        field_concat_str = "true"
    return field_concat_str


def __build_tags_filter_string(source: InfluxDataSource):
    # r["interval"] == "3m" and r["symbol"] == "BTC-USDT"
    tags_concat_str = ""
    for idx, tag in enumerate(source.tags.keys()):
        if idx > 0:
            tags_concat_str += " and "
        tags_concat_str += f'r["{tag}"] == "{source.tags.get(tag)}"'

    # in case we don't have tags filter
    if tags_concat_str == "":
        tags_concat_str = "true"

    return tags_concat_str


def __build_range_from_period(source: InfluxDataSource,
                              start: pd.Timestamp, stop: pd.Timestamp):

    # we add 1ns to include last value
    stop += pd.to_timedelta("1ns")

    return f'start: time(v:{start.value}), stop: time(v:{stop.value})'


def build_query_for_period(source: InfluxDataSource,
                           start: pd.Timestamp, stop: pd.Timestamp):

    query = f'''
from(bucket: "{source.collection}")
|> range({__build_range_from_period(source, start, stop)})
|> filter(fn: (r) => r["_measurement"] == "{source.name}")
|> filter(fn: (r) => {__build_tags_filter_string(source)})
|> filter(fn: (r) => {__build_fields_filter_string(source)})
|> keep(columns: ["_measurement","_time","_field","_value"])
|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'''

    logging.debug(f'query :{query}')

    return query
