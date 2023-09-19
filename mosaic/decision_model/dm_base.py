import pydantic
import typing
import pandas as pd
import random
#import tqdm
from ..utils.data_management import HyperParams

#from ..trading.core import SignalBase
from ..core import ObjMOSAIC
from ..predict_model.pm_base import PredictModelBase

import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

# PandasSeries = typing.TypeVar('pandas.core.frame.Series')
# PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')

        
class DMBase(ObjMOSAIC):

    buy_threshold: float = \
        pydantic.Field(None, description="If signal_score > buy_threshold => buy signal generated",
                       ge=0)
                       
    sell_threshold: float = \
        pydantic.Field(None, description="If signal_score < -sell_threshold => sell signal generated",
                       ge=0)
    
    params: HyperParams = \
        pydantic.Field(None, description="Decision model parameters")

    ohlcv_names: dict = pydantic.Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")


    
    @property
    def bw_length(self):
        return 0

    @property
    def fw_length(self):
        return 0

    def compute_signal(self, signal_score, **kwrds):

        #ipdb.set_trace()
        signal_s = pd.Series(index=signal_score.index,
                             name="signal",
                             dtype="object")

        if self.buy_threshold is not None:
            idx_buy = signal_score > self.buy_threshold
            signal_s.loc[idx_buy] = "buy"
            
        if self.sell_threshold is not None:
            idx_sell = signal_score < -self.sell_threshold
            signal_s.loc[idx_sell] = "sell"

        return pd.concat([signal_s,
                          signal_score.rename("score")],
                         axis=1)
    
    def predict(self, ohlcv_df, **kwrds):
        
        raise NotImplementedError("compute method not implemented")

    # def fit(self, ohlcv_df, method="brute_force", **fit_params):

    #     fit_method = getattr(self, f"fit_{method}")

    #     fit_method(ohlcv_df, **fit_params)
       
    # def fit_brute_force(self, ohlcv_df,
    #                     bt_cls,
    #                     bt_params={},
    #                     dm_params={},
    #                     progress_mode=True,
    #                     target_measure="perf_open_open",
    #                     nb_trades_min=15,
    #                     ):

    #     dm_params_list = compute_combinations(**self.dm_params)

    #     bt_eval_list = []
    #     for params in tqdm.tqdm(dm_params_list,
    #                             disable=not progress_mode,
    #                             desc="Parameters",
    #                             ):
            
    #         bt_cur = bt_cls(
    #             ohlcv_df=ohlcv_df,
    #             decision_model=self.dm_cls(**params),
    #             **bt_params,
    #         )
            
    #         bt_cur.run()
    
    #         bt_eval_list.append(dict(params, **bt_cur.perf.dict()))

    #     brute_force_df = \
    #         pd.DataFrame.from_records(bt_eval_list)\
    #                     .sort_values(by=target_measure,
    #                                  ascending=False)

    #     idx_const_nb_trades = \
    #         brute_force_df["nb_trades"] > nb_trades_min

    #     brute_force_bis_df = \
    #         brute_force_df.loc[idx_const_nb_trades]

    #     dm_params_opt = \
    #         brute_force_bis_df.iloc[0]\
    #                           .loc[dm_params.keys()]\
    #                           .to_dict()

    #     self.params = self.params.__class__(**dm_params_opt)


class DM1ML(DMBase):
    
    pm: PredictModelBase = \
        pydantic.Field(PredictModelBase(), description="Buy/sell predict model")

    @property
    def bw_length(self):
        return self.pm.bw_length

    def fit(self, ohlcv_df, **kwrds):
        self.pm.fit(ohlcv_df, **kwrds)
    
    def predict(self, ohlcv_df, **kwrds):
        signal_score = self.pm.predict(ohlcv_df, **kwrds)
        return self.compute_signal(signal_score)

    
class DM2ML(DMBase):
    
    pm_buy: PredictModelBase = \
        pydantic.Field(PredictModelBase(), description="Buy predict model")
    pm_sell: PredictModelBase = \
        pydantic.Field(PredictModelBase(), description="Buy predict model")

    @property
    def bw_length(self):
        return max(self.pm_buy.bw_length, self.pm_sell.bw_length)

    def fit(self, ohlcv_df, **kwrds):
        self.pm_buy.fit(ohlcv_df, **kwrds)
        self.pm_sell.fit(ohlcv_df, **kwrds)
    
    def predict(self, ohlcv_df, **kwrds):

        buy_score = self.pm_buy.predict(ohlcv_df, **kwrds)
        sell_score = self.pm_sell.predict(ohlcv_df, **kwrds)

        signal_score = buy_score - sell_score

        return self.compute_signal(signal_score)
