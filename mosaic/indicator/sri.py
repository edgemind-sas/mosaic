from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import typing
from pydantic import Field
from .indicator import IndicatorOHLCV
import pkg_resources
import numpy as np
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


class RangeIndex(IndicatorOHLCV):

    length: int = Field(
        1, description="Window to compute range", ge=1)
    var_ri: str = Field(
        "close", description="Variable to compute range index")
    var_range_min: str = Field(
        "close", description="Variable to compute range lower bound")
    var_range_max: str = Field(
        "close", description="Variable to compute range higher bound")

    @property
    def bw_length(self):
        return super().bw_length + self.length

    @property
    def names_map(self):
        """Indicator names format mapping: To be overloaded"""
        return {
            "ri": f"RI_{self.length}",
        }

    def compute(self, ohlcv_df, return_range=False, **kwrds):
        """Compute indicator"""

        super().compute(ohlcv_df, **kwrds)

        indic_df = pd.DataFrame(index=ohlcv_df.index)

        data_var_ri = ohlcv_df[self.ohlcv_names.get(self.var_ri)]
        
        data_range_min = ohlcv_df[self.ohlcv_names.get(self.var_range_min)]\
            .rolling(self.length).min()
        data_range_max = ohlcv_df[self.ohlcv_names.get(self.var_range_max)]\
            .rolling(self.length).max()

        data_range = data_range_max - data_range_min

        idx_range_0 = data_range == 0

        indic_df[self.names("ri")] = 0
        
        indic_df.loc[~idx_range_0, self.names("ri")] = \
            2*(data_var_ri.loc[~idx_range_0] -
               data_range_min.loc[~idx_range_0]).div(data_range.loc[~idx_range_0]) - 1

        if return_range:
            return indic_df, data_range_min, data_range_max
        else:
            return indic_df

    def plotly(self, ohlcv_df, layout={}, ret_indic=False, **params):

        var_open = self.ohlcv_names.get("open", "open")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_close = self.ohlcv_names.get("close", "close")

        indic_df, data_range_min, data_range_max = \
            self.compute(ohlcv_df, return_range=True).reset_index().dropna()

        fig = make_subplots(rows=2, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.02)

        fig.add_trace(go.Candlestick(x=ohlcv_df.index,
                                     open=ohlcv_df[var_open],
                                     high=ohlcv_df[var_high],
                                     low=ohlcv_df[var_low],
                                     close=ohlcv_df[var_close], name="OHLC"),
                      row=1, col=1)

        color_indic = px.colors.qualitative.T10[0]
        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=data_range_max,
            name=self.var_range_max,
            mode='lines',
            line_color=color_indic,
            line_dash="dot"
        ),
            row=1, col=1)

        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=data_range_min,
            name=self.var_range_min,
            mode='lines',
            line_color=color_indic,
            line_dash="dot"
        ),
            row=1, col=1)

        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=indic_df[self.names("ri")],
            name=self.names("ri"),
            mode='markers+lines',
            line_color=color_indic
        ),
            row=2, col=1)

        layout["xaxis_rangeslider_visible"] = False
        fig.update_layout(**layout)

        # include a go.Bar trace for volumes
        # fig2 = px.line(indic_df,
        #                x="time",
        #                y=self.indic_name,
        #                markers=True)

        # # fig2.update_traces(mode="lines+markers")
        # fig.add_trace(fig2.data[0],
        #               row=2, col=1)

        if ret_indic:
            return fig, indic_df, data_range_min, data_range_max
        else:
            return fig


class SRI(RangeIndex):
    """Support range index"""
    var_hit_min: str = Field(
        "low", description="Variable used to calculate the number of crossings of the range lower bound")
    var_hit_max: str = Field(
        "high", description="Variable used to calculate the number of crossings of the range higher bound")

    @property
    def names_map(self):
        """Indicator names format mapping: To be overloaded"""
        return dict(super().names_map, **{
            "hl": f"SRI_HL_{self.length}",
            "hh": f"SRI_HH_{self.length}",
        })

    def compute(self, ohlcv_df, **kwrds):
        """Compute method"""

        # OHLCV variable identification
        var_hit_low = self.ohlcv_names.get(self.var_hit_min)
        var_hit_high = self.ohlcv_names.get(self.var_hit_max)

        indic_df, data_range_min, data_range_max = \
            super().compute(ohlcv_df, return_range=True, **kwrds)

        ohlcv_low_shift_df = \
            pd.concat([ohlcv_df[var_hit_low].shift(i).rename(i)
                       for i in range(self.length)], axis=1)
        indic_bmin_dup_df = \
            pd.concat([data_range_min.rename(i)
                       for i in range(self.length)], axis=1)
        indic_df[self.names("hl")] = \
            (ohlcv_low_shift_df < indic_bmin_dup_df).sum(axis=1).astype(float)

        ohlcv_high_shift_df = \
            pd.concat([ohlcv_df[var_hit_high].shift(i).rename(i)
                       for i in range(self.length)], axis=1)
        indic_bmax_dup_df = \
            pd.concat([data_range_max.rename(i)
                       for i in range(self.length)], axis=1)
        indic_df[self.names("hh")] = \
            (ohlcv_high_shift_df > indic_bmax_dup_df).sum(axis=1).astype(float)

        return indic_df

    def plotly(self, ohlcv_df, layout={}, ret_indic=False, **params):

        fig, indic_df, data_range_min, data_range_max = \
            super().plotly(ohlcv_df, layout=layout, ret_indic=True, **params)

        hits_hovertemplate = \
            "#Hits: %{customdata[0]}"

        color_indic = px.colors.qualitative.T10[0]

        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=data_range_min,
            name=self.names("hl"),
            mode='markers',
            showlegend=False,
            marker_color=indic_df[[self.names("hl")]],
            marker_size=4,
            customdata=indic_df[[self.names("hl")]],
            hovertemplate=hits_hovertemplate),
            row=1, col=1)

        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=data_range_max,
            name=self.names("hh"),
            mode='markers',
            showlegend=False,
            marker_color=indic_df[[self.names("hh")]],
            marker_size=4,
            customdata=indic_df[[self.names("hh")]],
            hovertemplate=hits_hovertemplate),
            row=1, col=1)

        return fig
