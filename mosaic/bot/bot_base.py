import logging
import pydantic
import typing
import pkg_resources
import pandas as pd
import pandas_ta as ta
import numpy as np
import plotly.express as px
from ..core import ObjMOSAIC
from ..indicator import RSIIndicator
#from ..trading.core import TradeBase, SignalBase
#from ..indicator import Indicator
from ..decision_model.dm_base import DMBase
from ..invest_model import InvestModel
#from ..utils import join_obj_columns

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401
if 'colored' in installed_pkg:
    import colored  # noqa: F401

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')
PandasSeries = typing.TypeVar('pandas.core.frame.Series')


def format_number(v, thresh=0, color_pos="green", color_neg="red", fmt="f"):
    if v is None:
        return v
    fmt_str = f"{{0:{fmt}}}"
    v_str = fmt_str.format(v)
    if ('colored' in installed_pkg):
        return colored.stylize(v_str, colored.fg("red"))\
            if v <= thresh else colored.stylize(v_str, colored.fg("green"))
    else:
        return v_str


class BotPerfBase(pydantic.BaseModel):
    
    perf_asset: float = pydantic.Field(
        None, description="Asset performance")

    nb_trades: int = pydantic.Field(
        None, description="Number of trades")
    
    trade_duration_mean: float = pydantic.Field(
        None, description="Strategy mean trade duration")

    time_between_trades_mean: float = pydantic.Field(
        None, description="Strategy mean time between trade")

    def __str__(self):
        strlist = []

        perf_asset_str = \
            format_number(self.perf_asset, 1)
        strlist.append(
            f"Perf asset: {perf_asset_str}")

        nb_trades_str = self.nb_trades
        strlist.append(
            f"Nb. trades: {nb_trades_str}")

        trade_duration_mean_str = self.trade_duration_mean
        strlist.append(
            f"Mean trade duration: {trade_duration_mean_str}")

        time_between_trades_mean_str = self.time_between_trades_mean
        strlist.append(
            f"Mean time between trades: {time_between_trades_mean_str}")
        
        return "\n".join(strlist)

    
class BotPerfTest(BotPerfBase):
    
    perf_open_open: float = pydantic.Field(
        None, description="Bot open-open asset performance")

    perf_high_low: float = pydantic.Field(
        None, description="Bot high-low asset performance")

    perf_rel_open_open: float = pydantic.Field(
        None, description="Bot open-open relative performance against asset perf")

    perf_rel_high_low: float = pydantic.Field(
        None, description="Bot high-low relative performance against asset perf")

    def __str__(self):
        strlist = [super().__str__()]

        perf_open_open_str = \
            format_number(self.perf_open_open, thresh=1, fmt="6.3f")
        perf_rel_open_open_str = \
            format_number(self.perf_rel_open_open, thresh=0, fmt="6.1%")

        strlist.append(
            f"Perf OO: {perf_open_open_str}"
            f" [{perf_rel_open_open_str} / asset]"
            )

        perf_high_low_str = \
            format_number(self.perf_high_low, thresh=1, fmt="6.3f")
        perf_rel_high_low_str = \
            format_number(self.perf_rel_high_low, thresh=0, fmt="6.1%")

        strlist.append(
            f"Perf HL: {perf_high_low_str}"
            f" [{perf_rel_high_low_str} / asset]"
            )

        return "\n".join(strlist)

    
class BotPerfLive(BotPerfBase):
    
    perf: float = pydantic.Field(
        None, description="Bot current asset performance")


