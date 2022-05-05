from ..config.indicator_config import IndicatorSourceConfig
from ..indicator.indicator_source import IndicatorSource
from ..indicator.query.query_builder import QueryBuilder
from ..db_bakend.query_indicator import InfluxIndicatorQueryClient
import pandas as pd


def get_history(id, tags, value, bucket, start_date, stop_date, history_bw=0, history_fw=0):
    source_config = IndicatorSourceConfig(
        id=id, tags=tags, history_bw=history_bw, history_fw=history_fw, value=value)

    start_date_ts: pd.Timestamp = pd.to_datetime(
        start_date, utc=True, unit='ns')
    stop_date_ts: pd.Timestamp = pd.to_datetime(
        stop_date, utc=True, unit='ns')

    source = IndicatorSource(config=source_config, name="my_indicator")
    query_builder = QueryBuilder()
    query = query_builder.build_query_for_period(
        source, bucket, start_date_ts, stop_date_ts)

    client = InfluxIndicatorQueryClient()
    return client.query_as_dataframe(query)
