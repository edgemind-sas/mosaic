import logging
import sys
import pydantic
import typing
import pkg_resources
from datetime import datetime
import random
import string
import pandas as pd
import numpy as np
import plotly.express as px
import hashlib
import tqdm

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

from ..core import ObjMOSAIC
from .exchange import ExchangeBase
from .orders import OrderBase
#from ..bot.bot_base import BotBase
from ..db.db_base import DBBase
from ..decision_model.dm_base import DMBase
from ..invest_model.invest_model import InvestModelBase
from ..utils.data_management import fmt_currency


PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')
PandasSeries = typing.TypeVar('pandas.core.frame.Series')


class Portfolio(pydantic.BaseModel):

    bot_uid: str = pydantic.Field(
        None, description="Bot id")
    dt: datetime = pydantic.Field(
        None, description="Current timestamp")
    quote_price: datetime = pydantic.Field(
        None, description="Current quote price")
    quote_amount_init: float = pydantic.Field(
        1, description="Initial quote amount")
    quote_amount: float = pydantic.Field(
        0, description="Current quote amount")
    base_amount: float = pydantic.Field(
        0, description="Current base amount")
    quote_exposed: float = pydantic.Field(
        0, description="Current base amount in quote equivalent")
    quote_value: float = pydantic.Field(
        0, description="Current portfolio value in quote unit")
    performance: float = pydantic.Field(
        0, description="Current portfolio performance")

    def __init__(self, **data: typing.Any):
        super().__init__(**data)
        
        self.quote_amount = self.quote_amount_init
    
    def update_order(self, od):

        if od.side == "buy":

            self.quote_amount -= od.quote_amount
            self.base_amount += od.base_amount

        elif od.side == "sell":
            
            self.quote_amount += od.quote_amount
            self.base_amount -= od.base_amount

        else:

            raise ValueError(f"Unrecognized order side {od.side}")

    def update(self, fees=0):

        self.quote_exposed = \
            self.base_amount*self.quote_price*(1 - fees)

        self.quote_value = self.quote_amount + self.quote_exposed

        self.performance = self.quote_value/self.quote_amount_init

class DMConfig(pydantic.BaseModel):

    fit_horizon: int = pydantic.Field(
        None, description="Number of historical data used to adjust decision model")

    predict_horizon: int = pydantic.Field(
        None, description="Number of decisions before updating decision model")


