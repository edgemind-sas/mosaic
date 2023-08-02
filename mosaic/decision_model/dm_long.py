import pydantic
import typing
import sys
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pkg_resources
from .dm_base import DMBase
#from ..backtest.dm_optim import DMLongOptimizer

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

PandasSeries = typing.TypeVar('pandas.core.frame.Series')
PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')


class DMLong(DMBase):
    
    # orders: PandasSeries = \
    #     pydantic.Field(None, description="Final long orders series")

    # indic_bkd: typing.Any = \
    #     pydantic.Field(None, description="Indicators backends")

    # indic_df: typing.Any = \
    #     pydantic.Field(None, description="Indicators values")
    
    def compute_signals(self, idx_buy, idx_sell, **kwrds):

        signals_raw = pd.Series(index=idx_buy.index,
                                dtype="float",
                                name="signal")

        signals_raw.loc[idx_buy] = 1
        signals_raw.loc[idx_sell] = 0

        return signals_raw
    
    def plotly(self, ohlcv_df,
               ret_signals=False,
               layout={},
               layout_ohlcv={},
               layout_indic={},
               **params):

        signals_raw = self.compute(ohlcv_df, **params)

        buy_style = dict(
            color="#FFD700",
        )
        sell_style = dict(
            color="#C74AFF",
        )
        
        signals_buy = signals_raw.loc[signals_raw == 1]
        signals_buy_trace = go.Scatter(
            x=signals_buy.index,
            y=ohlcv_df.loc[signals_buy.index, "close"],
            mode='markers',
            marker=dict(color=buy_style.get("color")),
            name='buy signals')

        signals_sell = signals_raw.loc[signals_raw == 0]
        signals_sell_trace = go.Scatter(
            x=signals_sell.index,
            y=ohlcv_df.loc[signals_sell.index, "close"],
            mode='markers',
            marker=dict(color=sell_style.get("color")),
            name='sell signals')

        ohlcv_sub = dict(row=1, col=1)
        indic_sub = {}
        if hasattr(self.indic_bkd, "plotly"):
            fig_indic = self.indic_bkd.plotly(ohlcv_df,
                                              layout=layout_indic,
                                              **params)
            subplot_layout = dict(rows=2, cols=1)
            indic_sub = dict(row=2, col=1)
        else:
            subplot_layout = dict(rows=1, cols=1)

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
        fig_sp.add_trace(fig_indic.data[0], **indic_sub)
            
        fig_sp.add_trace(signals_buy_trace, **ohlcv_sub)
        fig_sp.add_trace(signals_sell_trace, **ohlcv_sub)
        if indic_sub:
            try:
                for dt in signals_buy.index:
                    fig_sp.add_shape(
                        type="line",
                        x0=dt, y0=fig_indic.data[0]["y"].min(),
                        x1=dt, y1=fig_indic.data[0]["y"].max(),
                        line=dict(color=buy_style.get("color"),
                                  width=3,
                                  dash="dot"), **indic_sub)

                for dt in signals_sell.index:
                    fig_sp.add_shape(
                        type="line",
                        x0=dt, y0=fig_indic.data[0]["y"].min(),
                        x1=dt, y1=fig_indic.data[0]["y"].max(),
                        line=dict(color=sell_style.get("color"),
                                  width=3,
                                  dash="dot"), **indic_sub)
            except Exception as e:
                sys.stdout.write("Exception in DMLong.plotly while drawing buy/sell vertical lines on indicators plot :", e)

        layout["xaxis_rangeslider_visible"] = False
        fig_sp.update_layout(**layout)

        if ret_signals:
            return fig_sp, signals_raw
        else:
            return fig_sp

        
# class DMLongOptimizer(pydantic.BaseModel):

#     dm_cls: typing.Type[DMLong] = pydantic.Field(
#         ..., description="Decision model")

#     bt_cls: typing.Any = pydantic.Field(
#         ..., description="BT class")

#     # bt_cls: typing.Type[DMLong] = pydantic.Field(
#     #     ..., description="Decision model")
    
#     dm_params: dict = \
#         pydantic.Field({}, description="DM parameters to test")

#     brute_force_df: PandasDataFrame = \
#         pydantic.Field(None, description="Brute force optimization resulting data")

#     def brute_force(self, ohlcv_df,
#                     bt_params={},
#                     progress_mode=True,
#                     target_measure="perf_open_open",
#                     nb_trades_min=15,
#                     ):

#         dm_params_list = compute_combinations(**self.dm_params)

#         bt_eval_list = []
#         for params in tqdm.tqdm(dm_params_list,
#                                 disable=not progress_mode,
#                                 desc="Parameters",
#                                 ):

#             bt_cur = self.bt_cls(
#                 ohlcv_df=ohlcv_df,
#                 decision_model=self.dm_cls(params=params),
#                 **bt_params,
#             )

#             bt_cur.run()

#             bt_eval_list.append(dict(params, **bt_cur.perf.dict()))

#         self.brute_force_df = \
#             pd.DataFrame.from_records(bt_eval_list)\
#                         .sort_values(by=target_measure,
#                                      ascending=False)

#         idx_const_nb_trades = \
#             self.brute_force_df["nb_trades"] > nb_trades_min

#         brute_force_bis_df = \
#             self.brute_force_df.loc[idx_const_nb_trades]

#         dm_params_opt = \
#             brute_force_bis_df.iloc[0]\
#                               .loc[self.dm_params.keys()]\
#                               .to_dict()

#         return self.dm_cls(params=dm_params_opt)
