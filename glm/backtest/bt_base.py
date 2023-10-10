import logging
import pydantic
import typing
import pkg_resources
import pandas as pd
import numpy as np
import plotly.express as px

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401
    
from ..indicator import Indicator
from ..decision_model.dm_base import DMBase
from ..invest_model import InvestModelBase
from ..utils import join_obj_columns

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')
PandasSeries = typing.TypeVar('pandas.core.frame.Series')


class BTPerformance(pydantic.BaseModel):
    
    perf_buy_hold: float = pydantic.Field(
        None, description="Returns obtain with buy and hold strategy")

    nb_trades: int = pydantic.Field(
        None, description="Number of trades")
    
    perf_open_open: float = pydantic.Field(
        None, description="Strategy open-open returns")

    perf_high_low: float = pydantic.Field(
        None, description="Strategy high-low returns")

    trade_duration_mean: float = pydantic.Field(
        None, description="Strategy mean trade duration")

    time_between_trades_mean: float = pydantic.Field(
        None, description="Strategy mean time between trade")


class DMConfig(pydantic.BaseModel):

    fit_horizon: int = pydantic.Field(
        None, description="Number of historical data used to adjust decision model ")

    predict_horizon: int = pydantic.Field(
        None, description="Number of decisions before updating decision model")


class BTBase(pydantic.BaseModel):

    name: str = pydantic.Field(
        None, description="Name of the backtest")

    fees_buy: float = pydantic.Field(
        0, description="Buy fees to apply")

    fees_sell: float = pydantic.Field(
        0, description="Sell fees to apply")
        
    decision_model: DMBase = pydantic.Field(
        None, description="Decision model")

    invest_model: InvestModelBase = pydantic.Field(
        None, description="Invest model")

    ohlcv_df: PandasDataFrame = pydantic.Field(
        None, description="BT OHLCV data")

    asset_norm: PandasSeries = pydantic.Field(
        None, description="Asset evolution normalized over the period")

    dm_config: DMConfig = pydantic.Field(
        DMConfig(), description="Decision Model learning parameters")
    
    # indic_df: PandasDataFrame = pydantic.Field(
    #     None, description="BT indicators data")

    # decisions_df: PandasDataFrame = pydantic.Field(
    #     None, description="BT Decisions data")

    # decisions_s: PandasSeries = pydantic.Field(
    #     None, description="BT Decisions ")
    
    trades_df: PandasDataFrame = pydantic.Field(
        None, description="BT trades")

    perf: BTPerformance = pydantic.Field(
        BTPerformance(), description="BT performance")
    
    ohlcv_names: dict = pydantic.Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")

    
    @classmethod
    def get_subclasses(cls, recursive=True):
        """ Enumerates all subclasses of a given class.

        # Arguments
        cls: class. The class to enumerate subclasses for.
        recursive: bool (default: True). If True, recursively finds all sub-classes.

        # Return value
        A list of subclasses of `cls`.
        """
        sub = cls.__subclasses__()
        if recursive:
            for cls in sub:
                sub.extend(cls.get_subclasses(recursive))
        return sub

    @classmethod
    def from_config(basecls, **config):

        cls_sub_dict = {
            cls.__name__: cls for cls in BTBase.get_subclasses(basecls)}

        clsname = config.pop("class_name")
        cls = cls_sub_dict.get(clsname)

        if cls is None:
            raise ValueError(
                f"{clsname} is not a subclass of {basecls.__name__}")

        return cls(**config)

    def evaluate(self, **kwrds):

        var_open = self.ohlcv_names.get("open", "open")
        var_low = self.ohlcv_names.get("low", "low")
        var_high = self.ohlcv_names.get("high", "high")
        var_close = self.ohlcv_names.get("close", "close")

        self.asset_norm = \
            (self.ohlcv_df[var_open]/self.ohlcv_df[var_open].iloc[0]).rename("perf_asset")
        
        self.perf.perf_buy_hold = \
            self.asset_norm.iloc[-1]

        self.perf.nb_trades = len(self.trades_df)

        if self.perf.nb_trades == 0:
            return

        self.perf.trade_duration_mean = \
            self.trades_df["trade_duration"].mean()

        self.perf.time_between_trades_mean = \
            self.trades_df["time_from_last_trade"].mean()

        for var_buy, var_sell in [(var_open, var_open),
                                  (var_high, var_low)]:

            var_returns_1 = f"returns1_{var_buy}_{var_sell}"
            var_returns_1_fees = f"{var_returns_1}_fees"
            var_perf = f"perf_{var_buy}_{var_sell}"
            
            ret1_log = np.log(self.trades_df[var_returns_1_fees])
            self.trades_df[var_perf] = np.exp(ret1_log.cumsum())

            setattr(self.perf, var_perf,
                    self.trades_df[var_perf].iloc[-1])
            
    #ipdb.set_trace()
        
