from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import typing
import pydantic
from . import BTBase
import pkg_resources
import numpy as np
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')

class BTSimple(BTBase):

    def compute_indic(self, ohlcv_df, **kwards):
        
        indic_df_list = [indic_obj.compute(ohlcv_df, discrete_only=True)
                         for indic_obj in self.indicators]

        return pd.concat(indic_df_list, axis=1)
        
    
    def fit(self, ohlcv_df, **kwrds):

        indic_df = self.compute_indic(ohlcv_df)

        self.decision_model.fit(ohlcv_df, indic_df)
            
        
    def compute(self, ohlcv_df, **kwrds):

        self.ohlcv_df = ohlcv_df
        
        self.indic_df = self.compute_indic(self.ohlcv_df)

        self.decisions_df = \
            self.decision_model.compute(self.ohlcv_df,
                                        self.indic_df)

        var_indics = list(self.indic_df.columns)

        self.trades_all_df = pd.concat([self.ohlcv_df,
                                   self.indic_df,
                                   self.decisions_df], axis=1)

        idx_indic_na = self.indic_df.isna().any(axis=1)
        
        self.trades_all_df["buy_price"] = \
            self.trades_all_df[self.ohlcv_names["open"]].copy()
        self.trades_all_df["amount_quote_bet"] = 1
        self.trades_all_df.loc[idx_indic_na, "amount_quote_bet"] = np.nan
        self.trades_all_df["amount_quote"] = -self.trades_all_df["amount_quote_bet"]
        self.trades_all_df["amount_base"] = \
            self.trades_all_df["amount_quote_bet"]\
                .div(self.trades_all_df["buy_price"])\
                *(1-self.fees_factor)
        
        self.trades_all_df["quote_returns"] = \
            self.trades_all_df["sell_price"]*self.trades_all_df["amount_base"]*(1-self.fees_factor)

        trades_all_indic_grp = self.trades_all_df.groupby(var_indics)

        trades_all_exp_df_list = []
        for indic, trades_indic_cur_df in trades_all_indic_grp:
            trades_exp_df = trades_indic_cur_df.reindex(ohlcv_df.index)
            trades_exp_df["amount_quote"] = trades_exp_df["amount_quote"].fillna(0)
            trades_exp_df["amount_base"] = trades_exp_df["amount_base"].fillna(0)

            trades_indic_cur_sell_time_grp = trades_indic_cur_df.groupby("sell_time")
            amount_sold = trades_indic_cur_sell_time_grp["amount_base"].sum()
            quote_returns = trades_indic_cur_sell_time_grp["quote_returns"].sum()

            trades_exp_df.loc[amount_sold.index, "amount_base"] -= amount_sold
            
            trades_exp_df.loc[quote_returns.index, "amount_quote"] += quote_returns

            trades_exp_df["balance_quote"] = trades_exp_df["amount_quote"].fillna(0).cumsum()

            #ipdb.set_trace()
            
            trades_all_exp_df_list.append(trades_exp_df)

        self.trades_all_exp_df = pd.concat(trades_all_exp_df_list, axis=0)


    def to_xlsx(self, filename):

        writer = pd.ExcelWriter(filename,
                                engine='xlsxwriter')

        #ipdb.set_trace()
        trades_all_df = self.trades_all_df.tz_localize(None)
        trades_all_df["sell_time"] = trades_all_df["sell_time"].dt.tz_localize(None)
        trades_all_df.to_excel(writer,
                               sheet_name="Trades all")
        trades_all_exp_df = self.trades_all_exp_df.tz_localize(None)
        trades_all_exp_df["sell_time"] = trades_all_exp_df["sell_time"].dt.tz_localize(None)
        trades_all_exp_df.to_excel(writer,
                                   sheet_name="Trades exp all")
        
        var_indic = list(self.indic_df.columns)
        trades_all_exp_indic_grp = trades_all_exp_df.groupby(var_indic)
        for indic, trades_indic_exp_cur_df in trades_all_exp_indic_grp:

            trades_indic_exp_cur_df.to_excel(writer, sheet_name=str(indic))

        writer.save()

        
        
    def print_summary(self, layout={}, **params):

        var_indic = list(self.indic_df.columns)

        bt_quote_returns_mean = \
            self.trades_all_df.groupby(var_indic)["quote_returns"].mean()
        
        print(bt_quote_returns_mean)

        bt_sell_signal_summary = \
            self.trades_all_df.groupby("sell_signal").agg({"sell_signal": 'size', "quote_returns": "mean"})
        print(bt_sell_signal_summary)

        bt_quote_returns_signal_mean = \
            self.trades_all_df.groupby(var_indic + ["sell_signal"]).agg({"sell_signal": 'size', "quote_returns": "mean"})
        
        print(bt_quote_returns_signal_mean)
        
    # def plot_summary_bis(self, layout={}, **params):

    #     trades_data_var = ["balance_quote"]

    #     var_indic = list(self.indic_df.columns)
    #     trades_data = self.trades_all_exp_df[trades_data_var + var_indic]\
    #                       .dropna()
        
    #     indic_joined = join_obj_columns(trades_data[var_indic])

    #     data_to_plot_df = pd.concat([trades_data, indic_joined], axis=1)\
    #                         .reset_index()

    #     fig = px.line(data_to_plot_df,
    #                   x="time",
    #                   y="balance_quote",
    #                   color=indic_joined.name,
    #                   markers=True)

    #     fig.update_layout(**layout)

    #     return fig

    
    def plot_summary(self, layout={}, **params):

        trades_data_var = ["quote_returns"]

        var_indic = list(self.indic_df.columns)
        trades_data = self.trades_all_df[trades_data_var + var_indic]\
                          .dropna()
        
        indic_joined = join_obj_columns(trades_data[var_indic])

        data_to_plot_df = pd.concat([trades_data, indic_joined], axis=1)\
                            .reset_index()

        fig = px.line(data_to_plot_df,
                      x="time",
                      y="quote_returns",
                      color=indic_joined.name,
                      markers=True)

        fig.update_layout(**layout)

        return fig

    
    #ipdb.set_trace()
        

