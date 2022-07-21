from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import typing
from pydantic import Field
from .indicator import IndicatorOHLCV
import pkg_resources
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
    def var_close_min(self):
        return self.indic_name + "_min"

    @property
    def var_close_max(self):
        return self.indic_name + "_max"

    @property
    def levels_all(self):
        return [-1] + [-l for l in reversed(sorted(self.levels))] \
            + sorted(self.levels) + [1]

    @property
    def labels(self):
        nb_pos_bins = len(self.levels)

        return [f"{k + 1 if k > 0 else ''}-" for k in reversed(range(nb_pos_bins))] + \
            ["="] + \
            [f"{k + 1 if k > 0 else ''}+" for k in range(nb_pos_bins)]

    def compute(self, ohlcv_df):
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

        return indic_df

    def plotly(self, ohlcv_df, layout={}, ret_indic=False, **params):

        var_open = self.ohlcv_names.get("open", "open")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_close = self.ohlcv_names.get("close", "close")

        indic_df = self.compute(ohlcv_df).reset_index().dropna()

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
    hits_fmt: str = Field(
        "{indic_name}_hits_{hits_str}", description="Range hit indicator name format")
    hits_d_fmt: str = Field(
        "{indic_name}d_hits_{hits_str}", description="Discrete range hit indicator name format")

    @property
    def hits_d_labels(self):
        return [f"{int(self.hits_levels[0])-1}-"] + \
            [f"{int(x)}-{int(y)-1}"
             for x, y in zip(self.hits_levels[:-1], self.hits_levels[1:])] + \
            [f"{int(self.hits_levels[-1])}+"]

    @property
    def var_hits_min(self):
        return self.hits_fmt.format(indic_name=self.indic_name,
                                    hits_str="min")

    @property
    def var_hits_max(self):
        return self.hits_fmt.format(indic_name=self.indic_name,
                                    hits_str="max")

    @property
    def var_hits_d_min(self):
        return self.hits_d_fmt.format(indic_name=self.indic_name,
                                      hits_str="min")

    @property
    def var_hits_d_max(self):
        return self.hits_d_fmt.format(indic_name=self.indic_name,
                                      hits_str="max")

    def compute(self, ohlcv_df):
        """Generalized hammer (GH) indicator"""

        # OHLCV variable identification
        var_close = self.ohlcv_names.get("close", "close")
        var_low = self.ohlcv_names.get("low", "low")
        var_high = self.ohlcv_names.get("high", "high")

        indic_df = super().compute(ohlcv_df)

        idx_hits_min = ohlcv_df[var_low] <= indic_df[self.var_close_min]
        idx_hits_max = ohlcv_df[var_high] >= indic_df[self.var_close_max]

        indic_df[self.var_hits_min] = idx_hits_min.rolling(self.window).sum()
        indic_df[self.var_hits_max] = idx_hits_max.rolling(self.window).sum()

        hits_bins = [-float("inf")] + \
            [x - 0.5 for x in self.hits_levels] + \
            [float("inf")]
        indic_df[self.var_hits_d_min] = \
            pd.cut(indic_df[self.var_hits_min],
                   bins=hits_bins,
                   labels=self.hits_d_labels)
        indic_df[self.var_hits_d_max] = \
            pd.cut(indic_df[self.var_hits_max],
                   bins=hits_bins,
                   labels=self.hits_d_labels)

        return indic_df

    def plotly(self, ohlcv_df, layout={}, ret_indic=False, **params):

        fig, indic_df = super().plotly(ohlcv_df, layout=layout, ret_indic=True, **params)

        hits_color_palette = \
            px.colors.sample_colorscale(
                px.colors.sequential.Plasma, len(self.hits_d_labels))

        hits_hovertemplate = \
            "#Hits: %{customdata[0]} | %{customdata[1]}"

        hits_min_marker_color = \
            [hits_color_palette[i]
             for i in indic_df[self.var_hits_d_min].cat.codes]
        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=indic_df[self.var_close_min],
            name=self.var_hits_min,
            mode='markers',
            showlegend=False,
            marker_color=hits_min_marker_color,
            marker_size=4,
            customdata=indic_df[[self.var_hits_min, self.var_hits_d_min]],
            hovertemplate=hits_hovertemplate),
            row=1, col=1)

        hits_max_marker_color = \
            [hits_color_palette[i]
             for i in indic_df[self.var_hits_d_max].cat.codes]
        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=indic_df[self.var_close_max],
            name=self.var_hits_max,
            mode='markers',
            showlegend=False,
            marker_color=hits_max_marker_color,
            marker_size=4,
            customdata=indic_df[[self.var_hits_max, self.var_hits_d_max]],
            hovertemplate=hits_hovertemplate),
            row=1, col=1)

        return fig