class BotTrading(ObjMOSAIC):

    uid: str = pydantic.Field(
        None, description="Bot Unique id")
    
    name: str = pydantic.Field(
        None, description="Name of the trading architecture")

    symbol: str = pydantic.Field(
        ..., description="Trading symbol")

    timeframe: str = pydantic.Field(
        ..., description="Trading timeframe")

    dt_ohlcv_current: datetime = pydantic.Field(
        None, description="Session OHLCV current datetime")

    dt_ohlcv_closed: datetime = pydantic.Field(
        None, description="Session last closed OHLCV datetime")
    
    dt_session_start: datetime = pydantic.Field(
        None, description="Session starting date")

    dt_session_end: datetime = pydantic.Field(
        None, description="Session end date")

    dt_ohlcv_start: datetime = pydantic.Field(
        None, description="Session OHLCV starting tick")

    dt_ohlcv_end: datetime = pydantic.Field(
        None, description="Session OHLCV ending tick")

    quote_current: float = pydantic.Field(
        None, description="Current asset quotation")
    
    mode: str = pydantic.Field(
        None, description="Bot mode: 'backtest', 'livetest', 'live'")

    status: str = pydantic.Field(
        "waiting", description="Current bot status")

    status_comment: str = pydantic.Field(
        None, description="Status info (mostly when something goes wrong)")

    portfolio: Portfolio = pydantic.Field(
        None, description="Bot current portfolio")

    decision_model: DMBase = pydantic.Field(
        None, description="Decision model")

    invest_model: InvestModelBase = pydantic.Field(
        None, description="Invest model")

    # bot: BotBase = pydantic.Field(
    #     None, description="Bot")

    diff_thresh_buy_sell_orders: int = pydantic.Field(
        0, description="#buy/#sell orders diff limit. 0 means we can buy only if there are as many buy orders as sell orders")

    # nb_data_fit: int = pydantic.Field(
    #     None, description="Number of data used to fit decision model")

    # nb_data_pred: int = pydantic.Field(
    #     None, description="Number of data to be predict before fitting again")

    buy_orders_open: typing.Dict[str, OrderBase] = pydantic.Field(
        {}, description="Open buy orders")

    buy_orders_executed: typing.Dict[str, OrderBase] = pydantic.Field(
        {}, description="Executed buy orders")

    buy_orders_cancelled: typing.Dict[str, OrderBase] = pydantic.Field(
        {}, description="Cancelled buy orders")

    sell_orders_open: typing.Dict[str, OrderBase] = pydantic.Field(
        {}, description="Open sell orders")

    sell_orders_executed: typing.Dict[str, OrderBase] = pydantic.Field(
        {}, description="Executed sell orders")

    sell_orders_cancelled: typing.Dict[str, OrderBase] = pydantic.Field(
        {}, description="Cancelled sell orders")
    
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

    db: DBBase = pydantic.Field(
        None, description="Trading data backend")

    logger: typing.Any = pydantic.Field(
        None, description="Trading architecture logger")

    @pydantic.validator("buy_orders_open", pre=True, always=True)
    def validate_buy_orders_open(cls, value):
        if isinstance(value, list):
            return {key: {"uid": key, "side": "buy"} for key in value}
        elif isinstance(value, dict):
            return value
        else:
            raise ValueError("buy_orders_open should be a dict or a list")

    @pydantic.validator("buy_orders_executed", pre=True, always=True)
    def validate_buy_orders_executed(cls, value):
        if isinstance(value, list):
            return {key: {"uid": key, "side": "buy"} for key in value}
        elif isinstance(value, dict):
            return value
        else:
            raise ValueError("buy_orders_executed should be a dict or a list")

    @pydantic.validator("buy_orders_cancelled", pre=True, always=True)
    def validate_buy_orders_cancelled(cls, value):
        if isinstance(value, list):
            return {key: {"uid": key, "side": "buy"} for key in value}
        elif isinstance(value, dict):
            return value
        else:
            raise ValueError("buy_orders_cancelled should be a dict or a list")

    @pydantic.validator("sell_orders_open", pre=True, always=True)
    def validate_sell_orders_open(cls, value):
        if isinstance(value, list):
            return {key: {"uid": key, "side": "sell"} for key in value}
        elif isinstance(value, dict):
            return value
        else:
            raise ValueError("sell_orders_open should be a dict or a list")

    @pydantic.validator("sell_orders_executed", pre=True, always=True)
    def validate_sell_orders_executed(cls, value):
        if isinstance(value, list):
            return {key: {"uid": key, "side": "sell"} for key in value}
        elif isinstance(value, dict):
            return value
        else:
            raise ValueError("sell_orders_executed should be a dict or a list")

    @pydantic.validator("sell_orders_cancelled", pre=True, always=True)
    def validate_sell_orders_cancelled(cls, value):
        if isinstance(value, list):
            return {key: {"uid": key, "side": "sell"} for key in value}
        elif isinstance(value, dict):
            return value
        else:
            raise ValueError("sell_orders_cancelled should be a dict or a list")

    
    @pydantic.validator("status", pre=True, always=True)
    def validate_status(cls, value):
        if value not in ["waiting", "started", "finished", "aborted"]:
            raise ValueError("status must be 'waiting', 'started', 'finished' or 'aborted'")
        return value

    @pydantic.validator("mode", pre=True, always=True)
    def validate_mode(cls, value):
        if value not in ["backtest", "livetest", "live"]:
            raise ValueError("mode must be 'backtest', 'livetest', or 'live'")
        return value

    @property
    def base(self):
        return self.symbol.split("/")[0]

    @property
    def quote(self):
        return self.symbol.split("/")[1]

    def __init__(self, clean_db=False, **data: typing.Any):
        super().__init__(**data)

        self.exchange.connect()
        self.exchange.logger = self.logger
        
        if self.db:
            self.db.logger = self.logger
            self.db.connect()

    def signal_handler(self, signum, frame):
        self.abort("Abort by user")
        sys.exit(1)

    def dict(self, orders_ids=False, **kwrds):
        self_dict = super().dict(**kwrds)

        if orders_ids:

            for side in ["buy", "sell"]:
                for state in ["open", "executed", "cancelled"]:

                    order_key = f"{side}_orders_{state}"
                    self_dict[order_key] = list(getattr(self, order_key).keys())

        return self_dict
    
    def summary_light(self,
                      custom_format={},
                      ):

        summary = {}

        def id_fun(x):
            return x

        summary["id"] = self.uid
        summary["UID"] = custom_format.get("UID", id_fun)(self.uid)
        summary["Name"] = self.name
        summary["Mode"] = self.mode
        summary["Symbol"] = self.symbol
        summary["Timeframe"] = self.timeframe

        summary["Perf"] = f"{fmt_currency(self.portfolio.quote_value)} {self.quote}"

        if self.status != "waiting":
            progress = \
                (self.dt_ohlcv_current - self.dt_ohlcv_start)/\
                (self.dt_ohlcv_end - self.dt_ohlcv_start)
            progress = custom_format.get("Progress", id_fun)(progress)
            
            summary["Progress"] = progress if self.mode == "backtest" \
                else None

        summary["Status"] = self.status
            
        return summary
    
    def summary(self,
                custom_format={},
                ):

        summary = {}

        def id_fun(x):
            return x

        summary["id"] = self.uid
        summary["UID"] = custom_format.get("UID", id_fun)(self.uid)
        summary["Name"] = self.name
        summary["Mode"] = self.mode
        summary["Symbol"] = self.symbol
        summary["Timeframe"] = self.timeframe
        summary["DM"] = self.decision_model.__class__.__name__
        summary["IV"] = self.invest_model.__class__.__name__
        summary["Exchange"] = self.exchange.name
        summary["Quote"] = None if self.mode == "backtest" \
            else f"{fmt_currency(self.quote_current)} {self.quote}"

        summary["Perf"] = f"{fmt_currency(self.portfolio.quote_value)} {self.quote}"

        for side in ["buy", "sell"]:
            summary[f"#{side.capitalize()} orders"] = \
                " | ".join([f"({state[0].upper()}) {len(getattr(self, f'{side}_orders_{state}'))}"
                            for state in ["open", "executed", "cancelled"]])

        if self.status != "waiting":
            progress = \
                (self.dt_ohlcv_current - self.dt_ohlcv_start)/\
                (self.dt_ohlcv_end - self.dt_ohlcv_start)
            progress = custom_format.get("Progress", id_fun)(progress)
            
            summary["Progress"] = progress if self.mode == "backtest" \
                else None
            
        return summary

    def db_update(self):

        attr_excluded = {
            #"decision_model",
            #"invest_model",
            #"ohlcv_names",
            #"exchange",
            "db",
            "logger",
        }
        self_dict = self.dict(orders_ids=True,
                              exclude_none=True,
                              exclude=attr_excluded)
        if self.db:
            self.db.update(endpoint="bots",
                           data=self_dict,
                           index=["uid"])

    def db_get_portelio_history(self):
        pass
        
            
    def start(self, **kwards):

        self.dt_session_start = datetime.utcnow()
        # Generate an id by hashing session attributes + an optional name
        id_json = self.json(include={"name",
                                     "symbol",
                                     "timeframe",
                                     "mode",
                                     "dt_session_start"})
        self.uid = hashlib.sha256(id_json.encode("utf-8")).hexdigest()
        # Set status to "started"
        self.status = "started"
        self.portfolio.bot_uid = self.uid
        
        self.db_update()

        if self.logger:
            log_msg_str = f"""
Starting bot
Id              : {self.uid}
Name            : {self.name}
Base currency   : {self.base}
Quote currency  : {self.quote}
Timeframe       : {self.timeframe}
Session DT      : {self.dt_session_start}
Mode            : {self.mode}

Exchange
Name            : {self.exchange.name}
Fees            : {self.exchange.fees.maker}

Portfolio
quote_amount    : {self.portfolio.quote_amount}
base_amount     : {self.portfolio.base_amount}
"""
            self.logger.info(log_msg_str)

        # Start session !
        getattr(self, f"start_{self.mode}")(**kwards)
        
        self.finish()

    def finish(self):
        # Set date_end to the current UTC timestamp
        self.dt_session_end = datetime.utcnow()

        # Set status to "finished"
        self.status = "finished"

        if self.db:
            self.db_update()

        if self.logger:
            log_msg_str = f"Trading session {self.name} closed at {self.dt_session_end}"
            self.logger.info(log_msg_str)

    def abort(self, abort_message):
        """ Method used when the session est anormally interrupted
        """
        
        # Set date_end to the current UTC timestamp
        self.dt_session_end = datetime.utcnow()

        # Set status to "aborted"
        self.status = "aborted"
        self.status_comment = abort_message

        if self.db:
            self.db_update()

        if self.logger:
            log_msg_str = f"Trading bot {self.name} aborted at {self.dt_session_end} : {abort_message}"
            self.logger.info(log_msg_str)

            
    def start_backtest(self, progress_mode=False, data_dir=".", **kwrds):

        ohlcv_ori_df = \
            self.exchange.get_historic_ohlcv(
                date_start=self.dt_ohlcv_start,
                date_end=self.dt_ohlcv_end,
                symbol=self.symbol,
                timeframe=self.timeframe,
                index="datetime",
                data_dir=data_dir,
                force_reload=False,
                progress_mode=progress_mode
            )
        quote_current_s, ohlcv_closed_df = self.exchange.flatten_ohlcv(ohlcv_ori_df)

        #self.dt_ohlcv_start = ohlcv_closed_df.index[0]
        #self.dt_ohlcv_end = ohlcv_closed_df.index[-1]

        
        tdelta = self.exchange.timeframe_to_timedelta(self.timeframe)
        # ohlcv_cur_df = \
        #     self.exchange.get_last_ohlcv(closed=False)

        self.dt_ohlcv_closed = None

        with tqdm.tqdm(total=len(quote_current_s), disable=not progress_mode) as pbar:
            for self.dt_ohlcv_current, self.quote_current in quote_current_s.items():
                
                if self.dt_ohlcv_current != self.dt_ohlcv_closed:
                    dt_start = self.dt_ohlcv_current - tdelta*self.decision_model.bw_length
                    ohlcv_cur_df = ohlcv_closed_df.loc[dt_start:self.dt_ohlcv_current]
                    signal = self.decision_model.compute(ohlcv_cur_df, **kwrds)\
                        .replace({np.nan: None})\
                        .loc[self.dt_ohlcv_current]

                    if self.logger:
                        self.logger.debug(f"DT current:     {self.dt_ohlcv_current}\n"
                                          f"Quote price:    {fmt_currency(self.quote_current)} {self.quote}\n"
                                          f"DT last closed: {self.dt_ohlcv_closed}\n"
                                          f"signal:         {signal}\n"
                                          f"OHLCV:\n"
                                          f"{ohlcv_cur_df}")

                    #decision = self.bot.tick(quote_cur)
                    if signal is not None:

                        if signal == 1:
                            getattr(self, "buy")()
                        else:
                            getattr(self, "sell")()

                else:
                    if self.logger:
                        self.logger.debug(f"DT current:     {self.dt_ohlcv_current}\n"
                                          f"Quote price:    {fmt_currency(self.quote_current)} {self.quote}\n"
                                          f"DT last closed: {self.dt_ohlcv_closed}\n")

                # Update orders
                self.update_orders()
                
                # Updating portfolio
                self.portfolio.dt = self.dt_ohlcv_current
                self.portfolio.quote_price = self.quote_current
                self.portfolio.update(fees=self.exchange.fees.maker)
                if self.db:
                    self.db.update(endpoint="portfolio",
                                   data=self.portfolio.dict(),
                                   index=["bot_uid", "dt"])

                    if (pbar.n % 1000) == 0:
                        self.db_update()
                    
                # Updating variables
                #ipdb.set_trace()               
                self.dt_ohlcv_closed = self.dt_ohlcv_current
                pbar.update()
            
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


    def get_nb_buy_sell_orders_diff(self):

        nb_buy_orders = \
            len(self.buy_orders_open) + \
            len(self.buy_orders_executed)
        nb_sell_orders = \
            len(self.sell_orders_open) + \
            len(self.sell_orders_executed)

        return nb_buy_orders - nb_sell_orders

    
    def is_buy_allowed(self):
        
        return self.get_nb_buy_sell_orders_diff() <= self.diff_thresh_buy_sell_orders

    def is_sell_allowed(self):

        return self.get_nb_buy_sell_orders_diff() == self.diff_thresh_buy_sell_orders + 1
    
    def buy(self, **kwrds):

        if self.is_buy_allowed():
            order_specs = dict(
                cls="OrderMarket",
                bot_uid=self.uid,
                dt_open=self.dt_ohlcv_current,
                fees=self.exchange.fees.maker,
                side="buy",
                quote_amount=self.invest_model.get_buy_quote_amount(self.portfolio),
            )

            order = OrderBase.from_dict(order_specs)
            order.db = self.db
            
            self.buy_orders_open[order.uid] = order

        else:

            if self.logger:
                self.logger.debug("Buy order not allowed : Buy/Sell threshold not respected")

    def sell(self, **kwrds):

        if self.is_sell_allowed():

            order_specs = dict(
                cls="OrderMarket",
                bot_uid=self.uid,
                dt_open=self.dt_ohlcv_current,
                fees=self.exchange.fees.maker,
                side="sell",
                base_amount=self.invest_model.get_sell_base_amount(self.portfolio),
            )

            order = OrderBase.from_dict(order_specs)
            order.db = self.db

            self.sell_orders_open[order.uid] = order
        else:

            if self.logger:
                self.logger.debug("Sell order not allowed : Buy/Sell threshold not respected")


    def update_orders(self):

        # Here list is important in order to work on a
        # copy of the dict keys because we modify the structure
        # of buy_orders_open while scanning it.
        for od_uid in list(self.buy_orders_open.keys()):
            od = self.buy_orders_open[od_uid]
            if od.is_executable():
                res = od.execute(dt=self.dt_ohlcv_current,
                                 quote_price=self.quote_current)
                self.portfolio.update_order(od)
                self.buy_orders_executed[od_uid] = self.buy_orders_open.pop(od_uid)


        for od_uid in list(self.sell_orders_open.keys()):
            od = self.sell_orders_open[od_uid]
            if od.is_executable():
                res = od.execute(dt=self.dt_ohlcv_current,
                                 quote_price=self.quote_current)
                self.portfolio.update_order(od)
                self.sell_orders_executed[od_uid] = self.sell_orders_open.pop(od_uid)

                
                    
