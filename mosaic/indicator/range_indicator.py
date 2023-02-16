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


class RangeIndexIndicator(IndicatorOHLCV):

    window: int = Field(
        0, description="Past time window to compute volume levels")
    levels: typing.List[float] = Field(
        [0.5], description="Positive level bins")
    indic_fmt: str = Field(
        "RI", description="Indicator name format")
    indic_d_fmt: str = Field(
        "{indic_name}d", description="Discrete indicator name format")

    @property
    def history_bw(self):
        return self.window

    @property
    def indic_name(self):
        return self.indic_fmt.format(window=self.window,
                                     levels=self.levels)

    @property
    def indic_d_name(self):
        return self.indic_d_fmt.format(
            indic_name=self.indic_name,
            window=self.window,
            levels=self.levels)

    @property
    def indic_d_names(self):
        return [self.indic_d_name]

    @property
    def var_close_min(self):
        return self.indic_name + "_cmin"

    @property
    def var_close_max(self):
        return self.indic_name + "_cmax"

    @property
    def levels_all(self):
        return [-1] + [-l for l in reversed(sorted(self.levels))] \
            + sorted(self.levels) + [1]

    @property
    def labels(self):
        nb_pos_bins = len(self.levels)

        return [f"{k + 1 if k > 0 else ''}-" for k in reversed(range(nb_pos_bins))] + \
            ["~"] + \
            [f"{k + 1 if k > 0 else ''}+" for k in range(nb_pos_bins)]

    def compute(self, ohlcv_df, lag=None, discrete_only=False):
        """Generalized hammer (GH) indicator"""

        # OHLCV variable identification
        var_close = self.ohlcv_names.get("close", "close")

        indic_df = pd.DataFrame(index=ohlcv_df.index,
                                columns=[self.indic_name,
                                         self.indic_d_name])

        data_close = ohlcv_df[var_close]
        data_close_roll = data_close.rolling(self.window)

        indic_df[self.var_close_min] = data_close_roll.min()
        indic_df[self.var_close_max] = data_close_roll.max()

        close_range = indic_df[self.var_close_max] - \
            indic_df[self.var_close_min]

        indic_df[self.indic_name] = \
            2*(data_close -
               indic_df[self.var_close_min]).div(close_range) - 1
        indic_df[self.indic_d_name] = pd.cut(indic_df[self.indic_name],
                                             bins=self.levels_all,
                                             labels=self.labels,
                                             include_lowest=True)

        if discrete_only:
            indic_df = indic_df[self.indic_d_names]
            
        return self.apply_lag(indic_df, lag=lag)

    def plotly(self, ohlcv_df, layout={}, ret_indic=False, **params):

        var_open = self.ohlcv_names.get("open", "open")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_close = self.ohlcv_names.get("close", "close")

        indic_df = self.compute(ohlcv_df, lag=0).reset_index().dropna()

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
            y=indic_df[self.var_close_max],
            name=self.var_close_max,
            mode='lines',
            line_color=color_indic,
            line_dash="dot"
        ),
            row=1, col=1)

        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=indic_df[self.var_close_min],
            name=self.var_close_min,
            mode='lines',
            line_color=color_indic,
            line_dash="dot"
        ),
            row=1, col=1)

        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=indic_df[self.indic_name],
            name=self.indic_name,
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
            return fig, indic_df
        else:
            return fig


