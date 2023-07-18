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


class MFI(IndicatorOHLCV):
    """
Money Flow Index (MFI)

Uses both price and volume to measure buying and selling pressure. It is positive when the typical price rises (buying pressure) and negative when the typical price declines (selling pressure). A ratio of positive and negative money flow is then plugged into an RSI formula to create an oscillator that moves between zero and one hundred.

http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:money_flow_index_mfi
"""
    
    names_fmt: dict = Field(
        {"mfi": "MFI_{length}"}, description="Names format mapping")
    length: int = Field(
        14, description="MA window length used to compute the indicator",
        ge=1)

    @property
    def bw_length(self):
        return super().bw_length + self.length

    def compute(self, ohlcv_df, **kwrds):
        """Compute RSI"""
        super().compute(ohlcv_df, **kwrds)

        # OHLCV variable identification
        var_close = self.ohlcv_names.get("close", "close")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_volume = self.ohlcv_names.get("volume", "volume")

        indic_df = pd.DataFrame(index=ohlcv_df.index)

        indic_df[self.names[0]] = ta.mfi(
            high=ohlcv_df[var_high],
            low=ohlcv_df[var_low],
            close=ohlcv_df[var_close],
            volume=ohlcv_df[var_volume],
            length=self.length)

        return self.apply_offset(indic_df)

    def plotly(self, ohlcv_df, layout={}, ret_indic=False, plot_ohlcv=False, **params):

        indic_df = self.compute(ohlcv_df).dropna()

        fig = super().plotly(ohlcv_df, plot_ohlcv=plot_ohlcv)
        fig_trace = dict(row=2, col=1) if plot_ohlcv else {}

        color_indic = px.colors.qualitative.T10[0]
        fig.add_trace(go.Scatter(
            x=indic_df.index,
            y=indic_df[self.names[0]],
            name=self.names[0],
            mode='markers+lines',
            line_color=color_indic
        ), **fig_trace)

        layout["xaxis_rangeslider_visible"] = False
        fig.update_layout(**layout)

        if ret_indic:
            return fig, indic_df
        else:
            return fig
