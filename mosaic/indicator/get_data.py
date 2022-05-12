from ..config.indicator_config import IndicatorSourceConfig
from .indicator_source import IndicatorSource
from mosaic.indicator import QueryBuilder
from ..db_bakend.query_indicator import InfluxIndicatorQueryClient
import pandas as pd


def get_data(name, tags, values, collection, start_date, stop_date, history_bw=0, history_fw=0):
    source_config = IndicatorSourceConfig(
        name=name, tags=tags, history_bw=history_bw, history_fw=history_fw, values=values)

    start_date_ts: pd.Timestamp = pd.to_datetime(
        start_date, utc=True, unit='ns')
    stop_date_ts: pd.Timestamp = pd.to_datetime(
        stop_date, utc=True, unit='ns')

    source = IndicatorSource(config=source_config, name="my_indicator")
    query_builder = QueryBuilder()
    query = query_builder.build_query_for_period(
        source, collection, start_date_ts, stop_date_ts)

    client = InfluxIndicatorQueryClient()
    df = client.query_as_dataframe(query)
    df = df.reindex(values, axis="columns")
    return df
