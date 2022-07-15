import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import typing
from pydantic import Field
from .indicator import IndicatorOHLCV


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
    def labels(self):
        nb_pos_bins = len(self.levels) + 1

        return [f"{k + 1 if k > 0 else ''}-" for k in reversed(range(nb_pos_bins))] + \
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

        close_min = data_close_roll.min()
        close_max = data_close_roll.max()

        close_range = close_max - close_min

        indic_df[self.indic_name] = (data_close - close_min).div(close_range)

        return indic_df

    def plotly(self, ohlcv_df, layout={}, **params):

        var_volume = self.ohlcv_names.get("volume", "volume")

        indic_df = self.compute(ohlcv_df)
        indic_name = self.indic_fmt.format(window=self.window)

        fig = px.bar(ohlcv_df, y=var_volume,
                     color=indic_df[indic_name].astype(str).fillna("NA"),
                     labels={'color': indic_name},
                     **params)

        # # include a go.Bar trace for volumes
        # fig.add_trace(go.Bar(x=ohlcv_df.index,
        #                      y=ohlcv_df[var_volume],
        #                      name="Volume"),
        #               **trace_params)

        fig.update_layout(**layout)

        return fig
