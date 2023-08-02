from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
import typing
import pydantic
from .bot_base import BotBase
import warnings
import sys
#from ..decision_model.dm_long import DMLongOptimizer
import pkg_resources
import numpy as np
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

from ..utils import compute_combinations, ValueNeighborhood
import tqdm

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')

class BotLong(BotBase):
    
    def compute_trades_test(self,
                            fees=0, **kwrds):

        # Cleaned signals : Fill NaN forward then fill NaN with 0 to deal with first NaNs
        signals = self.signals.fillna(method="ffill").fillna(0)
        
        # Drop consecutive duplicates to keep only buy and sell times
        signals_dt = signals.loc[signals.shift() != signals]
        # Manage first timestamp and drop it if 0 to keep buy -> sell sequences
        if signals_dt.iloc[0] == 0:
            signals_dt = signals_dt.iloc[1:]

        idx_buy = signals_dt.index[signals_dt == 1]
        idx_sell = signals_dt.index[signals_dt != 1]
        if len(idx_buy) != len(idx_sell):
            idx_sell = idx_sell.append(pd.DatetimeIndex([self.ohlcv_df.index[-1]]))
        
        var_d = {var: self.ohlcv_names.get(var, var)
                 for var in ["open", "low", "high", "close"]}

        buy_sell_time_df = \
            pd.concat([idx_buy.rename("buy_time")
                       .to_series()
                       .reset_index(drop=True),
                       idx_sell.rename("sell_time")
                       .to_series()
                       .reset_index(drop=True)], axis=1)

        # if buy_sell_time_df["sell_time"].iloc[-1] is pd.NaT:
        #     buy_sell_time_df["sell_time"].iloc[-1] = ohlcv_df.index[-1]
        
        buy_sell_time_df["trade_duration"] = \
            buy_sell_time_df["sell_time"] - buy_sell_time_df["buy_time"]

        buy_sell_time_df["time_from_last_trade"] = \
            buy_sell_time_df["buy_time"] - buy_sell_time_df["sell_time"].shift(1)

        trades_df_list = [buy_sell_time_df]

        # amount_base = \
        #     ohlcv_df[var_buy_ohlcv]\
        #     .loc[idx_buy].rename(var_buy_price)\
        #                  .reset_index(drop=True)
        
        for var_buy, var_sell in [("open", "open"),
                                  ("high", "low")]:

            var_buy_ohlcv = var_d[var_buy]
            var_sell_ohlcv = var_d[var_sell]

            var_buy_price = f"buy_{var_buy}"
            var_sell_price = f"sell_{var_sell}"
            var_returns = f"returns_{var_buy}_{var_sell}"
            #var_returns_fees = f"{var_returns}_fees"
            var_returns_1 = f"returns1_{var_buy}_{var_sell}"
            #var_returns_1_fees = f"{var_returns_1}_fees"

            buy_price = \
                self.ohlcv_df[var_buy_ohlcv]\
                .loc[idx_buy].rename(var_buy_price)\
                             .reset_index(drop=True)

            # amount_base = \
            #     ohlcv_df[var_buy_ohlcv]\
            #         .loc[idx_buy].rename(var_buy_price)\
            #                      .reset_index(drop=True)

            sell_price = \
                self.ohlcv_df[var_sell_ohlcv]\
                .loc[idx_sell].rename(var_sell_price)\
                              .reset_index(drop=True)

            # amount_quote
            
            returns = ((sell_price*((1 - fees)**2)/buy_price) - 1)\
                .rename(var_returns)

            # returns_fees = ((sell_price*fees/buy_price) - 1)\
            #     .rename(var_returns_fees)

            returns_1 = (returns + 1).rename(var_returns_1)

            # returns_1_fees = (returns_fees + 1)\
            #     .rename(var_returns_1_fees)

            trades_df = \
                pd.concat([buy_price, sell_price,
                           returns, returns_1],
                          axis=1)

            trades_df_list.append(trades_df)

        self.trades_test = pd.concat(trades_df_list, axis=1)

            #self.evaluate()

    def plotly_test(self, **kwrds):

        var_open = self.ohlcv_names.get("open", "open")
        var_low = self.ohlcv_names.get("low", "low")
        var_high = self.ohlcv_names.get("high", "high")
        var_close = self.ohlcv_names.get("close", "close")

        # var_price = bt_results["var_buy_on"]
        
        # orders_df = bt_results["orders_df"]
        # bt_eval_indic, bt_eval_raw = backtest_eval(data_df, bt_results)

        #ipdb.set_trace()
        # Styling plots
        asset_customdata = \
            list(self.ohlcv_df[[f"{var_open}",
                                f"{var_high}",
                                f"{var_low}",
                                f"{var_close}",
                                ]].to_numpy())

        asset_hovertemplate = \
            '<b>Time</b>: %{x}<br>'\
            '<b>Open</b>: %{customdata[0]:.2f}<br>'\
            '<b>High</b>: %{customdata[1]:.2f}<br>'\
            '<b>Low</b>: %{customdata[2]:.2f}<br>'\
            '<b>Close</b>: %{customdata[3]:.2f}<br>'\

        perf_hovertemplate = \
            '<b>Time</b>: %{x}<br>'\
            '<b>Performance</b>: %{y}<br>'\

        trades_customdata = \
            list(self.trades_test[
                ["buy_time",
                 f"buy_{var_open}",
                 f"buy_{var_high}",
                 "sell_time",
                 f"sell_{var_open}",
                 f"sell_{var_low}",
                 f"returns_{var_open}_{var_open}",
                 f"returns_{var_high}_{var_low}",
                 ]].to_numpy())

        trades_info_hovertemplate = \
            '<b>Buy time</b>: %{customdata[0]}<br>'\
            '<b>Buy open-price</b>: %{customdata[1]:.2f}<br>'\
            '<b>Buy high-price</b>: %{customdata[2]:.2f}<br>'\
            '<b>Sell time</b>: %{customdata[3]}<br>'\
            '<b>Sell open-price</b>: %{customdata[4]:.2f}<br>'\
            '<b>Sell low-price</b>: %{customdata[5]:.2f}<br>'\
            '<b>Returns open-open</b>: %{customdata[6]:.5f}<br>'\
            '<b>Returns high-low</b>: %{customdata[7]:.5f}<br>'\

        
        trades_buy_hovertemplate = \
            '<b>Buy signal</b><br><br>' + trades_info_hovertemplate

        trades_sell_hovertemplate = \
            '<b>Sell signal</b><br><br>' + trades_info_hovertemplate

        asset_style = dict(
            marker_color="darkgray",
            marker_line_width=1,
            marker_size=5,
            customdata=asset_customdata,
            hovertemplate=asset_hovertemplate,
        )

        trades_maker_color = \
            pd.Series("green", index=self.trades_test.index)
        # trades_test["sell_marker_color"] = "green"
        idx_loss = self.trades_test[f"returns_{var_open}_{var_open}"] < 0
        idx_loss_gain = \
            (self.trades_test[f"returns_{var_open}_{var_open}"] > 0) & \
            (self.trades_test[f"returns_{var_high}_{var_low}"] < 0)
        trades_maker_color.loc[idx_loss] = "red"
        trades_maker_color.loc[idx_loss_gain] = "salmon"

        buy_signal_style = dict(
            marker_symbol="triangle-right",
            marker_line_color="black",
            marker_line_width=1,
            marker_color=trades_maker_color,
            marker_size=10,
            customdata=trades_customdata,
            hovertemplate=trades_buy_hovertemplate,
        )

        sell_signal_style = dict(**buy_signal_style)
        sell_signal_style["marker_symbol"] = "triangle-left"
        sell_signal_style["hovertemplate"] = trades_sell_hovertemplate
        
        perf_open_open_marker_color = \
            pd.Series("green", index=self.trades_test.index)
        idx_loss = self.trades_test[f"returns_{var_open}_{var_open}"] < 0
        perf_open_open_marker_color.loc[idx_loss] = "red"

        # bt_eval_raw["ret_strat_orders"]
        perf_open_open_style = dict(
            marker_line_width=1,
            marker_size=6,
            line_color="orange",
            marker_color=perf_open_open_marker_color,
            hovertemplate=perf_hovertemplate,
        )

        perf_high_low_marker_color = \
            pd.Series("green", index=self.trades_test.index)
        idx_loss = self.trades_test[f"returns_{var_high}_{var_low}"] < 0
        perf_high_low_marker_color.loc[idx_loss] = "red"

        # bt_eval_raw["ret_strat_orders"]
        perf_high_low_style = dict(
            marker_line_width=1,
            marker_size=6,
            line_color="violet",
            marker_color=perf_high_low_marker_color,
            customdata=trades_customdata,
            hovertemplate=perf_hovertemplate,
        )

        perf_asset_style = dict(
            marker_line_width=2,
            marker_size=0,
            opacity=0.8,
            line_color="darkgray",
            hovertemplate=perf_hovertemplate,
        )
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=('Asset cotation',
                            'Bot performance',
                            ),
            # column_widths=[0.7, 0.3],
            # specs=[[{"type": "xy"}, {"type": "xy"}],
            #        [{"type": "xy"}, {"type": "domain"}]],
        )

        ohlcv_trace = go.Scatter(
                x=self.ohlcv_df.index, y=self.ohlcv_df[var_open],
                mode='lines',
                name=f'Asset {var_open} price',
                **asset_style)
        fig.add_trace(ohlcv_trace, row=1, col=1)

        buy_signals_trace = \
            go.Scatter(x=self.trades_test["buy_time"],
                       y=self.trades_test[f"buy_{var_open}"],
                       mode='markers',
                       name='Buy signals',
                       **buy_signal_style)
        fig.add_trace(buy_signals_trace, row=1, col=1)

        sell_signals_trace = \
            go.Scatter(x=self.trades_test["sell_time"],
                       y=self.trades_test[f"sell_{var_open}"],
                       mode='markers',
                       name='Sell signals',
                       **sell_signal_style)
        fig.add_trace(sell_signals_trace, row=1, col=1)

        asset_norm = self.ohlcv_df[var_close]/self.ohlcv_df[var_open].iloc[0]
        perf_asset_trace = \
            go.Scatter(x=asset_norm.index,
                       y=asset_norm,
                       mode='lines',
                       name='Asset performance',
                       **perf_asset_style)
        fig.add_trace(perf_asset_trace, row=2, col=1)

        if self.perf_test.nb_trades > 0:
            perf_open_open_trace = \
                go.Scatter(x=self.trades_test["sell_time"],
                           y=self.trades_test[f"perf_{var_open}_{var_open}"],
                           mode='lines',
                           name='Strategy open-open performance',
                           **perf_open_open_style)
            fig.add_trace(perf_open_open_trace, row=2, col=1)

            perf_high_low_trace = \
                go.Scatter(x=self.trades_test["sell_time"],
                           y=self.trades_test[f"perf_{var_high}_{var_low}"],
                           mode='lines',
                           name='Strategy high-low performance',
                           **perf_high_low_style)
            fig.add_trace(perf_high_low_trace, row=2, col=1)    

        return fig

    def dm_tuning_bf_basic(self, ohlcv_df,
                           dm_params={},
                           bot_params={},
                           run_test_params={},
                           progress_mode=True,
                           target_measure="perf_high_low",
                           nb_trades_min=15,
                           returns_tuning_df=False,
                           **kwrds,
                           ):
        """DM model brute force tuning"""

        dm_params_list = compute_combinations(**dm_params)

        bot_eval_list = []
        dm_cls = self.decision_model.__class__
        for params in tqdm.tqdm(dm_params_list,
                                disable=not progress_mode,
                                desc="Parameters",
                                ):

            bot_cur = self.__class__(
                decision_model=dm_cls(params=params),
                **bot_params,
            )

            bot_cur.run_test(ohlcv_df, **run_test_params)

            bot_eval_list.append(dict(params, **bot_cur.perf_test.dict()))

        tuning_df = \
            pd.DataFrame.from_records(bot_eval_list)\
                        .sort_values(by=target_measure,
                                     ascending=False)

        idx_const_nb_trades = \
            tuning_df["nb_trades"] > nb_trades_min

        tuning_bis_df = \
            tuning_df.loc[idx_const_nb_trades]

        if len(tuning_bis_df) > 0:
            dm_params_opt = \
                tuning_bis_df.iloc[0]\
                             .loc[dm_params.keys()]\
                             .to_dict()
        else:
            warnings.warn("Tuning DM parameters failed, "
                          "Returns current DM parameters",
                          category=UserWarning)
            dm_params_opt = self.decision_model.params

        if returns_tuning_df:
            return dm_cls(params=dm_params_opt), tuning_df
        else:
            return dm_cls(params=dm_params_opt)

    def dm_tuning_bf_neighbor(self, ohlcv_df,
                              neighbor_specs: typing.Dict[str, ValueNeighborhood] = {},
                              **kwrds):

        dm_params = \
            self.decision_model.params.domain_from_neighbor(neighbor_specs)
        
        #ipdb.set_trace()
        return self.dm_tuning_bf_basic(ohlcv_df,
                                       dm_params=dm_params,
                                       **kwrds)

    def dm_tuning_sa(self, ohlcv_df,
                     neighbor_specs: typing.Dict[str, ValueNeighborhood] = {},
                     cooling_rate=0.99,
                     iter_max=1000,
                     nchanges=None,
                     rand_seed=None,
                     bot_params={},
                     run_test_params={},
                     progress_mode=False,
                     verbose_mode=False,
                     target_measure="perf_high_low",
                     returns_tuning_df=False,
                     **kwrds,
                     ):
        """DM model SA tuning"""
        #ipdb.set_trace()
        np.random.seed(rand_seed)
        
        dm_cls = self.decision_model.__class__

        def obj_fun(params):
            bot_cur = self.__class__(
                decision_model=dm_cls(params=params),
                **bot_params,
            )

            bot_cur.run_test(ohlcv_df, **run_test_params)
            perf = getattr(bot_cur.perf_test, target_measure)
            return perf if perf else 0, bot_cur
            
        params_cur = self.decision_model.params.copy()
        params_best = params_cur.copy()
        obj_value_cur, tmp = obj_fun(params_cur)
        obj_value_best = obj_value_cur
        cooling_rate_cur = 1.0
        
        bot_eval_list = []
        for iter in tqdm.tqdm(range(iter_max),
                              disable=not progress_mode,
                              desc="SA Iteration",
                              ):

            # Choose random neighbor
            params_new = \
                params_cur.random_from_neighbor(
                    neighbor_specs=neighbor_specs,
                    nchanges=nchanges)

            obj_value_new, bot_new = obj_fun(params_new)
            obj_value_ret = obj_value_new/obj_value_cur
            obj_value_diff = obj_value_new - obj_value_cur

            # Jump criterion
            cooling_rate_cur *= cooling_rate
            jump_crit = 1/(1 + np.exp(obj_value_diff/cooling_rate_cur))
            
            # Metropolis Hasting criterion
            # Reduce the temperature
            # temperature *= cooling_rate
            # jump_crit = np.exp(obj_value_ret/temperature)

            params_jump_accepted = False
            
            if obj_value_new > obj_value_cur:
                params_cur = params_new.copy()
                obj_value_cur = obj_value_new
                if obj_value_cur > obj_value_best:
                    params_best = params_cur.copy()
                    obj_value_best = obj_value_cur
            else:
                # Metropolis Hasting criterion
                rand_num = np.random.rand()
                params_jump_accepted = jump_crit < rand_num
                if params_jump_accepted:
                    params_cur = params_new.copy()

            if verbose_mode:
                log_str = f"[SA Tuning] #Iter = {iter:6d}/{iter_max:6d} | JC = {jump_crit:7.3e} | Obj. cur. = {obj_value_cur:5.3f} | Obj. best. = {obj_value_best:5.3f} {'*'*params_jump_accepted}\n\n"\
                    f"Current parameters:\n{params_cur}\n\n"\
                    f"Best parameters:\n{params_best}\n\n"
                sys.stdout.write(log_str)

            bot_eval_list.append(dict(params_cur, **bot_new.perf_test.dict()))


        #ipdb.set_trace()

        tuning_df = \
            pd.DataFrame.from_records(bot_eval_list)\
                        .sort_values(by=target_measure,
                                     ascending=False)

        if returns_tuning_df:
            return dm_cls(params=params_best), tuning_df
        else:
            return dm_cls(params=params_best)

