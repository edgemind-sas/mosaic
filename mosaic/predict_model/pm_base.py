import pydantic
import typing
import copy
import pandas as pd
#import tqdm
from ..core import ObjMOSAIC
from ..utils.data_management import HyperParams
#from ..trading.core import SignalBase
from ..indicator.indicator import IndicatorOHLCV
import sklearn.preprocessing as skp


import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

# PandasSeries = typing.TypeVar('pandas.core.frame.Series')
# PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')


class PredictModelBase(ObjMOSAIC):

    params: HyperParams = \
        pydantic.Field(None, description="Prediction model parameters")

    features: typing.List[IndicatorOHLCV] = pydantic.Field(
        [], description="List of features indicators")

    var_features: typing.List[str] = pydantic.Field(
        [], description="List of features variable names")

    sk_preproc: str = pydantic.Field(
        None, description="Name of the sklearn preprocessing class")

    sk_preproc_params: dict = pydantic.Field(
        {}, description="sklearn preprocessing parameters")
    
    sk_preproc_features: typing.Any = \
        pydantic.Field(None, description="Pre processing data function for features from sklean preprocessing package")

    sk_preproc_target: typing.Any = \
        pydantic.Field(None, description="Pre processing data function for targets from sklean preprocessing package")

    # standard_features: bool = pydantic.Field(
    #     True, description="Indicates if features should be center and scaled")

    # features_center: list = pydantic.Field(
    #     None, description="Feature center vector")

    # features_std: list = pydantic.Field(
    #     None, description="Feature standard deviation vector")

    ohlcv_names: dict = pydantic.Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")

    bkd: typing.Any = pydantic.Field(None, description="Model backend")

    @property
    def bw_length(self):
        return max([indic.bw_length
                    for indic in self.features]) if self.features else 0

    def __init__(self, **data: typing.Any):
        super().__init__(**data)

        if self.sk_preproc is not None:
            self.sk_preproc_features = \
                getattr(skp, self.sk_preproc)(**self.sk_preproc_params)
            self.sk_preproc_target = \
                getattr(skp, self.sk_preproc)(**self.sk_preproc_params)

    
    def dict(self, **kwrds):

        attr_to_exclude = {"bkd", "logger", "sk_preproc"}
        
        if kwrds.get("exclude"):
            [kwrds["exclude"].add(attr) for attr in attr_to_exclude]
        else:
            kwrds["exclude"] = attr_to_exclude
            
        return super().dict(**kwrds)

    def compute_features(self, ohlcv_df):

        features_df_list = \
            [indic.compute(ohlcv_df)
             for indic in self.features]
        if features_df_list:
            features_df = pd.concat(features_df_list, axis=1)
        else:
            features_df = pd.DataFrame(index=ohlcv_df.index)

        self.var_features = list(features_df.columns)
        
        return features_df
    


class PMReturns(PredictModelBase):

    returns_horizon: int = \
        pydantic.Field(0, description="Close returns horizon to be predicted")

    @property
    def bw_length(self):
        return super().bw_length

    @property
    def var_target(self):
        return f"ret_{self.returns_horizon}"

    def prepare_data_fit(self, ohlcv_df, dropna=True, **kwrds):

        features_df = self.compute_features(ohlcv_df)
        #super().prepare_data_fit(ohlcv_df, dropna=dropna, **kwrds)
        target_s = self.compute_returns(ohlcv_df)

        # Aligned features and target
        data_all_df = pd.concat([features_df, target_s], axis=1).sort_index()

        if dropna:
            data_all_df.dropna(inplace=True)

            
        # Get aligned features and target data
        features_df = data_all_df[self.var_features]
        target_s = data_all_df[self.var_target]

        if self.sk_preproc is not None:
            
            features_arr = self.sk_preproc_features.fit_transform(features_df)
            features_df = pd.DataFrame(features_arr,
                                       index=features_df.index,
                                       columns=features_df.columns)
            
            target_arr = target_s.values.reshape(-1, 1)
            target_arr = self.sk_preproc_target.fit_transform(target_arr)
            target_s = pd.Series(target_arr.flatten(),
                                 name=target_s.name,
                                 index=target_s.index)

        return features_df, target_s

    def prepare_data_predict(self, ohlcv_df, dropna=True, **kwrds):

        features_df = self.compute_features(ohlcv_df)

        if dropna:
            features_df.dropna(inplace=True)

        if self.sk_preproc is not None:
            features_arr = self.sk_preproc_features.transform(features_df)
            features_df = pd.DataFrame(features_arr,
                                       index=features_df.index,
                                       columns=features_df.columns)

        return features_df

    
    def postproc_data_predict(self, data_pred, **kwrds):

        if self.sk_preproc_target is not None:
            data_pred = self.sk_preproc_target.inverse_transform(data_pred)
            
        return data_pred

    def compute_returns(self, ohlcv_df):

        close_var = self.ohlcv_names.get("close", "close")
        
        # NOTE : Here returns are shifted (-1) to properly align returns with 
        # features to avoid anticipation biais
        ret = ohlcv_df[close_var].pct_change(self.returns_horizon+1)\
                                 .shift(-self.returns_horizon-1)\
                                 .rename(self.var_target)
        return ret


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
        return f"{super().var_target}_{self.direction}"

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

        
