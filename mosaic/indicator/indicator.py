from pydantic import Field
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from ..core import ObjMOSAIC


class Indicator(ObjMOSAIC):
    """
    Technical indicator base class.
    """
    
    @property
    def bw_length(self):
        return 0

    @property
    def names_map(self):
        """Indicator names format mapping: To be overloaded"""
        return {}
    
    def names(self, names=None):

        if not names:
            var_names = list(self.names_map.values())
        elif isinstance(names, str):
            var_names = self.names_map[names]
        else:
            var_names = [self.names_map[name] for name in names]

        return var_names
    
    def compute(self, *data, **kwrds):
        pass

    def plotly(self, ohlcv_df, plot_ohlcv=False):

        var_open = self.ohlcv_names.get("open", "open")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_close = self.ohlcv_names.get("close", "close")

        if plot_ohlcv:
            fig = make_subplots(rows=2, cols=1,
                                shared_xaxes=True,
                                vertical_spacing=0.02)

            fig.add_trace(go.Candlestick(x=ohlcv_df.index,
                                         open=ohlcv_df[var_open],
                                         high=ohlcv_df[var_high],
                                         low=ohlcv_df[var_low],
                                         close=ohlcv_df[var_close], name="OHLC"),
                          row=1, col=1)
        else:
            fig = go.Figure()

        return fig


class IndicatorOHLCV(Indicator):

    ohlcv_names: dict = Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")
