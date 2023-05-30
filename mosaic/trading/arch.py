import logging
import sys
import pydantic
import typing
import pkg_resources
import datetime
import pandas as pd
import numpy as np
import plotly.express as px

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

from .exchange import ExchangeBase
from ..core import ObjMOSAIC
from ..bot.bot_base import BotBase

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')
PandasSeries = typing.TypeVar('pandas.core.frame.Series')




class DMConfig(pydantic.BaseModel):

    fit_horizon: int = pydantic.Field(
        None, description="Number of historical data used to adjust decision model ")

    predict_horizon: int = pydantic.Field(
        None, description="Number of decisions before updating decision model")


class TradingArch(ObjMOSAIC):

    name: str = pydantic.Field(
        None, description="Name of the trading architecture")

    symbol: str = pydantic.Field(
        ..., description="Trading symbol")

    base: str = pydantic.Field(None, description="Base asset symbol")

    quote: str = pydantic.Field(None, description="Quote asset symbol")

    timeframe: str = pydantic.Field(
        ..., description="Trading timeframe")
    
    bot: BotBase = pydantic.Field(
        None, description="Bot")

    nb_data_fit: int = pydantic.Field(
        None, description="Number of data used to fit decision model")

    nb_data_pred: int = pydantic.Field(
        None, description="Number of data to be predict before fitting again")

    
    # ohlcv_df: PandasDataFrame = pydantic.Field(
    #     None, description="BT OHLCV data")

    # asset_norm: PandasSeries = pydantic.Field(
    #     None, description="Asset evolution normalized over the period")

    # dm_config: DMConfig = pydantic.Field(
    #     DMConfig(), description="Decision Model learning parameters")

    ohlcv_names: dict = pydantic.Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")

    exchange: ExchangeBase = pydantic.Field(
        None, description="Trading architecture exchange")

    @pydantic.validator('base', always=True)
    def set_default_base(cls, base, values):
        return values.get("symbol").split("/")[0]

    @pydantic.validator('quote', always=True)
    def set_default_quote(cls, quote, values):
        return values.get("symbol").split("/")[1]

    
    def start_session_offline(self,
                              progress_mode=True,
                              verbose_mode=False,
                              **kwrds):

        session_dt_cur = datetime.datetime.utcnow()
        # session_dt_cur = \
        #     pd.to_datetime(round(session_ts_cur/1000)*1000, unit="ms")

        if verbose_mode:
            log_msg_str = f"""
Starting offline trading session : {self.name}
Base currency  : {self.base}
Quote currency : {self.quote}
Timeframe      : {self.timeframe}
Session DT     : {session_dt_cur}

Exchange
Name           : {self.exchange.name}
Fees           : {self.exchange.fees.maker}
"""
            sys.stdout.write(log_msg_str)

        quote_current_s, ohlcv_closed_df = self.exchange.get_ohlcv()
        # ohlcv_cur_df = \
        #     self.exchange.get_last_ohlcv(closed=False)

        

        for dt_cur, quote_cur in quote_current_s.iteritems():

            # ADD BOT
            
            ipdb.set_trace()

        
        return
        
        
        iter_max = int(np.ceil((nb_data - nb_data_fit)/nb_data_pred))

        idx_fit_min = 0
        idx_fit_max = self.nb_data_fit
        ohlcv_fit_df = ohlcv_df.iloc[idx_fit_min:idx_fit_max]
        fit_dt_min = ohlcv_fit_df.index[0]
        fit_dt_max = ohlcv_fit_df.index[-1]

        log_msg_str = f"""
Fitting parameters
Data range : {fit_dt_min} -> {fit_dt_max} [idx: {idx_fit_min} -> {idx_fit_max}]")
"""
        # TODO: BE CAREFUL WITH OFFSET
        # TODO: FAIRE LE CAS SANS TUNING : nb_data_fit=0
        dm_fit, tuning_df_cur = \
            self.bot.dm_tuning_sa(
                ohlcv_fit_df,
                neighbor_specs=dm_param_specs,
                run_test_params=dict(fees=self.exchange.fees.maker),
                **self.tuning_params,
            )
        
        
        ipdb.set_trace()

        dm_param_specs = dm_param_init_specs.copy()

        tuning_df_list = []
        for i in tqdm.tqdm(range(iter_max),
                           desc="Update DM"):

            ohlcv_fit_df = ohlcv_df.iloc[idx_fit_min:idx_fit_max]

            fit_dt_min = ohlcv_fit_df.index[0]
            fit_dt_max = ohlcv_fit_df.index[-1]


            dm_fit, tuning_df_cur = mbo.BotLong(
                decision_model=mdm.DML_RSI2(offset=1,
                                            params=bot_rsi.decision_model.params),
            ).dm_tuning_sa(ohlcv_fit_df,
                           neighbor_specs=dm_param_specs,
                           run_test_params=run_test_params,
                           bot_params=bot_params,
                           **tuning_params,
                           )

            tuning_df_cur["fit_dt_min"] = fit_dt_min
            tuning_df_cur["fit_dt_max"] = fit_dt_max

            tuning_df_list.append(tuning_df_cur)

            print(f"> dm_fit params :\n{dm_fit.params}")

            dm_param_specs = dm_param_live_specs.copy()

            print("\nPrediction")

            idx_pred_min = max(idx_fit_max - dm_fit.bw_window, 0)
            idx_pred_max = min(idx_fit_max + nb_data_pred, nb_data)

            ohlcv_pred_df = ohlcv_df.iloc[idx_pred_min:idx_pred_max]

            print(f"> Data range : {ohlcv_pred_df.index[0]} -> {ohlcv_pred_df.index[-1]} [idx: {idx_pred_min} -> {idx_pred_max}] [Backward window: {dm_fit.bw_window}]")

            # ohlcv_cur_df = ohlcv_df.iloc[idx_min:idx_max]

            # TODO: Ajouter les ts_start et ts_end pour fit et pred
            #ipdb.set_trace()

            bot_rsi.decision_model = \
                dm_fit.__class__(
                    offset=1,
                    params=dm_fit.params)
            bot_rsi.run_test(ohlcv_pred_df,
                             update=True,
                             **run_test_params)

            print(f"> Last trades:\n{bot_rsi.trades_test.tail(5)}")

            print(f"> Results:\n{bot_rsi.perf_test}")

            idx_fit_min += nb_data_pred
            idx_fit_max += nb_data_pred


