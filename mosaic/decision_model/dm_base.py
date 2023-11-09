import pydantic
import typing
import pandas as pd
import numpy as np
import random
#import tqdm
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ..utils.data_management import HyperParams
from ..utils.viz_tools import plotly_convert_to_line_style

#from ..trading.core import SignalBase
from ..core import ObjMOSAIC
from ..predict_model.pm_base import PredictModelBase
from ..indicator.indicator import Indicator
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

# PandasSeries = typing.TypeVar('pandas.core.frame.Series')
# PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')

        
class DMBase(ObjMOSAIC):
    """ Decision model base class """
    buy_threshold: float = \
        pydantic.Field(0, description="If signal_score > buy_threshold => buy signal generated",
                       ge=0)
                       
    sell_threshold: float = \
        pydantic.Field(0, description="If signal_score < -sell_threshold => sell signal generated",
                       ge=0)

    no_signal_code: str = \
        pydantic.Field("pass", description="String to be used when no signal is generated")
    
    params: HyperParams = \
        pydantic.Field(None, description="Decision model parameters")

    ohlcv_names: dict = pydantic.Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")


    
    @property
    def bw_length(self):
        return 0

    def compute_signal(self, signal_score_df, **kwrds):

        signal_s = pd.Series(
            self.no_signal_code,
            index=signal_score_df.index,
            name="decision",
            dtype=pd.CategoricalDtype(
                categories=["buy", "sell", self.no_signal_code]
            ),
        )

        if self.buy_threshold is not None:
            idx_buy = signal_score_df["score"] > self.buy_threshold
            signal_s.loc[idx_buy] = "buy"
            
        if self.sell_threshold is not None:
            idx_sell = signal_score_df["score"] < -self.sell_threshold
            signal_s.loc[idx_sell] = "sell"

        return pd.concat([signal_s,
                          signal_score_df],
                         axis=1)
    
    def predict(self, ohlcv_df, **kwrds):
        
        raise NotImplementedError("compute method not implemented")


    def plotly(self, ohlcv_df,
               ret_signals=False,
               layout={},
               #layout_ohlcv={},
               var_buy="open",
               var_sell="open",
               nb_sub_plot=2,
               buy_style=dict(
                   color="#FFD700",
                   opacity=0.7,
               ),
               sell_style=dict(
                   color="#C74AFF",
                   opacity=0.7,
               ),
               score_style=dict(
                   color="#1f416d",
                   opacity=0.7,
               ),
               **params):

        signals = self.predict(ohlcv_df, **params)
        decisions_s = signals["decision"]
        scores = signals["score"]
        
        var_buy_data = self.ohlcv_names.get(var_buy)
        var_sell_data = self.ohlcv_names.get(var_sell)
        
        signals_buy = decisions_s.loc[decisions_s == "buy"]
        signals_buy_trace = go.Scatter(
            x=signals_buy.index,
            y=ohlcv_df.loc[signals_buy.index, var_buy_data],
            mode='markers',
            marker=buy_style,
            name='buy signals')

        signals_sell = decisions_s.loc[decisions_s == "sell"]
        signals_sell_trace = go.Scatter(
            x=signals_sell.index,
            y=ohlcv_df.loc[signals_sell.index, var_sell_data],
            mode='markers',
            marker=sell_style,
            name='sell signals')

        signals_score_trace = go.Scatter(
            x=scores.index,
            y=scores,
            mode='markers+lines',
            marker=score_style,
            line=plotly_convert_to_line_style(score_style),
            name='Score')

        ohlcv_sub = dict(row=1, col=1)
        signal_score_sub = dict(row=2, col=1)
        subplot_layout = dict(rows=nb_sub_plot, cols=1)

        fig_sp = make_subplots(shared_xaxes=True,
                               vertical_spacing=0.02,
                               **subplot_layout)

        var_open = self.ohlcv_names.get("open", "open")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_close = self.ohlcv_names.get("close", "close")

        trace_ohlcv = go.Candlestick(x=ohlcv_df.index,
                                     open=ohlcv_df[var_open],
                                     high=ohlcv_df[var_high],
                                     low=ohlcv_df[var_low],
                                     close=ohlcv_df[var_close],
                                     name="OHLC")
        #fig_ohlcv.update_layout(**layout_ohlcv)
        fig_sp.add_trace(trace_ohlcv, **ohlcv_sub)
        fig_sp.add_trace(signals_score_trace, **signal_score_sub)

        fig_sp.add_trace(signals_buy_trace, **ohlcv_sub)
        fig_sp.add_trace(signals_sell_trace, **ohlcv_sub)

        # Threshold lines
        fig_sp.add_shape(
            type="line",
            x0=scores.index.min(), y0=self.buy_threshold,
            x1=scores.index.max(), y1=self.buy_threshold,
            line=dict(color=buy_style.get("color"),
                      width=3,
                      dash="dot"), **signal_score_sub)

        fig_sp.add_shape(
            type="line",
            x0=scores.index.min(), y0=-self.sell_threshold,
            x1=scores.index.max(), y1=-self.sell_threshold,
            line=dict(color=sell_style.get("color"),
                      width=3,
                      dash="dot"), **signal_score_sub)

        layout["xaxis_rangeslider_visible"] = False
        fig_sp.update_layout(**layout)

        if ret_signals:
            return fig_sp, signals
        else:
            return fig_sp

        
