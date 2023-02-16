from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import typing
import pydantic
from .dm_base import DMBaseParams
from .dm_long import DMLong
from ..indicator import RSIIndicator
import pkg_resources
import numpy as np
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')


class DML_RSI_params(DMBaseParams):

    window: int = \
        pydantic.Field(0, description="MA window size used to compute RSI "
                       "indicator")
    buy_level: float = \
        pydantic.Field(30, description="RSI level to trigger a buy signal")

    sell_level: float = \
        pydantic.Field(70, description="RSI level to trigger a sell signal")


class DML_RSI(DMLong):

    params: DML_RSI_params = \
        pydantic.Field(0, description="RSI parameters")
    
    # def __init__(self, **params):
    #     super.__init__(**params)

    def compute(self, ohlcv_df, offset=1, **kwrds):
        
        self.indic_bkd = \
            RSIIndicator(window=self.params.window,
                         levels=[self.params.buy_level, self.params.sell_level],
                         mode="wilder",
                         offset=offset)

        self.indic_df = self.indic_bkd.compute(ohlcv_df)

        idx_buy = \
            self.indic_df[self.indic_bkd.indic_name_offset] < self.params.buy_level
        idx_sell = \
            self.indic_df[self.indic_bkd.indic_name_offset] > self.params.sell_level

        self.compute_orders(idx_buy, idx_sell)

        return self.orders


class DML_MACD(DMLong):

    window: int = \
        pydantic.Field(0, description="MA window size used to compute RSI "
                       "indicator")

    buy_level: float = \
        pydantic.Field(30, description="RSI level to trigger a buy signal")

    sell_level: float = \
        pydantic.Field(70, description="RSI level to trigger a sell signal")

    # def __init__(self, **params):
    #     super.__init__(**params)

    def compute(self, ohlcv_df, offset=1, **kwrds):

        self.indic_bkd = \
            RSIIndicator(window=self.window,
                         levels=[self.buy_level, self.sell_level],
                         mode="wilder",
                         offset=offset)

        self.indic_df = self.indic_bkd.compute(ohlcv_df)

        self.orders_raw = pd.Series(index=ohlcv_df.index,
                                    dtype="float")

        # ipdb.set_trace()
        idx_buy = self.indic_df[self.indic_bkd.indic_name_offset] < self.buy_level
        idx_sell = self.indic_df[self.indic_bkd.indic_name_offset] > self.sell_level

        self.orders_raw.loc[idx_buy] = 1
        self.orders_raw.loc[idx_sell] = 0

        self.apply_hold_time_constraint()

        return self.orders
