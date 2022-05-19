from .indicator_source import IndicatorSource
from pandas import DataFrame, Timestamp
from pandas.tseries.frequencies import to_offset
import pandas as pd


# Reindex to fill with NaN
def reindex_dataframe(df: DataFrame, source: IndicatorSource, start: Timestamp, stop: Timestamp):
    start_time = start - \
        (source.period * source.get_history_bw())

    # we add 1ns to include last value
    stop_time = stop + \
        (source.period * source.get_history_fw())

    true_index_df = pd.date_range(start=start_time, end=stop_time,
                                  freq=to_offset(source.period), name='time').to_frame()

    true_index_df = true_index_df.join(df)

    true_index_df.drop("time", axis=1, inplace=True)

    return true_index_df
