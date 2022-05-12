from pandas import Timestamp, DataFrame
from typing import Dict

from pydantic import Field
from ..indicator import Indicator
from ..config import IndicatorConfig


class ReturnsIndicator(Indicator):

    horizon: int = Field(-1)

    def __init__(self, indicator_config: IndicatorConfig):
        super().__init__(indicator_config)

        if "horizon" in indicator_config.parameters:
            self.horizon = indicator_config.parameters["horizon"]

    def compute_indicator(self, sourceData: Dict[str, DataFrame],
                          start: Timestamp, stop: Timestamp):

        # get the df of ohlcv source
        df: DataFrame = sourceData.get("ohlcv")

        df["ret"] = df.iloc[:-1].values/df.iloc[1:]-1

        return df[["ret"]]
