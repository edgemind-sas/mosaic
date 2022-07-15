import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import typing
from pydantic import Field
from .indicator import IndicatorOHLCV


class MVLIndicator(IndicatorOHLCV):

    window: int = Field(
        0, description="Past time window to compute volume levels")
    levels: typing.List[float] = Field(
        [0.5], description="Level bins")
    indic_fmt: str = Field(
        "MVL", description="Indicator name format")

    def compute(self, ohlcv_df):
        """Generalized hammer (GH) indicator"""

        # OHLCV variable identification
        var_volume = self.ohlcv_names.get("volume", "volume")

        indic_name = self.indic_fmt.format(window=self.window)
        indic_df = pd.DataFrame(index=ohlcv_df.index,
                                columns=[indic_name])

        data_volume = ohlcv_df[var_volume]
        data_volume_roll = data_volume.rolling(self.window)

        q_bin_list = []
        bin_left = 0
        bin_right = self.levels[0]
        volume_q_left = 0
        volume_q_right = data_volume_roll.quantile(bin_right)
        q_bin_str = f"l{100*bin_left:.0f}_{100*bin_right:.0f}"
        q_bin_list.append(q_bin_str)

        idx_q_bin = (volume_q_left <= data_volume) & \
            (data_volume < volume_q_right)
        indic_df.loc[idx_q_bin, indic_name] = q_bin_str

        for bin_left, bin_right in zip(self.levels[:-1], self.levels[1:]):

            volume_q_left = data_volume_roll.quantile(bin_left)
            volume_q_right = data_volume_roll.quantile(bin_right)
            q_bin_str = f"l{100*bin_left:.0f}_{100*bin_right:.0f}"
            q_bin_list.append(q_bin_str)

            idx_q_bin = (volume_q_left <= data_volume) & \
                (data_volume < volume_q_right)
            indic_df.loc[idx_q_bin, indic_name] = q_bin_str

        bin_left = self.levels[-1]
        bin_right = 1
        volume_q_left = data_volume_roll.quantile(bin_left)
        volume_q_right = float("inf")
        q_bin_str = f"l{100*bin_left:.0f}_{100*bin_right:.0f}"
        q_bin_list.append(q_bin_str)

        idx_q_bin = (volume_q_left <= data_volume) & \
            (data_volume < volume_q_right)
        indic_df.loc[idx_q_bin, indic_name] = q_bin_str

        q_bin_cats = pd.api.types.CategoricalDtype(categories=q_bin_list,
                                                   ordered=True)

        indic_df[indic_name] = indic_df[indic_name].astype(q_bin_cats)

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
