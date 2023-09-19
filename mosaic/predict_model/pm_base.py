import pydantic
import typing
import pandas as pd
#import tqdm
from ..core import ObjMOSAIC
from ..utils.data_management import HyperParams
#from ..trading.core import SignalBase

import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

# PandasSeries = typing.TypeVar('pandas.core.frame.Series')
# PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')


class PredictModelBase(ObjMOSAIC):

    params: HyperParams = \
        pydantic.Field(None, description="Decision model parameters")

    ohlcv_names: dict = pydantic.Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")

    @property
    def bw_length(self):
        return 0

    # @property
    # def fw_length(self):
    #     return 0
    
    def fit(self, ohlcv_df, **kwrds):
        pass

    def predict(self, ohlcv_df, **kwrds):
        return pd.Series(0.0,
                         index=ohlcv_df.index,
                         name="PMBase",
                         dtype='float64')


class PredictModelReturns(PredictModelBase):

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

        
