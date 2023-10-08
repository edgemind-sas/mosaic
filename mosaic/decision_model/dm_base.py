import pydantic
import typing
import pandas as pd
import random
#import tqdm
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ..utils.data_management import HyperParams

#from ..trading.core import SignalBase
from ..core import ObjMOSAIC
from ..predict_model.pm_base import PredictModelBase

import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

# PandasSeries = typing.TypeVar('pandas.core.frame.Series')
# PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')

        
class DMBase(ObjMOSAIC):

    buy_threshold: float = \
        pydantic.Field(None, description="If signal_score > buy_threshold => buy signal generated",
                       ge=0)
                       
    sell_threshold: float = \
        pydantic.Field(None, description="If signal_score < -sell_threshold => sell signal generated",
                       ge=0)
    
    params: HyperParams = \
        pydantic.Field(None, description="Decision model parameters")

    ohlcv_names: dict = pydantic.Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")


    
    @property
    def bw_length(self):
        return 0

    def compute_signal(self, signal_score, **kwrds):

        #ipdb.set_trace()
        signal_s = pd.Series(index=signal_score.index,
                             name="signal",
                             dtype="object")

        if self.buy_threshold is not None:
            idx_buy = signal_score > self.buy_threshold
            signal_s.loc[idx_buy] = "buy"
            
        if self.sell_threshold is not None:
            idx_sell = signal_score < -self.sell_threshold
            signal_s.loc[idx_sell] = "sell"

        return pd.concat([signal_s,
                          signal_score.rename("score")],
                         axis=1)
    
    def predict(self, ohlcv_df, **kwrds):
        
        raise NotImplementedError("compute method not implemented")

    # def fit(self, ohlcv_df, method="brute_force", **fit_params):

    #     fit_method = getattr(self, f"fit_{method}")

    #     fit_method(ohlcv_df, **fit_params)
       
    # def fit_brute_force(self, ohlcv_df,
    #                     bt_cls,
    #                     bt_params={},
    #                     dm_params={},
    #                     progress_mode=True,
    #                     target_measure="perf_open_open",
    #                     nb_trades_min=15,
    #                     ):

    #     dm_params_list = compute_combinations(**self.dm_params)

    #     bt_eval_list = []
    #     for params in tqdm.tqdm(dm_params_list,
    #                             disable=not progress_mode,
    #                             desc="Parameters",
    #                             ):
            
    #         bt_cur = bt_cls(
    #             ohlcv_df=ohlcv_df,
    #             decision_model=self.dm_cls(**params),
    #             **bt_params,
    #         )
            
    #         bt_cur.run()
    
    #         bt_eval_list.append(dict(params, **bt_cur.perf.dict()))

    #     brute_force_df = \
    #         pd.DataFrame.from_records(bt_eval_list)\
    #                     .sort_values(by=target_measure,
    #                                  ascending=False)

    #     idx_const_nb_trades = \
    #         brute_force_df["nb_trades"] > nb_trades_min

    #     brute_force_bis_df = \
    #         brute_force_df.loc[idx_const_nb_trades]

    #     dm_params_opt = \
    #         brute_force_bis_df.iloc[0]\
    #                           .loc[dm_params.keys()]\
    #                           .to_dict()

    #     self.params = self.params.__class__(**dm_params_opt)

    def plotly(self, ohlcv_df,
               ret_signals=False,
               layout={},
               layout_ohlcv={},
               layout_indic={},
               var_buy="open",
               var_sell="open",
               **params):

        signals = self.compute_signal(ohlcv_df, **params)
        decisions_s = signals["signal"]
        scores = signals["score"]
        
        buy_style = dict(
            color="#FFD700",
        )
        sell_style = dict(
            color="#C74AFF",
        )
        score_style = dict(
            color="#3300CC",
        )

        var_buy_data = self.ohlcv_names.get(var_buy)
        var_sell_data = self.ohlcv_names.get(var_sell)
        
        signals_buy = decisions_s.loc[decisions_s == "buy"]
        signals_buy_trace = go.Scatter(
            x=signals_buy.index,
            y=ohlcv_df.loc[signals_buy.index, var_buy_data],
            mode='markers',
            marker=dict(color=buy_style.get("color")),
            name='buy signals')

        signals_sell = decisions_s.loc[decisions_s == "sell"]
        signals_sell_trace = go.Scatter(
            x=signals_sell.index,
            y=ohlcv_df.loc[signals_sell.index, var_sell_data],
            mode='markers',
            marker=dict(color=sell_style.get("color")),
            name='sell signals')

        signals_score_trace = go.Scatter(
            x=scores.index,
            y=scores,
            mode='markers+line',
            marker=dict(color=score_style.get("color")),
            name='Score')

        ohlcv_sub = dict(row=1, col=1)
        signal_score_sub = dict(row=2, col=1)
        subplot_layout = dict(rows=2, cols=1)

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
            x0=scores.index.min(), y0=self.sell_threshold,
            x1=scores.index.max(), y1=self.sell_threshold,
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
    
    pm: PredictModelBase = \
        pydantic.Field(PredictModelBase(), description="Buy/sell predict model")

    @property
    def bw_length(self):
        return self.pm.bw_length

    def fit(self, ohlcv_df, **kwrds):
        self.pm.fit(ohlcv_df, **kwrds)
    
    def predict(self, ohlcv_df, **kwrds):
        signal_score = self.pm.predict(ohlcv_df, **kwrds)
        return self.compute_signal(signal_score)

    
class DM2ML(DMBase):
    
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

        buy_score = self.pm_buy.predict(ohlcv_df, **kwrds)
        sell_score = self.pm_sell.predict(ohlcv_df, **kwrds)

        signal_score = buy_score - sell_score

        return self.compute_signal(signal_score)
