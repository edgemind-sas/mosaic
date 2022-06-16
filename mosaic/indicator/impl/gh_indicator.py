from pandas import Timestamp, DataFrame
from typing import Dict
import pandas as pd

from pydantic import Field
from ..indicator import Indicator


def gh_indicator(ohlcv_df, alpha=0, ohlcv_names={}, indic_name_fmt="GH"):
    """Generalized hammer (GH) indicator"""

    # OHLCV variable identification
    var_open = ohlcv_names.get("open", "open")
    var_high = ohlcv_names.get("high", "high")
    var_low = ohlcv_names.get("low", "low")
    var_close = ohlcv_names.get("close", "close")

    oc_df = ohlcv_df[[var_open, var_close]]
    min_o_c = oc_df.min(axis=1)
    max_o_c = oc_df.max(axis=1)
    s_low = min_o_c - ohlcv_df[var_low]
    s_upper = ohlcv_df[var_high] - max_o_c

    body_abs = (ohlcv_df[var_close] - ohlcv_df[var_open]).abs()

    body_rvar = body_abs.div(ohlcv_df[var_open])
    body_abs.loc[body_rvar < alpha] = 1e100

    indic = (s_upper - s_low).div(body_abs)

    indic.name = indic_name_fmt.format(alpha=alpha)

    return indic


class GHIndicator(Indicator):

    def compute_bis(self, ohlcv_df, alpha=0, ohlcv_names={}, indic_name_fmt="GH"):
        """Generalized hammer (GH) indicator"""

        # OHLCV variable identification
        var_open = ohlcv_names.get("open", "open")
        var_high = ohlcv_names.get("high", "high")
        var_low = ohlcv_names.get("low", "low")
        var_close = ohlcv_names.get("close", "close")

        oc_df = ohlcv_df[[var_open, var_close]]
        min_o_c = oc_df.min(axis=1)
        max_o_c = oc_df.max(axis=1)
        s_low = min_o_c - ohlcv_df[var_low]
        s_upper = ohlcv_df[var_high] - max_o_c

        body_abs = (ohlcv_df[var_close] - ohlcv_df[var_open]).abs()

        body_rvar = body_abs.div(ohlcv_df[var_open])
        body_abs.loc[body_rvar < alpha] = 1e100

        indic = (s_upper - s_low).div(body_abs)

        indic.name = indic_name_fmt.format(alpha=alpha)

        return indic

    def compute(self, sourceData: Dict[str, DataFrame],
                start: Timestamp, stop: Timestamp):

        alpha = self.config.parameters.get("alpha")
        beta = self.config.parameters.get("beta")

        # OHLCV variable identification
        ohlcv_df = sourceData.get("ohlcv")

        # , ohlcv_names=ohlcv_names)
        gh = self.compute_bis(ohlcv_df, alpha=alpha)

        indic = pd.cut(gh, bins=[-float("inf"), -beta, beta, float("inf")],
                       labels=["-", "=", "+"])

        # indic.name = indic_name_fmt.format(alpha=alpha,
        #                                    beta=beta)
        indic.name = 'GHd'

        return indic.to_frame()