class DM1ML(DMBase):
    """ Decision model based on a single machine learning prediction model """

    pm: PredictModelBase = \
        pydantic.Field(PredictModelBase(), description="Buy/sell predict model")

    @property
    def bw_length(self):
        return self.pm.bw_length

    def fit(self, ohlcv_df, **kwrds):
        self.pm.fit(ohlcv_df, **kwrds)
    
    def predict(self, ohlcv_df, **kwrds):
        signal_score_df = pd.DataFrame(
            self.pm.predict(ohlcv_df, **kwrds).rename("score")
            )
        
        return self.compute_signal(signal_score_df)


class DMDR(DM1ML):
    """ Decision model based on deterministic rules """

    features: typing.Dict[str, Indicator] = pydantic.Field(
        [], description="Dict of features indicators")

    def __init__(self, **data: typing.Any):
        super().__init__(**data)

        self.pm = PredictModelBase(features=list(self.features.values()),
                                   ohlcv_names=self.ohlcv_names)
    
    def fit(self, ohlcv_df, **kwrds):
        pass

    def compute_signal_idx(self, features_df, **kwrds):
        """To be overloaded"""
        raise NotImplementedError
    
    def compute_signal(self, features_df, **kwrds):

        signal_s = pd.Series(
            self.no_signal_code,
            index=features_df.index,
            name="decision",
            dtype=pd.CategoricalDtype(
                categories=["buy", "sell", self.no_signal_code]
            ),
        )

        idx_buy, idx_sell = \
            self.compute_signal_idx(features_df, **kwrds)

        signal_s.loc[idx_buy] = "buy"
        signal_s.loc[idx_sell] = "sell"

        return pd.concat([signal_s,
                          features_df],
                         axis=1)

    def predict(self, ohlcv_df, **kwrds):
        return self.compute_signal(self.pm.compute_features(ohlcv_df))

    
class DM2ML(DMBase):
    """ Decision model based on two distinct machine learning prediction model : one for buy decisions and one for sell decisions """
    
    pm_buy: PredictModelBase = \
        pydantic.Field(PredictModelBase(), description="Buy predict model")
    pm_sell: PredictModelBase = \
        pydantic.Field(PredictModelBase(), description="Buy predict model")

    @property
    def bw_length(self):
        return max(self.pm_buy.bw_length, self.pm_sell.bw_length)

    def fit(self, ohlcv_df, **kwrds):
        self.pm_buy.fit(ohlcv_df, **kwrds)
        self.pm_sell.fit(ohlcv_df, **kwrds)
    
    def predict(self, ohlcv_df, **kwrds):

        buy_score = self.pm_buy.predict(ohlcv_df, **kwrds).rename("buy_score")
        sell_score = self.pm_sell.predict(ohlcv_df, **kwrds).rename("sell_score")

        signal_score = (buy_score - sell_score).rename("score")

        signal_score_df = pd.concat([signal_score,
                                     buy_score,
                                     sell_score], axis=1)
        return self.compute_signal(signal_score_df)

    def plotly(self,
               ohlcv_df,
               ret_signals=False,
               buy_style=dict(
                   color="#FFD700",
                   opacity=0.7,
               ),
               sell_style=dict(
                   color="#C74AFF",
                   opacity=0.7,
               ),
               score_style=dict(
                   color="#1f416d",
                   opacity=0.7,
               ),
               **kwrds):

        fig, signals = \
            super().plotly(ohlcv_df,
                           ret_signals=True,
                           nb_sub_plot=3,
                           buy_style=buy_style,
                           sell_style=sell_style,
                           score_style=score_style,
                           **kwrds)

        buy_score_trace = go.Scatter(
            x=signals.index,
            y=signals["buy_score"],
            mode='markers+lines',
            marker=buy_style,
            line=plotly_convert_to_line_style(buy_style),
            name='Buy score')
        
        sell_score_trace = go.Scatter(
            x=signals.index,
            y=signals["sell_score"],
            mode='markers+lines',
            marker=sell_style,
            line=plotly_convert_to_line_style(sell_style),
            name='Sell score')

        fig.add_trace(buy_score_trace, row=3, col=1)
        fig.add_trace(sell_score_trace, row=3, col=1)
        
        if ret_signals:
            return fig, signals
        else:
            return fig