class BotBase(ObjMOSAIC):

    name: str = pydantic.Field(
        None, description="Name of the backtest")

    # fees_buy: float = pydantic.Field(
    #     0, description="Buy fees to apply")

    # fees_sell: float = pydantic.Field(
    #     0, description="Sell fees to apply")
        
    decision_model: DMBase = pydantic.Field(
        None, description="Decision model")

    invest_model: InvestModel = pydantic.Field(
        None, description="Invest model")

    ohlcv_df: PandasDataFrame = pydantic.Field(
        None, description="BT OHLCV data")

    # asset_norm: PandasSeries = pydantic.Field(
    #     None, description="Asset evolution normalized over the period")

    signals: PandasSeries = pydantic.Field(
        None, description="Bot signals")

    trades_live: PandasDataFrame = \
        pydantic.Field(None, description="Bot live trades")

    trades_test: PandasDataFrame = \
        pydantic.Field(None, description="Bot test trades")


    # trades_open_open: PandasDataFrame = pydantic.Field(
    #     None, description="Test open-open trades")

    # trades_high_low: PandasDataFrame = pydantic.Field(
    #     None, description="Test high-low trades")

    # perf: typing.Dict[str, BotPerf] = pydantic.Field(
    #     {"live": BotPerf(), "open_open": BotPerf(), "high_low": BotPerf()}, \
    #     description="BT performance")
    perf_live: BotPerfLive = \
        pydantic.Field(BotPerfLive(), description="BT test performance")

    perf_test: BotPerfTest = \
        pydantic.Field(BotPerfTest(), description="BT test performance")
   
    ohlcv_names: dict = pydantic.Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")
    
    def run_test(self, ohlcv_df, fees=0, update=False, **kwrds):

        signals = self.decision_model.compute(ohlcv_df, **kwrds)

        if (self.signals is None) or (not update):
            self.signals = signals
            self.ohlcv_df = ohlcv_df
        else:
            idx_update = signals.index.difference(self.signals.index)
            self.signals = pd.concat([self.signals, signals.loc[idx_update]])
            self.ohlcv_df = pd.concat([self.ohlcv_df, ohlcv_df.loc[idx_update]])

        # try:
        #     signals_bis = self.decision_model.compute(self.ohlcv_df, **kwrds)
        #     pd.testing.assert_series_equal(self.signals.fillna(method="ffill").fillna(0),
        #                                    signals_bis.fillna(method="ffill").fillna(0))
        # except:
        #     idx_diff = self.signals != signals_bis
        #     signals_concat = pd.concat([self.signals, signals_bis.rename("signal_bis")], axis=1)
        #     signals_diff = signals_concat.loc[idx_diff]
        #     print(signals_diff)
        #     ipdb.set_trace()

        self.compute_trades_test(fees=fees)

        self.evaluate_test()


    def run_live(self, dt_cur, ohlcv_df, **kwards):

        ipdb.set_trace()
        signals = self.decision_model.compute(ohlcv_df, **kwrds)
        
        
                
    def evaluate_test(self, **kwrds):
        
        var_open = self.ohlcv_names.get("open", "open")
        var_low = self.ohlcv_names.get("low", "low")
        var_high = self.ohlcv_names.get("high", "high")
        var_close = self.ohlcv_names.get("close", "close")

        self.perf_test.perf_asset = \
            self.ohlcv_df[var_close].iloc[-1]/self.ohlcv_df[var_open].iloc[0]

        self.perf_test.nb_trades = len(self.trades_test)
                
        if self.perf_test.nb_trades == 0:
            return

        self.perf_test.trade_duration_mean = \
            self.trades_test["trade_duration"].mean()

        self.perf_test.time_between_trades_mean = \
            self.trades_test["time_from_last_trade"].mean()

        for var_buy, var_sell in [("open", "open"),
                                  ("high", "low")]:

            var_returns_1 = f"returns1_{var_buy}_{var_sell}"
            var_perf = f"perf_{var_buy}_{var_sell}"
            var_perf_rel = f"perf_rel_{var_buy}_{var_sell}"
            
            ret1_log = np.log(self.trades_test[var_returns_1])
            self.trades_test[var_perf] = np.exp(ret1_log.cumsum())

            perf_cur = self.trades_test[var_perf].iloc[-1]
            perf_rel_cur = perf_cur/self.perf_test.perf_asset - 1
            
            setattr(self.perf_test, var_perf, perf_cur)
            setattr(self.perf_test, var_perf_rel, perf_rel_cur)
            
    #ipdb.set_trace()


