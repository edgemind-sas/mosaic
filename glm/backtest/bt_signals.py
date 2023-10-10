from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import typing
import pydantic
from .bt_base import BTBase
import pkg_resources
import numpy as np
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')


class BTLong(BTBase):

    def compute_orders(self, **kwrds):

        if not self.dm_config.fit_horizon:
            return self.decision_model.compute(self.ohlcv_df, **kwrds)
        
        fit_horizon = 0 if not self.dm_config.fit_horizon \
            else self.dm_config.fit_horizon

        # Number of prediction to make
        nb_predictions = len(self.ohlcv_df) - fit_horizon
        
        predict_horizon = \
            nb_predictions \
            if not self.dm_config.predict_horizon \
            else self.dm_config.predict_horizon
        
        idx_fit = pd.Series(False, index=self.ohlcv_df.index)
        idx_fit.iloc[:fit_horizon] = True

        idx_predict = pd.Series(False, index=self.ohlcv_df.index)
        idx_predict.iloc[fit_horizon:(fit_horizon + predict_horizon)] = True

        nb_shifts = np.ceil(nb_predictions/predict_horizon)

        for i_shift in range(nb_shifts):

            ohlcv_fit = self.ohlcv_df.loc[idx_fit]

            self.decision_model.fit(ohlcv_fit, **kwrds)
            
            idx_fit = idx_fit.shift(predict_horizon).fillna(False)
            idx_predict = idx_predict.shift(predict_horizon).fillna(False)
            
        
        ipdb.set_trace()
        
            
        
    def run(self, **kwrds):

        #orders = self.decision_model.compute(self.ohlcv_df, **kwrds)
        
        orders = \
            self.compute_orders(**kwrds)


        # Drop consecutive duplicates to keep only buy and sell times
        orders_dt = orders.loc[orders.shift() != orders]
        # Manage first timestamp and drop it if 0 to keep buy -> sell sequences
        if orders_dt.iloc[0] == 0:
            orders_dt = orders_dt.iloc[1:]

        idx_buy = orders_dt.index[orders_dt == 1]
        idx_sell = orders_dt.index[orders_dt != 1]
        if len(idx_buy) != len(idx_sell):
            idx_sell = idx_sell.append(pd.DatetimeIndex([self.ohlcv_df.index[-1]]))
        
        var_open = self.ohlcv_names.get("open", "open")
        var_low = self.ohlcv_names.get("low", "low")
        var_high = self.ohlcv_names.get("high", "high")

        buy_sell_time_df = \
            pd.concat([idx_buy.rename("buy_time")
                       .to_series()
                       .reset_index(drop=True),
                       idx_sell.rename("sell_time")
                       .to_series()
                       .reset_index(drop=True)], axis=1)

        # if buy_sell_time_df["sell_time"].iloc[-1] is pd.NaT:
        #     buy_sell_time_df["sell_time"].iloc[-1] = self.ohlcv_df.index[-1]
        
        buy_sell_time_df["trade_duration"] = \
            buy_sell_time_df["sell_time"] - buy_sell_time_df["buy_time"]

        buy_sell_time_df["time_from_last_trade"] = \
            buy_sell_time_df["buy_time"] - buy_sell_time_df["sell_time"].shift(1)

        trades_df_list = [buy_sell_time_df]

        fees = (1 - self.fees_buy)*(1 - self.fees_sell)

        for var_buy, var_sell in [(var_open, var_open),
                                  (var_high, var_low)]:
            
            var_buy_price = f"buy_{var_buy}"
            var_sell_price = f"sell_{var_sell}"
            var_returns = f"returns_{var_buy}_{var_sell}"
            var_returns_fees = f"{var_returns}_fees"
            var_returns_1 = f"returns1_{var_buy}_{var_sell}"
            var_returns_1_fees = f"{var_returns_1}_fees"
            
            buy_price = \
                self.ohlcv_df[var_buy].loc[idx_buy].rename(var_buy_price)\
                                                   .reset_index(drop=True)
            sell_price = \
                self.ohlcv_df[var_sell].loc[idx_sell].rename(var_sell_price)\
                                                     .reset_index(drop=True)
            returns = ((sell_price/buy_price) - 1)\
                .rename(var_returns)

            returns_fees = ((sell_price*fees/buy_price) - 1)\
                .rename(var_returns_fees)

            returns_1 = (returns + 1).rename(var_returns_1)

            returns_1_fees = (returns_fees + 1)\
                .rename(var_returns_1_fees)

            trades_df = \
                pd.concat([buy_price, sell_price,
                           returns, returns_fees,
                           returns_1, returns_1_fees],
                          axis=1)

            trades_df_list.append(trades_df)

        self.trades_df = pd.concat(trades_df_list, axis=1)

        self.evaluate()


    def plotly(self, **kwrds):

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
            list(self.trades_df[["buy_time",
                                 f"buy_{var_open}",
                                 f"buy_{var_high}",
                                 "sell_time",
                                 f"sell_{var_open}",
                                 f"sell_{var_low}",
                                 f"returns_{var_open}_{var_open}_fees",
                                 f"returns_{var_high}_{var_low}_fees",
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
            pd.Series("green", index=self.trades_df.index)
        # trades_df["sell_marker_color"] = "green"
        idx_loss = self.trades_df[f"returns_{var_open}_{var_open}_fees"] < 0
        idx_loss_gain = \
            (self.trades_df[f"returns_{var_open}_{var_open}_fees"] > 0) & \
            (self.trades_df[f"returns_{var_high}_{var_low}_fees"] < 0)
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
            pd.Series("green", index=self.trades_df.index)
        idx_loss = self.trades_df[f"returns_{var_open}_{var_open}_fees"] < 0
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
            pd.Series("green", index=self.trades_df.index)
        idx_loss = self.trades_df[f"returns_{var_high}_{var_low}_fees"] < 0
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
            rows=2, cols=2,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=('Asset cotation',
                            'Returns distribution',
                            'Strategy performance',
                            'Strategy indicators'),
            column_widths=[0.7, 0.3],
            specs=[[{"type": "xy"}, {"type": "xy"}],
                   [{"type": "xy"}, {"type": "domain"}]],
        )

        ohlcv_trace = go.Scatter(
                x=self.ohlcv_df.index, y=self.ohlcv_df[var_open],
                mode='lines',
                name=f'Asset {var_open} price',
                **asset_style)
        fig.add_trace(ohlcv_trace, row=1, col=1)

        buy_signals_trace = \
            go.Scatter(x=self.trades_df["buy_time"],
                       y=self.trades_df[f"buy_{var_open}"],
                       mode='markers',
                       name='Buy signals',
                       **buy_signal_style)
        fig.add_trace(buy_signals_trace, row=1, col=1)

        sell_signals_trace = \
            go.Scatter(x=self.trades_df["sell_time"],
                       y=self.trades_df[f"sell_{var_open}"],
                       mode='markers',
                       name='Sell signals',
                       **sell_signal_style)
        fig.add_trace(sell_signals_trace, row=1, col=1)

        perf_asset_trace = \
            go.Scatter(x=self.asset_norm.index,
                       y=self.asset_norm,
                       mode='lines',
                       name='Asset performance',
                       **perf_asset_style)
        fig.add_trace(perf_asset_trace, row=2, col=1)

        if self.perf.nb_trades > 0:
            perf_open_open_trace = \
                go.Scatter(x=self.trades_df[f"sell_time"],
                           y=self.trades_df[f"perf_{var_open}_{var_open}"],
                           mode='lines',
                           name='Strategy open-open performance',
                           **perf_open_open_style)
            fig.add_trace(perf_open_open_trace, row=2, col=1)

            perf_high_low_trace = \
                go.Scatter(x=self.trades_df[f"sell_time"],
                           y=self.trades_df[f"perf_{var_high}_{var_low}"],
                           mode='lines',
                           name='Strategy high-low performance',
                           **perf_high_low_style)
            fig.add_trace(perf_high_low_trace, row=2, col=1)    

        return fig

    
