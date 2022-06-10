from pandas import Timestamp, DataFrame
from typing import Dict
import pandas as pd

from pydantic import Field
from ..indicator import Indicator
from ..config import IndicatorConfig


class ReturnsIndicator(Indicator):

    horizon: int = Field(-1)

    def __init__(self, indicator_config: IndicatorConfig):
        super().__init__(indicator_config)

        if "horizon" in indicator_config.parameters:
            self.horizon = indicator_config.parameters["horizon"]

    def compute(self, sourceData: Dict[str, DataFrame],
                start: Timestamp, stop: Timestamp):

        # get the df of ohlcv source
        df: DataFrame = sourceData.get("ohlcv")

        df["ret"] = df.iloc[:-1].values/df.iloc[1:]-1

        return df[["ret"]]


class ReturnsCloseIndicator(Indicator):

    def compute(self, sourceData: Dict[str, DataFrame],
                start: Timestamp, stop: Timestamp):

        hrz_list = self.config.parameters.get("horizon")

        # OHLCV variable identification
        ohlcv_df = sourceData.get("ohlcv")
        close_var = "close"
        close_pm1 = ohlcv_df[close_var].shift(1)

        ret_list = []
        for k in hrz_list:
            if k >= 0:
                close_k = ohlcv_df[close_var].shift(-k)
                ret_k = close_k/close_pm1 - 1
            else:
                close_k = ohlcv_df[close_var].shift(1 - k)
                ret_k = ohlcv_df[close_var]/close_k - 1

            ret_k.name = f"ret_{close_var}_p[{k}]"
            ret_list.append(ret_k)

        ret_df = pd.concat(ret_list, axis=1)

        return ret_df

        # # get the df of ohlcv source
        # df: DataFrame = sourceData.get("ohlcv")

        # df["ret"] = df.iloc[:-1].values/df.iloc[1:]-1

        # return df[["ret"]]
