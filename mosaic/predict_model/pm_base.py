import pydantic
import typing
import pandas as pd
#import tqdm
from ..core import ObjMOSAIC
from ..utils.data_management import HyperParams
#from ..trading.core import SignalBase
from ..indicator.indicator import IndicatorOHLCV

import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

# PandasSeries = typing.TypeVar('pandas.core.frame.Series')
# PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')


class PredictModelBase(ObjMOSAIC):

    params: HyperParams = \
        pydantic.Field(None, description="Decision model parameters")

    features: typing.List[IndicatorOHLCV] = pydantic.Field(
        [], description="List of features indicators")

    ohlcv_names: dict = pydantic.Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")

    bkd: typing.Any = pydantic.Field(None, description="Statistical model backend")

    @property
    def bw_length(self):
        return max([indic.bw_length
                    for indic in self.features])

    def dict(self, **kwrds):

        if kwrds["exclude"]:
            kwrds["exclude"].add("bkd")
            kwrds["exclude"].add("logger")
        else:
            kwrds["exclude"] = {"bkd", "logger"}
            
        return super().dict(**kwrds)

    def compute_features(self, ohlcv_df):

        features_df_list = \
            [indic.compute(ohlcv_df)
             for indic in self.features]

        if features_df_list:
            features_df = pd.concat(features_df_list, axis=1)
        else:
            features_df = pd.DataFrame(index=ohlcv_df.index)
            
        return features_df

    def fit(self, ohlcv_df, dropna=True, **kwrds):
        # NOTE : Here features are shifted to properly align returns with 
        # features observed just before the corresponding returns
        features_df = self.compute_features(ohlcv_df).shift(1)
        target_s = self.compute_returns(ohlcv_df)
        if dropna:
            data_all_df = pd.concat([features_df, target_s], axis=1).dropna()
            features_df = data_all_df[features_df.columns]
            target_s = data_all_df[target_s.name]

        return features_df, target_s

    def predict(self, ohlcv_df, **kwrds):
        return pd.Series(0.0,
                         index=ohlcv_df.index,
                         name="PMBase",
                         dtype='float64')


class PMReturns(PredictModelBase):

    returns_horizon: int = \
        pydantic.Field(0, description="Close returns horizon to be predicted")

    @property
    def target_var(self):
        return f"ret_{self.returns_horizon}"

    def compute_returns(self, ohlcv_df):

        close_var = self.ohlcv_names.get("close", "close")

        return ohlcv_df[close_var].pct_change(self.returns_horizon+1)\
                                  .shift(-self.returns_horizon)\
                                  .rename(self.target_var)


class PMReturnsUpDown(PMReturns):

    direction: str = \
        pydantic.Field(..., description="Returns direction to be predicted")

    threshold: float = \
        pydantic.Field(0, description="Threshold to discretize returns according to considered direction")

    threshold_mode: str = \
        pydantic.Field('normal', description="Mode to use threshold. Could be 'normal', the threshold value is considered as absolute value. Could be 'quantile', in this case threshold is given as a quantile (in [0,1]) of returns value")

    @pydantic.validator("direction", pre=True, always=True)
    def validate_direction(cls, value):
        val_accepted = ["up", "down"]
        if value not in val_accepted:
            raise ValueError("direction must be: {','.join(val_accepted)}")
        return value

    @pydantic.validator("threshold_mode", pre=True, always=True)
    def validate_threshold_mode(cls, value):
        val_accepted = ["normal", "quantile"]
        if value not in val_accepted:
            raise ValueError("threshold_mode must be: {','.join(val_accepted)}")
        return value

    @property
    def target_var(self):
        return f"{super().target_var}_{self.direction}"

    def compute_returns(self, ohlcv_df):

        ret = super().compute_returns(ohlcv_df)

        if self.threshold_mode == "normal":
            threshold = self.threshold
        elif self.threshold_mode == "quantile":
            if self.direction == "up":
                ret_tmp = ret[ret > 0]
                threshold = ret_tmp.quantile(self.threshold)
            else:
                ret_tmp = ret[ret < 0].abs()
                threshold = -ret_tmp.quantile(self.threshold)
                
        else:
            raise ValueError(f"Threshold mode {self.threshold_mode} not supported")
            
        ret_d = ret > threshold if self.direction == "up" \
            else ret < threshold
        
        return ret_d.rename(self.target_var)

        
