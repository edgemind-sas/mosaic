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
            2*(indic_df[self.var_close_max] -
               indic_df[self.var_close_min]).div(close_range) - 1
        indic_df[self.indic_d_name] = pd.cut(indic_df[self.indic_name],
                                             bins=self.levels_all,
                                             labels=self.labels,
                                             include_lowest=True)

        return indic_df

    def plotly(self, ohlcv_df, layout={}, **params):

        var_open = self.ohlcv_names.get("open", "open")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_close = self.ohlcv_names.get("close", "close")

        indic_df = self.compute(ohlcv_df)

        fig = make_subplots(rows=2, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.02)

        fig.add_trace(go.Candlestick(x=ohlcv_df.index,
                                     open=ohlcv_df[var_open],
                                     high=ohlcv_df[var_high],
                                     low=ohlcv_df[var_low],
                                     close=ohlcv_df[var_close], name="OHLC"),
                      row=1, col=1)

        layout["xaxis_rangeslider_visible"] = False
        fig.update_layout(**layout)

        # include a go.Bar trace for volumes
        fig2 = px.line(indic_df.reset_index().dropna(),
                       x="time",
                       y=self.indic_name,
                       markers=True)

        # fig2.update_traces(mode="lines+markers")
        fig.add_trace(fig2.data[0],
                      row=2, col=1)

        return fig


class SRIIndicator(RangeIndexIndicator):
    """Support range index"""
    window: int = Field(
        0, description="Past time window to compute volume levels")
    levels: typing.List[float] = Field(
        [0.5], description="Positive level bins")
    indic_fmt: str = Field(
        "RI", description="Indicator name format")
    indic_d_fmt: str = Field(
        "{indic_name}d", description="Discrete indicator name format")

    @property
    def var_hits_min(self):
        return self.indic_name + "_hits_min"

    @property
    def var_hits_max(self):
        return self.indic_name + "_hits_max"

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

        return indic_df
