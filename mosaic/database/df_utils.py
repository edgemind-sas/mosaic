from .datasource import InfluxDataSource
from pandas import DataFrame, Timedelta, Timestamp, date_range
from pandas.tseries.frequencies import to_offset


# Reindex to fill with NaN
def reindex_dataframe(df: DataFrame, start: Timestamp, stop: Timestamp, period: Timedelta):

    # we need a period in order to reindex
    if period is None or period.total_seconds() == 0:
        return df

    true_index_df = date_range(start=start, end=stop,
                               freq=to_offset(period), name='time').to_frame()

    true_index_df = true_index_df.join(df)

    true_index_df.drop("time", axis=1, inplace=True)

    return true_index_df
