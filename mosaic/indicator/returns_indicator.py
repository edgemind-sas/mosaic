import typing
import pandas as pd
from pydantic import Field
from .indicator import IndicatorOHLCV


class ReturnsBaseIndicator(IndicatorOHLCV):
    horizon: typing.List[int] = \
        Field([0], description="Returns time steps in past or future")
    period_name: str = \
        Field("period", description="Returns column index name")
    period_fmt: str = \
        Field(None, description="Returns columns format")

    def __init__(self, **data):
        super().__init__(**data)
        self.history_bw = 1
        self.history_fw = len(self.horizon) - 1


class ReturnsCloseIndicator(ReturnsBaseIndicator):

    def compute(self, ohlcv_df: pd.DataFrame):

        close_var = self.ohlcv_names.get("close", "close")
        close_pm1 = ohlcv_df[close_var].shift(1)

        ret_list = []
        for k in self.horizon:
            if k >= 0:
                close_k = ohlcv_df[close_var].shift(-k)
                ret_k = close_k/close_pm1 - 1
            else:
                close_k = ohlcv_df[close_var].shift(1-k)
                ret_k = ohlcv_df[close_var]/close_k - 1

            ret_k.name = k if self.period_fmt is None \
                else f"{self.period_fmt}{k:+}"
            ret_list.append(ret_k)

        ret_df = pd.concat(ret_list, axis=1)
        ret_df.columns.name = self.period_name.format(var=close_var, k=k)
        return ret_df


class ReturnsHighIndicator(ReturnsBaseIndicator):

    def compute(self, ohlcv_df: pd.DataFrame):

        # OHLCV variable identification
        close_var = self.ohlcv_names.get("close", "close")
        high_var = self.ohlcv_names.get("high", "high")

        close_pm1 = ohlcv_df[close_var].shift(1)

        ret_list = []
        for k in self.horizon:
            if k >= 0:
                high_k = ohlcv_df.rolling(abs(k)+1)[high_var]\
                                 .max().shift(-k)
                ret_k = high_k/close_pm1 - 1
            else:
                close_k = ohlcv_df[close_var].shift(1-k)
                high_k = ohlcv_df.rolling(abs(k)+1)[high_var]\
                                 .max()
                ret_k = high_k/close_k - 1

            ret_k.name = k if self.period_fmt is None \
                else f"{self.period_fmt}{k:+}"

            ret_list.append(ret_k)

        ret_df = pd.concat(ret_list, axis=1)
        ret_df.columns.name = self.period_name.format(var=high_var, k=k)
        return ret_df


class ReturnsLowIndicator(ReturnsBaseIndicator):

    def compute(self, ohlcv_df: pd.DataFrame):

        # OHLCV variable identification
        close_var = self.ohlcv_names.get("close", "close")
        low_var = self.ohlcv_names.get("low", "low")

        close_pm1 = ohlcv_df[close_var].shift(1)

        ret_list = []
        for k in self.horizon:
            if k >= 0:
                low_k = ohlcv_df.rolling(abs(k)+1)[low_var]\
                                .min().shift(-k)
                ret_k = low_k/close_pm1 - 1
            else:
                close_k = ohlcv_df[close_var].shift(1-k)
                low_k = ohlcv_df.rolling(abs(k)+1)[low_var]\
                                .min()
                ret_k = low_k/close_k - 1

            ret_k.name = k if self.period_fmt is None \
                else f"{self.period_fmt}{k:+}"

            ret_list.append(ret_k)

        ret_df = pd.concat(ret_list, axis=1)
        ret_df.columns.name = self.period_name.format(var=low_var, k=k)
        return ret_df