class SRIIndicator(RangeIndexIndicator):
    """Support range index"""
    window: int = Field(
        0, description="Past time window to compute volume levels")
    indic_fmt: str = Field(
        "SRI", description="Indicator name format")
    indic_d_fmt: str = Field(
        "{indic_name}d", description="Discrete indicator name format")
    hits_levels: typing.List[float] = Field(
        [2, 4], description="Range hits levels")
    low_str: str = Field(
        "low", description="Lower range bound name")
    high_str: str = Field(
        "high", description="Higher range bound name")
    hits_fmt: str = Field(
        "{indic_name}_nhits_{hits_str}", description="Range hit indicator name format")
    hits_d_fmt: str = Field(
        "{indic_name}d_nhits_{hits_str}", description="Discrete range hit indicator name format")

    @property
    def indic_d_names(self):
        return super().indic_d_names + [self.var_nhits_d_low, self.var_nhits_d_high]

    @property
    def hits_d_labels(self):
        return [f"{int(self.hits_levels[0])-1}-"] + \
            [f"{int(x)}-{int(y)-1}"
             for x, y in zip(self.hits_levels[:-1], self.hits_levels[1:])] + \
            [f"{int(self.hits_levels[-1])}+"]

    @property
    def var_nhits_low(self):
        return self.hits_fmt.format(indic_name=self.indic_name,
                                    hits_str=self.low_str)

    @property
    def var_nhits_high(self):
        return self.hits_fmt.format(indic_name=self.indic_name,
                                    hits_str=self.high_str)

    @property
    def var_nhits_d_low(self):
        return self.hits_d_fmt.format(indic_name=self.indic_name,
                                      hits_str=self.low_str)

    @property
    def var_nhits_d_high(self):
        return self.hits_d_fmt.format(indic_name=self.indic_name,
                                      hits_str=self.high_str)

    def compute(self, ohlcv_df, lag=None, discrete_only=False):
        """Compute method"""

        # OHLCV variable identification
        var_low = self.ohlcv_names.get("low", "low")
        var_high = self.ohlcv_names.get("high", "high")

        indic_df = super().compute(ohlcv_df, lag=0)
        
        ohlcv_low_shift_df = pd.concat([ohlcv_df[var_low].shift(i).rename(i)
                                        for i in range(self.window)], axis=1)
        indic_bmin_dup_df = pd.concat([indic_df[self.var_close_min].rename(i)
                                       for i in range(self.window)], axis=1)
        indic_df[self.var_nhits_low] = \
            (ohlcv_low_shift_df < indic_bmin_dup_df).sum(axis=1).astype(float)

        ohlcv_high_shift_df = pd.concat([ohlcv_df[var_high].shift(i).rename(i)
                                        for i in range(self.window)], axis=1)
        indic_bmax_dup_df = pd.concat([indic_df[self.var_close_max].rename(i)
                                       for i in range(self.window)], axis=1)
        indic_df[self.var_nhits_high] = \
            (ohlcv_high_shift_df > indic_bmax_dup_df).sum(axis=1).astype(float)

        hits_bins = [-float("inf")] + \
            [x - 0.5 for x in self.hits_levels] + \
            [float("inf")]
        indic_df[self.var_nhits_d_low] = \
            pd.cut(indic_df[self.var_nhits_low],
                   bins=hits_bins,
                   labels=self.hits_d_labels)
        indic_df[self.var_nhits_d_high] = \
            pd.cut(indic_df[self.var_nhits_high],
                   bins=hits_bins,
                   labels=self.hits_d_labels)

        if discrete_only:
            indic_df = indic_df[self.indic_d_names]

        return self.apply_lag(indic_df, lag=lag)

    def compute_nhits_low_point(self, bmin, ohlcv_low_window):
        """Helpers for original slow compute method"""

        return np.nan if np.isnan(bmin) \
            else (ohlcv_low_window < bmin).sum()

    def compute_nhits_high_point(self, bmax, ohlcv_high_window):
        """Helpers for original slow compute method"""
        return np.nan if np.isnan(bmax) \
            else (ohlcv_high_window > bmax).sum()

    def plotly(self, ohlcv_df, layout={}, ret_indic=False, **params):

        fig, indic_df = super().plotly(ohlcv_df, layout=layout, ret_indic=True, **params)

        hits_color_palette = \
            px.colors.sample_colorscale(
                px.colors.sequential.Plasma, len(self.hits_d_labels))

        hits_hovertemplate = \
            "#Hits: %{customdata[0]} | %{customdata[1]}"

        hits_min_marker_color = \
            [hits_color_palette[i]
             for i in indic_df[self.var_nhits_d_low].cat.codes]
        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=indic_df[self.var_close_min],
            name=self.var_nhits_low,
            mode='markers',
            showlegend=False,
            marker_color=hits_min_marker_color,
            marker_size=4,
            customdata=indic_df[[self.var_nhits_low, self.var_nhits_d_low]],
            hovertemplate=hits_hovertemplate),
            row=1, col=1)

        hits_max_marker_color = \
            [hits_color_palette[i]
             for i in indic_df[self.var_nhits_d_high].cat.codes]
        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=indic_df[self.var_close_max],
            name=self.var_nhits_high,
            mode='markers',
            showlegend=False,
            marker_color=hits_max_marker_color,
            marker_size=4,
            customdata=indic_df[[self.var_nhits_high, self.var_nhits_d_high]],
            hovertemplate=hits_hovertemplate),
            row=1, col=1)

        return fig
