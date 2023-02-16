import pydantic
import typing
#import pandas as pd
import random
import numpy as np
#import tqdm
from ..utils import ValueNeighborhood
#from ..trading.core import SignalBase
from ..core import ObjMOSAIC

import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

# PandasSeries = typing.TypeVar('pandas.core.frame.Series')
# PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')



class DMBaseParams(pydantic.BaseModel):

    def __str__(self):
        return "\n".join(
            [f"{k}: {v}" for k, v in self.dict().items()])

    def random_from_neighbor(
            self,
            neighbor_specs: typing.Dict[str, ValueNeighborhood] = {},
            nchanges=None,
            inplace=False,
    ):
        
        nb_params = len(self.dict())
        if inplace:
            param_new = self
        else:
            param_new = self.copy()

        if nchanges is None:
            nchanges = int(np.ceil(np.random.rand()*nb_params))
        
        params_to_change = \
            random.sample(self.dict().keys(),
                          min(nchanges, nb_params))

        for param_name in params_to_change:

            param_neigh_spec = neighbor_specs.get(param_name)
            if not (param_neigh_spec):
                continue
            param_value_cur = getattr(self, param_name)

            param_value_new = \
                param_neigh_spec.random_neighbor_from_value(param_value_cur)

            setattr(param_new, param_name, param_value_new)

        if not inplace:
            return param_new

    def domain_from_neighbor(
            self,
            neighbor_spec: typing.Dict[str, ValueNeighborhood] = {},
    ):
        
        dm_params = {}

        for param, param_spec in neighbor_spec.items():

            param_value_cur = getattr(self, param)
            dm_params[param] = \
                param_spec.domain_from_value(param_value_cur)

        return dm_params
        
class DMBase(ObjMOSAIC):

    params: DMBaseParams = \
        pydantic.Field(0, description="Decision model parameters")

    ohlcv_names: dict = pydantic.Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")

    @property
    def bw_window(self):
        return 0

    @property
    def fw_window(self):
        return 0

    
    def compute(self, ohlcv_df, **kwrds):
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
