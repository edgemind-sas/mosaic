from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import typing
import pydantic
from .dm_base import DMBaseParams
from .dm_long import DMLong
from ..indicator.indicator import IndicatorOHLCV
from ..indicator.trend_indicator import RSIIndicator
import pkg_resources
import numpy as np
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')
PandasSeries = typing.TypeVar('pandas.core.frame.DataFrame')


class DML_TA(DMLong):

    indic_bkd: IndicatorOHLCV = \
        pydantic.Field(None, description="Indicator backend")

    indic_s: PandasSeries = \
        pydantic.Field(None, description="Indicator series")

    @property
    def bw_window(self):
        return self.indic_bkd.bw_window

    def compute(self, ohlcv_df, **kwrds):

        self.indic_s = \
            self.indic_bkd.compute(ohlcv_df)[self.indic_bkd.indic_name_offset]

        if self.indic_s is None:
            self.indic_s = pd.Series(np.nan, index=ohlcv_df.index)
            
class DML_RSI_params(DMBaseParams):

    window: int = \
        pydantic.Field(0, description="MA window size used to compute RSI "
                       "indicator")
    buy_level: float = \
        pydantic.Field(30, description="RSI level to trigger a buy signal")

    sell_level: float = \
        pydantic.Field(70, description="RSI level to trigger a sell signal")



class DML_RSI(DML_TA):

    params: DML_RSI_params = \
        pydantic.Field(DML_RSI_params(), description="RSI parameters")
    
    def __init__(self, offset=1, **params):
        super().__init__(**params)

        self.indic_bkd = \
            RSIIndicator(window=self.params.window,
                         levels=[self.params.buy_level, self.params.sell_level],
                         offset=offset)
        
    def compute(self, ohlcv_df, **kwrds):

        super().compute(ohlcv_df, **kwrds)

        # --- Decision rule --- #

        idx_buy = self.indic_s < self.params.buy_level
        idx_sell = self.indic_s > self.params.sell_level

        # --- End of decision rule --- #
        
        signals_raw = self.compute_signals(idx_buy, idx_sell)

        #ipdb.set_trace()
        
        return signals_raw


class DML_RSI2_params(DML_RSI_params):

    window_conf_signal: int = \
        pydantic.Field(1, description="Signal confirmation window")

    window_conf_change: int = \
        pydantic.Field(1, description="Change confirmation window")

    
class DML_RSI2(DML_RSI):

    params: DML_RSI2_params = \
        pydantic.Field(DML_RSI2_params(), description="RSI parameters")

    @property
    def bw_window(self):
        return max(super().bw_window,
                   self.params.window_conf_change + \
                   self.params.window_conf_signal)
    
    def __init__(self, offset=1, **params):
        super().__init__(**params)

        self.indic_bkd = \
            RSIIndicator(window=self.params.window,
                         levels=[self.params.buy_level, self.params.sell_level],
                         offset=offset)
        
    def compute(self, ohlcv_df, **kwrds):

        super().compute(ohlcv_df, **kwrds)

        # --- Decision rule --- #
        indic_conf_signal = \
            pd.concat([self.indic_s.shift(self.params.window_conf_change + k)
                       for k in range(self.params.window_conf_signal)], axis=1)

        indic_conf_change = \
            pd.concat([self.indic_s.shift(k)
                       for k in range(self.params.window_conf_change)], axis=1)

        
        # Confirmation time for buy/sell signals
        indic_conf_signal_buy = \
            (indic_conf_signal < self.params.buy_level).all(axis=1)
        indic_conf_signal_sell = \
            (indic_conf_signal > self.params.sell_level).all(axis=1)

        # Confirmation time for buy/sell trend changes
        indic_conf_change_buy = \
            (indic_conf_change > self.params.buy_level).all(axis=1)
        indic_conf_change_sell = \
            (indic_conf_change < self.params.sell_level).all(axis=1)

        
        # Go out of buy/sell signal after confirmation time
        idx_buy = indic_conf_signal_buy & indic_conf_change_buy
        idx_sell = indic_conf_signal_sell & indic_conf_change_sell

        # TEST
        # indic_test = pd.concat([self.indic_s, indic_conf_signal, indic_conf_change], axis=1)
        # indic_buy = pd.concat([self.indic_s, indic_conf_signal_buy, indic_conf_change_buy, idx_buy], axis=1)
        # indic_sell = pd.concat([self.indic_s, indic_conf_signal_sell, indic_conf_change_sell, idx_sell], axis=1)
        # print(indic_test.tail(50))
        # print(indic_buy.tail(50))
        # print(indic_sell.tail(50))
        # ipdb.set_trace()

        # --- End of decision rule --- #
        
        signals_raw = self.compute_signals(idx_buy, idx_sell)

        #ipdb.set_trace()
        
        return signals_raw
