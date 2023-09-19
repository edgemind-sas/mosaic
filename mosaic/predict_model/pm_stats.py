import pydantic
import typing
import pandas as pd
import statsmodels.api as sm

#import tqdm
#from ..trading.core import SignalBase
from .pm_base import PredictModelReturns
from ..indicator.indicator import IndicatorOHLCV

import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

# PandasSeries = typing.TypeVar('pandas.core.frame.Series')
# PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')


class PredictModelStats(PredictModelReturns):

    features: typing.List[IndicatorOHLCV] = pydantic.Field(
        [], description="List of features indicators")

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

    # @property
    # def fw_length(self):
    #     return 0
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


class PredictLinearRegression(PredictModelStats):

    def fit(self, ohlcv_df, **kwrds):

        features_df, target_s = super().fit(ohlcv_df, **kwrds)

        features_df = sm.add_constant(features_df)
        
        mod = sm.OLS(target_s, features_df)
        self.bkd = mod.fit()
        

    def predict(self, ohlcv_df, **kwrds):

        features_df = sm.add_constant(self.compute_features(ohlcv_df))
        
        return self.bkd.predict(features_df).fillna(0)

