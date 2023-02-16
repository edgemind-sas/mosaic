import pydantic
import typing
import pandas as pd
import numpy as np
import pkg_resources
import tqdm
from ..utils import compute_combinations
from .dm_base import DMBase
#from ..backtest.dm_optim import DMLongOptimizer

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

PandasSeries = typing.TypeVar('pandas.core.frame.Series')
PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')


class DMLong(DMBase):
    
    # orders: PandasSeries = \
    #     pydantic.Field(None, description="Final long orders series")

    # indic_bkd: typing.Any = \
    #     pydantic.Field(None, description="Indicators backends")

    # indic_df: typing.Any = \
    #     pydantic.Field(None, description="Indicators values")
    
    def compute_signals(self, idx_buy, idx_sell, **kwrds):

        signals_raw = pd.Series(index=idx_buy.index,
                                dtype="float",
                                name="signal")

        signals_raw.loc[idx_buy] = 1
        signals_raw.loc[idx_sell] = 0

        return signals_raw



        
# class DMLongOptimizer(pydantic.BaseModel):

#     dm_cls: typing.Type[DMLong] = pydantic.Field(
#         ..., description="Decision model")

#     bt_cls: typing.Any = pydantic.Field(
#         ..., description="BT class")

#     # bt_cls: typing.Type[DMLong] = pydantic.Field(
#     #     ..., description="Decision model")
    
#     dm_params: dict = \
#         pydantic.Field({}, description="DM parameters to test")

#     brute_force_df: PandasDataFrame = \
#         pydantic.Field(None, description="Brute force optimization resulting data")

#     def brute_force(self, ohlcv_df,
#                     bt_params={},
#                     progress_mode=True,
#                     target_measure="perf_open_open",
#                     nb_trades_min=15,
#                     ):

#         dm_params_list = compute_combinations(**self.dm_params)

#         bt_eval_list = []
#         for params in tqdm.tqdm(dm_params_list,
#                                 disable=not progress_mode,
#                                 desc="Parameters",
#                                 ):

#             bt_cur = self.bt_cls(
#                 ohlcv_df=ohlcv_df,
#                 decision_model=self.dm_cls(params=params),
#                 **bt_params,
#             )

#             bt_cur.run()

#             bt_eval_list.append(dict(params, **bt_cur.perf.dict()))

#         self.brute_force_df = \
#             pd.DataFrame.from_records(bt_eval_list)\
#                         .sort_values(by=target_measure,
#                                      ascending=False)

#         idx_const_nb_trades = \
#             self.brute_force_df["nb_trades"] > nb_trades_min

#         brute_force_bis_df = \
#             self.brute_force_df.loc[idx_const_nb_trades]

#         dm_params_opt = \
#             brute_force_bis_df.iloc[0]\
#                               .loc[self.dm_params.keys()]\
#                               .to_dict()

#         return self.dm_cls(params=dm_params_opt)
