import pandas as pd

from pydantic import Field
from .indicator import IndicatorOHLCV


class GHIndicator(IndicatorOHLCV):

    alpha: float = Field(
        0, description="Body width lower bound to filter too small bodies")
    beta: float = Field(
        2, description="Threshold for absolute ratio between main shadow length and (body + small shadow) length")
    labels: list = Field([-1, 0, 1], description="Discrete hammer labels")
    indic_num_fmt: str = Field(
        "GH", description="Numerical indicator name format")
    indic_d_fmt: str = Field(
        "GHd", description="Discrete indicator name format")

    def compute(self, ohlcv_df):
        """Generalized hammer (GH) indicator"""

        # OHLCV variable identification
        var_open = self.ohlcv_names.get("open", "open")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_close = self.ohlcv_names.get("close", "close")

        oc_df = ohlcv_df[[var_open, var_close]]
        min_o_c = oc_df.min(axis=1)
        max_o_c = oc_df.max(axis=1)
        s_low = min_o_c - ohlcv_df[var_low]
        s_upper = ohlcv_df[var_high] - max_o_c

        body_abs = (ohlcv_df[var_close] - ohlcv_df[var_open]).abs()

        body_rvar = body_abs.div(ohlcv_df[var_open])
        body_abs.loc[body_rvar < self.alpha] = 1e100

        gh = (s_upper - s_low).div(body_abs)
        gh.name = self.indic_num_fmt.format(alpha=self.alpha)

        ghd = pd.cut(gh, bins=[-float("inf"), -self.beta, self.beta, float("inf")],
                     labels=self.labels)

        ghd.name = self.indic_d_fmt.format(alpha=self.alpha, beta=self.beta)

        return pd.concat([gh, ghd], axis=1)
