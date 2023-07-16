from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import typing
import pandas_ta as ta
from pydantic import Field
from .indicator import IndicatorOHLCV
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


class RSIIndicator(IndicatorOHLCV):

    window: int = Field(
        0, description="MA window size used to compute the indicator")
    levels: typing.List[float] = Field(
        None, description="Discretization levels if None no discretization is performed")
    indic_fmt: str = Field(
        "RSI{window}", description="Indicator name format")
    indic_d_fmt: str = Field(
        "{indic_name}d", description="Discrete indicator name format")
    mode: str = Field(
        "classic", description="Calulation mode 'classic' or 'wilder'")

    @property
    def bw_window(self):
        return super().bw_length + self.window

    # @property
    # def indic_name(self):
    #     return self.indic_fmt.format(window=self.window,
    #                                  levels=self.levels)

    # @property
    # def indic_d_name(self):
    #     return self.indic_d_fmt.format(
    #         indic_name=self.indic_name,
    #         window=self.window,
    #         levels=self.levels)

    # @property
    # def indic_name_offset(self):
    #     return self.offset_fmt.format(indic_name=self.indic_name,
    #                                   offset=-self.offset)

    # @property
    # def indic_d_name_offset(self):
    #     return self.offset_fmt.format(indic_name=self.indic_d_name,
    #                                   offset=-self.offset)

    @property
    def labels(self):
        return [f"{int(self.levels[0])}-"] + \
            [f"{int(x)}-{int(y)}"
             for x, y in zip(self.levels[:-1], self.levels[1:])] + \
            [f"{int(self.levels[-1])}+"]

    def compute(self, ohlcv_df, **kwrds):
        """Compute RSI"""
        super().compute(ohlcv_df, **kwrds)

        # OHLCV variable identification
        var_close = self.ohlcv_names.get("close", "close")
        data_close = ohlcv_df[var_close]

        indic_df = pd.DataFrame(index=ohlcv_df.index)

        if self.mode == "classic":
            close_delta = data_close.diff(1)

            delta_up = close_delta.copy(deep=True)
            delta_up[delta_up < 0] = 0
            delta_down = close_delta.copy(deep=True)
            delta_down[delta_down > 0] = 0

            roll_up = delta_up.rolling(self.window).mean()
            roll_down = delta_down.rolling(self.window).mean()

            indic_df[self.indic_name] = 100*roll_up/(roll_up + roll_down.abs())
        elif self.mode == "wilder":
            indic_df[self.indic_name] = ta.rsi(data_close, length=self.window)
        else:
            raise ValueError(f"{self.mode} not supported")

        if self.levels:
            indic_df[self.indic_d_name] = \
                pd.cut(indic_df[self.indic_name],
                       bins=[0] + self.levels + [100],
                       labels=self.labels)

        return self.apply_offset(indic_df)

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
            y=indic_df[self.indic_name_offset],
            name=self.indic_name,
            mode='markers+lines',
            line_color=color_indic
        ),
            row=2, col=1)

        layout["xaxis_rangeslider_visible"] = False
        fig.update_layout(**layout)

        if ret_indic:
            return fig, indic_df
        else:
            return fig
