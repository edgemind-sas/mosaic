from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import typing
import pydantic
from . import DecisionModel
from ..indicator import ReturnsCloseIndicator, ReturnsHighIndicator, ReturnsLowIndicator
import pkg_resources
import numpy as np
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')

class QHLDM(DecisionModel):

    horizon: int = \
        pydantic.Field(0, description="Invest horizon")
    period_name: str = \
        pydantic.Field("period", description="Returns period column index name")
    period_fmt: str = \
        pydantic.Field(None, description="Period columns format")
    returns_hlc: typing.Dict[str, PandasDataFrame] = \
        pydantic.Field({}, description="Returns dictionnary")
    ret_hl_indic_grp: typing.Dict[str, typing.Any] = \
        pydantic.Field({}, description="Private returns HL/Indic groupby structure")
    level_high: float = \
        pydantic.Field(0.5, description="High returns level to set take profit threshold")
    level_low: float = \
        pydantic.Field(0.5, description="Low returns level to set stop loss threshold")
       
    def compute_returns_hlc(self, ohlcv_df: pd.DataFrame):

        returns_hlc = {}
        self.returns_hlc["high"] = ReturnsHighIndicator(
            horizon=[self.horizon],
            period_name=self.period_name,
            period_fmt=self.period_fmt,
            ohlcv_names=self.ohlcv_names).compute(ohlcv_df)
        self.returns_hlc["low"] = ReturnsLowIndicator(
            horizon=[self.horizon],
            period_name=self.period_name,
            period_fmt=self.period_fmt,
            ohlcv_names=self.ohlcv_names).compute(ohlcv_df)
        # self.returns_hlc["close"] = ReturnsCloseIndicator(
        #     horizon=[self.horizon],
        #     period_name=self.period_name,
        #     period_fmt=self.period_fmt,
        #     ohlcv_names=self.ohlcv_names).compute(ohlcv_df)

        return self.returns_hlc

    def fit(self, ohlcv_df: pd.DataFrame, indic_df: pd.DataFrame):

        self.compute_returns_hlc(ohlcv_df)

        for ret_name in ["low", "high"]:
            self.ret_hl_indic_grp = \
                {ret_name: pd.concat([self.returns_hlc[ret_name], indic_df], axis=1)\
                 .groupby(list(indic_df.columns)) for ret_name in ["low", "high"]}
            
    def compute(self, ohlcv_df, indic_df, **kwrds):
        """ 
        indic_df : the discretized indicator as a Dataframe
        """

        #decision_df = ohlcv_df.join(indic_df)
        
        #bt_results_df["close[-1]"] =bt_results_df["close"].shift() # we will need close[-1] to calculate the sl_price and tp_price

        # rho_low : the low returns quantile at level level_low
        rho_low = self.ret_hl_indic_grp["low"]\
              .quantile(1 - self.level_low)\
              .rename(columns={self.horizon:"rho_low"})
        
        # rho_high : the high returns quantile at level level_high
        rho_high = self.ret_hl_indic_grp["high"]\
              .quantile(self.level_high)\
              .rename(columns={self.horizon:"rho_high"})

        decisions_df = pd.concat([
            indic_df.join(rho_low,
                          on=list(indic_df.columns))["rho_low"],
            indic_df.join(rho_high,
                          on=list(indic_df.columns))["rho_high"]], axis=1)
        
        decisions_df["sl_price"] = \
            (1 + decisions_df["rho_low"])*ohlcv_df[self.ohlcv_names["open"]]
        decisions_df["tp_price"] = \
            (1 + decisions_df["rho_high"])*ohlcv_df[self.ohlcv_names["open"]]

        sell_time_s = pd.Series(np.nan, index=decisions_df.index, name="sell_time")
        sell_signal_s = pd.Series(np.nan, index=decisions_df.index, name="sell_signal")
        sell_price_s = pd.Series(np.nan, index=decisions_df.index, name="sell_price")

        # decision_df.loc["sell_signal"] = np.nan
        # decision_df.loc["sell_price"] = np.nan

        deltat = ohlcv_df.index[1] - ohlcv_df.index[0]
        
        ohlcv_low_shift_df = \
            pd.concat([ohlcv_df[self.ohlcv_names["low"]].shift(-i).rename(i)
                       for i in range(self.horizon + 1)], axis=1)
        sl_price_dup_df = \
            pd.concat([decisions_df["sl_price"].rename(i)
                       for i in range(self.horizon + 1)], axis=1)

        ohlcv_high_shift_df = \
            pd.concat([ohlcv_df[self.ohlcv_names["high"]].shift(-i).rename(i)
                       for i in range(self.horizon + 1)], axis=1)
        tp_price_dup_df = \
            pd.concat([decisions_df["tp_price"].rename(i)
                       for i in range(self.horizon + 1)], axis=1)
        
        idx_na = ohlcv_low_shift_df.isna().any(axis=1) | \
            ohlcv_high_shift_df.isna().any(axis=1) | \
            sl_price_dup_df.isna().any(axis=1) | \
            tp_price_dup_df.isna().any(axis=1) | \
            (ohlcv_df.index > ohlcv_df.index[-1] - (self.horizon + 1)*deltat)


        tp_period = (ohlcv_high_shift_df > tp_price_dup_df).idxmax(axis=1) + \
            (ohlcv_high_shift_df < tp_price_dup_df).all(axis=1)*(self.horizon + 1)
        sl_period = (ohlcv_low_shift_df < sl_price_dup_df).idxmax(axis=1) + \
            (ohlcv_low_shift_df > sl_price_dup_df).all(axis=1)*(self.horizon + 1)
        
        idx_hl = (tp_period > self.horizon) & (sl_period > self.horizon) & ~idx_na
        idx_tp = (tp_period < sl_period) & ~idx_hl & ~idx_na 
        idx_sl = (tp_period > sl_period) & ~idx_hl & ~idx_na
        idx_sltp = (tp_period == sl_period) & ~idx_hl & ~idx_na 

        # Set sell time and sell signal
        sell_signal_s.loc[idx_hl] = "HL"
        sell_time_s.loc[idx_hl] = decisions_df.index[idx_hl] + self.horizon*deltat

        sell_signal_s.loc[idx_tp] = "TP"
        sell_time_s.loc[idx_tp] = decisions_df.index[idx_tp] + tp_period.loc[idx_tp]*deltat

        sell_signal_s.loc[idx_sl] = "SL"
        sell_time_s.loc[idx_sl] = decisions_df.index[idx_sl] + tp_period.loc[idx_sl]*deltat

        sell_signal_s.loc[idx_sltp] = "SLTP"
        sell_time_s.loc[idx_sltp] = decisions_df.index[idx_sltp] + tp_period.loc[idx_sltp]*deltat

        # Set sell price
        sell_price_s.loc[idx_hl] = \
            ohlcv_df.loc[sell_time_s.loc[idx_hl],
                         self.ohlcv_names["close"]].values[:]
        sell_price_s.loc[idx_sl] = \
            decisions_df.loc[sell_time_s.loc[idx_sl], "sl_price"].values[:]
        sell_price_s.loc[idx_tp] = \
            decisions_df.loc[sell_time_s.loc[idx_tp], "tp_price"].values[:]
        sell_price_s.loc[idx_sltp] = \
            decisions_df.loc[sell_time_s.loc[idx_sltp], "sl_price"].values[:]


        # idx_tp = (ohlcv_low_shift_df > sl_price_dup_df).all(axis=1) & \
        #     (ohlcv_high_shift_df < tp_price_dup_df).all(axis=1) & \
        #     ~idx_na

        # sell_signal_s.loc[idx_tp] = "TP"
        # sell_time_s.loc[idx_tp] = decision_df.index[idx_tp] + self.horizon*deltat


        # sell_price_s.loc[~idx_na] = \
        #     ohlcv_df.loc[sell_time_s.loc[~idx_na],
        #                  self.ohlcv_names["close"]].values[:]

        decisions_df = pd.concat([decisions_df,
                                 sell_signal_s,
                                 pd.to_datetime(sell_time_s),
                                 sell_price_s], axis=1)

        
        return decisions_df
