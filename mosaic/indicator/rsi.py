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


class RSI(IndicatorOHLCV):

    length: int = Field(
        1, description="MA window length used to compute the indicator")
    mode: str = Field(
        "ta", description="Calulation mode 'ta' or 'simple'")

    @property
    def bw_length(self):
        return super().bw_length + self.length

    @property
    def names_map(self):
        """Indicator names format mapping"""
        return {
            "rsi": f"RSI_{self.length}",
        }

    
    def compute(self, ohlcv_df, **kwrds):
        """Compute indicator"""
        super().compute(ohlcv_df, **kwrds)

        # OHLCV variable identification
        var_close = self.ohlcv_names.get("close", "close")
        data_close = ohlcv_df[var_close]

        indic_df = pd.DataFrame(index=ohlcv_df.index)

        if self.mode == "simple":
            close_delta = data_close.diff(1)

            delta_up = close_delta.copy(deep=True)
            delta_up[delta_up < 0] = 0
            delta_down = close_delta.copy(deep=True)
            delta_down[delta_down > 0] = 0

            roll_up = delta_up.rolling(self.length).mean()
            roll_down = delta_down.rolling(self.length).mean()

            indic_df[self.names('rsi')] = 100*roll_up/(roll_up + roll_down.abs())
        elif self.mode == "ta":
            indic_df[self.names('rsi')] = ta.rsi(data_close, length=self.length)
        else:
            raise ValueError(f"{self.mode} not supported")

        # if self.levels:
        #     indic_df[self.indic_d_name] = \
        #         pd.cut(indic_df[self.indic_name],
        #                bins=[0] + self.levels + [100],
        #                labels=self.labels)

        return indic_df

    def plotly(self, ohlcv_df, layout={}, ret_indic=False, plot_ohlcv=False, **params):

        indic_df = self.compute(ohlcv_df).dropna()

        fig = super().plotly(ohlcv_df, plot_ohlcv=plot_ohlcv)
        fig_trace = dict(row=2, col=1) if plot_ohlcv else {}

        color_indic = px.colors.qualitative.T10[0]
        fig.add_trace(go.Scatter(
            x=indic_df.index,
            y=indic_df[self.names('rsi')],
            name=self.names('rsi'),
            mode='markers+lines',
            line_color=color_indic
        ), **fig_trace)

        if plot_ohlcv:
            layout["xaxis_rangeslider_visible"] = False
            
        fig.update_layout(**layout)

        if ret_indic:
            return fig, indic_df
        else:
            return fig
