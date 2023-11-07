import logging
import sys
import pydantic
import typing
import pkg_resources
from datetime import datetime, timedelta
import random
import string
import time
import pytz
from tzlocal import get_localzone
import pandas as pd
import numpy as np
import plotly.express as px
import hashlib
import tqdm
from textwrap import dedent, indent

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401
if 'colored' in installed_pkg:
    import colored # noqa: F401

from ..core import ObjMOSAIC
from .orders import OrderBase, OrderMarket
from .exchange import ExchangeBase
#from ..bot.bot_base import BotBase
from ..db.db_base import DBBase
from ..decision_model.dm_base import DMBase
from ..invest_model.invest_model import InvestModelBase, InvestLongModel
from ..utils.data_management import \
    DSOHLCV, \
    fmt_currency, \
    timeframe_to_seconds, \
    timeframe_to_timedelta
from ..utils.io import \
    update_console
from ..version import __version__ as MOSAIC_VERSION

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')
PandasSeries = typing.TypeVar('pandas.core.frame.Series')


class Portfolio(pydantic.BaseModel):
    """Keeps track of the current state of the trading portfolio.
    Includes current performance metrics and current amounts in base and quote currency.
    """
    
    bot_uid: str = pydantic.Field(
        None, description="Bot id")
    fees_taker: float = pydantic.Field(
        0, description="Fees taker to be considered to compute quote value")

    dt: datetime = pydantic.Field(
        None, description="Current timestamp")
    last_buy_order_dt: datetime = pydantic.Field(
        None, description="Last buy order timestamp")
    last_sell_order_dt: datetime = pydantic.Field(
        None, description="Last buy order timestamp")
    quote_price_init: float = pydantic.Field(
        None, description="Initial quote price")
    quote_price: float = pydantic.Field(
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
    asset_performance: float = pydantic.Field(
        0, description="Current asset performance")
    intratrade_duration_cum: int = pydantic.Field(
        0, description="Cumulative trade duration in seconds (between consecutive buy and sell orders)")
    intertrade_duration_cum: int = pydantic.Field(
        0, description="Cumulative inter trade duration in seconds (between consecutive sell and buy orders)")
    nb_buy_orders: int = pydantic.Field(
        0, description="Nomber of buy orders")
    nb_sell_orders: int = pydantic.Field(
        0, description="Nomber of sell orders")
    performance: float = pydantic.Field(
        0, description="Current portfolio performance")

    @property
    def intratrade_duration_mean(self):
        return timedelta(seconds=self.intratrade_duration_cum)/self.nb_buy_orders \
            if self.nb_buy_orders > 0 else None

    @property
    def intertrade_duration_mean(self):
        return timedelta(seconds=self.intertrade_duration_cum)/self.nb_buy_orders \
            if self.nb_buy_orders > 0 else None

    
    def __init__(self, **data: typing.Any):
        super().__init__(**data)

        self.reset()

    def __str__(self, exclude_bot_uid=False):

        indent_str = " "*4
        
        if exclude_bot_uid:
            attrs_liststr = []
        else:
            attrs_liststr = [f"Bot UID: {self.bot_uid}"]

        attrs_liststr.append(f"Time: {self.dt}")

        attrs_liststr.append(f"Initial quote amount: {fmt_currency(self.quote_amount_init)}")
        attrs_liststr.append(f"Quote amount: {fmt_currency(self.quote_amount)}")
        attrs_liststr.append(f"Base amount: {fmt_currency(float(self.base_amount))}")
        attrs_liststr.append(f"Quote exposed: {fmt_currency(self.quote_exposed)}")
        attrs_liststr.append(f"Quote value: {fmt_currency(self.quote_value)}")

        attrs_liststr.append("KPI")
        attrs_liststr.append(
            indent(f"Asset performance: {self.asset_performance:.3}",
                   indent_str))
        attrs_liststr.append(
            indent(f"Strategy performance: {self.format_performance()}",
                   indent_str))
        attrs_liststr.append(
            indent(f"# orders executed: {self.nb_buy_orders} buys | {self.nb_sell_orders} sells",
                   indent_str))
        if self.intertrade_duration_mean:
            attrs_liststr.append(
                indent(f"Mean intertrade duration: {self.intertrade_duration_mean}",
                       indent_str))
        if self.intratrade_duration_mean:
            attrs_liststr.append(
                indent(f"Mean intratrade duration: {self.intratrade_duration_mean}",
                       indent_str))

        return "\n".join(attrs_liststr)

    def __repr__(self):
        return self.__str__()

    def format_performance(self):
        performance_str = f"{self.performance:.3}"
        if 'colored' in installed_pkg:
            if self.performance > 1 and self.performance > self.asset_performance:
                return colored.stylize(performance_str, colored.fg("green"))
            elif self.performance > 1 and self.performance <= self.asset_performance:
                return colored.stylize(performance_str, colored.fg("blue"))
            elif self.performance < 1 and self.performance > self.asset_performance:
                return colored.stylize(performance_str, colored.fg("magenta"))
            else:
                return colored.stylize(performance_str, colored.fg("red"))

        return performance_str

        
    def reset(self):
        
        self.quote_amount = self.quote_amount_init
        self.base_amount = 0.0
        self.quote_price = None
        self.quote_price_init = None
        self.dt = None
        self.update()
        
    def update_order(self, od):

        if od.side == "buy":

            self.quote_amount -= od.quote_amount
            self.base_amount += od.base_amount
            self.nb_buy_orders += 1
            self.last_buy_order_dt = self.dt
            if self.last_sell_order_dt:
                self.intertrade_duration_cum += \
                    (self.last_buy_order_dt - self.last_sell_order_dt).total_seconds()

        elif od.side == "sell":
            
            self.quote_amount += od.quote_amount
            self.base_amount -= od.base_amount
            self.nb_sell_orders += 1
            self.last_sell_order_dt = self.dt
            if self.last_buy_order_dt:
                self.intratrade_duration_cum += \
                    (self.last_sell_order_dt - self.last_buy_order_dt).total_seconds()

        else:

            raise ValueError(f"Unrecognized order side {od.side}")

        self.update()

    def update(self):

        self.quote_exposed = 0 if self.quote_price is None \
            else self.base_amount*self.quote_price*(1 - self.fees_taker)

        self.quote_value = self.quote_amount + self.quote_exposed

        self.asset_performance = 0 if self.quote_price_init is None \
            else self.quote_price/self.quote_price_init

        self.performance = self.quote_value/self.quote_amount_init

    
class BotTrading(ObjMOSAIC):
    """
    BotTrading handles automated trading operations.  It supports various backtesting and live trading modes 
    and is capable of interacting with various data sources and decision models.

    Attributes:
        mosaic_version (str): The MOSAIC version being used.
        uid (str): A unique identifier for the bot.
        name (str): A descriptive name for the bot.
        ds_trading (DSOHLCV): The primary data source used for real-time trading or backtesting.
        ds_dm (DSOHLCV): The data source specifically used for the decision-making model.
        ds_fit (DSOHLCV): The data source used for model fitting or optimization.
        dt_ohlcv_current (datetime): The current datetime for the Session OHLCV.
        dt_ohlcv_closed (datetime): The last closed datetime for the Session OHLCV.
        dt_session_start (datetime): The start date of the session.
        dt_session_end (datetime): The end date of the session.
        quote_current (float): The current asset quotation.
        bt_buy_on (str): The backtest buy price hypothesis.
        bt_sell_on (str): The backtest sell price hypothesis.
        mode (str): The bot mode. Can be 'btfast', 'btclassic', 'livetest', or 'live'.
        status (str): The current status of the bot.
        status_comment (str): Additional status info, mostly used when something goes wrong.
        portfolio (Portfolio): The current portfolio of the bot.
        decision_model (DMBase): The decision model being used.
        order_model (OrderBase): The order model being used.
        invest_model (InvestModelBase): The investment model being used.
        diff_thresh_buy_sell_orders (int): Limit for buy/sell orders diff. 0 means we can buy only if there 
            are as many buy orders as sell orders.
        orders_open (dict): A dictionary holding the open orders.
        orders_executed (dict): A dictionary holding the executed orders.
        orders_cancelled (dict): A dictionary holding the cancelled orders.
        ohlcv_names (dict): A dictionary mapping of OHLCV variable names.
        progress (float): The bot's progress in backtest mode.
        ohlcv_fit_dfd (dict): The bot's modeling data for fitting.
        ohlcv_dm_dfd (dict): The bot's modeling data for decision making.
        ohlcv_trading_dfd (dict): The bot's trading modeling data.
        db (DBBase): The bot's status data backend.
        db_trace (DBBase): The bot's trading data backend.
        logger (any): Used for logging architecture.

    """
    mosaic_version: str = pydantic.Field(
        MOSAIC_VERSION, description="MOSAIC version")
    
    uid: str = pydantic.Field(
        None, description="Unique identifier for the bot")
    
    name: str = pydantic.Field(
        None, description="Descriptive name of the bot",
        user_input=True,
    )

    ds_trading: DSOHLCV = pydantic.Field(
        ..., description="Primary data source used for real-time trading or backtesting")

    ds_dm: DSOHLCV = pydantic.Field(
        None, description="Data source specifically used for decision-making model")

    ds_fit: DSOHLCV = pydantic.Field(
        None, description="Data source used for model fitting or optimization")
    
    dt_ohlcv_current: datetime = pydantic.Field(
        None, description="Session OHLCV current datetime")

    dt_ohlcv_closed: datetime = pydantic.Field(
        None, description="Session last closed OHLCV datetime")
    
    dt_session_start: datetime = pydantic.Field(
        None, description="Session starting date")

    dt_session_end: datetime = pydantic.Field(
        None, description="Session end date")

    quote_current: float = pydantic.Field(
        None, description="Current asset quotation")

    bt_buy_on: str = pydantic.Field(
        "open", description="Backtest buy price hypothesis",
        user_input=["open", "high", "low", "close"],
    )

    bt_sell_on: str = pydantic.Field(
        "open", description="Backtest sell price hypothesis",
        user_input=["open", "high", "low", "close"],
    )

    mode: str = pydantic.Field(
        'btfast', description="Bot mode: 'btfast', 'btclassic', 'livetest', 'live'",
        user_input=['btfast', 'btclassic', 'livetest', 'live'],
    )

    status: str = pydantic.Field(
        "waiting", description="Current bot status")

    status_comment: str = pydantic.Field(
        None, description="Status info (mostly when something goes wrong)")

    portfolio: Portfolio = pydantic.Field(
        Portfolio(), description="Bot current portfolio")

    decision_model: DMBase = pydantic.Field(
        None, description="Decision model")

    order_model: OrderBase = pydantic.Field(
        OrderMarket(), description="Order model")

    invest_model: InvestModelBase = pydantic.Field(
        InvestLongModel(), description="Invest model")

    diff_thresh_buy_sell_orders: int = pydantic.Field(
        0, description="#buy/#sell orders diff limit. 0 means we can buy only if there are as many buy orders as sell orders")

    orders_open: typing.Dict[str, OrderBase] = pydantic.Field(
        {}, description="Open orders")

    orders_executed: typing.Dict[str, OrderBase] = pydantic.Field(
        {}, description="Executed orders")

    orders_cancelled: typing.Dict[str, OrderBase] = pydantic.Field(
        {}, description="Cancelled orders")

    ohlcv_names: dict = pydantic.Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")
    
    progress: float = pydantic.Field(
        0, description="Bot progress in backtest mode")

    ohlcv_fit_dfd: dict = pydantic.Field(
        {}, description="Bot modeling data for fitting")

    ohlcv_dm_dfd: dict = pydantic.Field(
        {}, description="Bot modeling data for decision making")

    ohlcv_trading_dfd: dict = pydantic.Field(
        {}, description="Bot trading modeling data")

    exchange: ExchangeBase = pydantic.Field(
        None, description="Trading architecture exchange")
    
    db: DBBase = pydantic.Field(
        None, description="Bot status data backend")

    db_trace: DBBase = pydantic.Field(
        None, description="Bot trading data backend")
    
    logger: typing.Any = pydantic.Field(
        None, description="Trading architecture logger")

    @pydantic.validator("orders_open", pre=True, always=True)
    def validate_orders_open(cls, value):
        if isinstance(value, list):
            return {key: {"uid": key} for key in value}
        elif isinstance(value, dict):
            return value
        else:
            raise ValueError("orders_open should be a dict or a list")

    @pydantic.validator("orders_executed", pre=True, always=True)
    def validate_orders_executed(cls, value):
        if isinstance(value, list):
            return {key: {"uid": key} for key in value}
        elif isinstance(value, dict):
            return value
        else:
            raise ValueError("orders_executed should be a dict or a list")

    @pydantic.validator("orders_cancelled", pre=True, always=True)
    def validate_orders_cancelled(cls, value):
        if isinstance(value, list):
            return {key: {"uid": key} for key in value}
        elif isinstance(value, dict):
            return value
        else:
            raise ValueError("orders_cancelled should be a dict or a list")

    
    @pydantic.validator("status", pre=True, always=True)
    def validate_status(cls, value):
        if value not in ["waiting", "started", "finished", "aborted"]:
            raise ValueError("status must be 'waiting', 'started', 'finished' or 'aborted'")
        return value

    @pydantic.validator("mode", pre=True, always=True)
    def validate_mode(cls, value):
        valid_modes = ["btfast", "btclassic", "livetest", "live"]
        if value not in valid_modes:
            raise ValueError("Mode must be in {', '.join(valid_modes)}")
        return value

    @property
    def symbol(self):
        return self.ds_trading.symbol

    @property
    def timeframe(self):
        return self.ds_trading.timeframe
    
    @property
    def base(self):
        return self.symbol.split("/")[0]

    @property
    def quote(self):
        return self.symbol.split("/")[1]

    @property
    def session_duration(self):
        return self.dt_session_end - self.dt_session_start \
            if self.dt_session_end else None
    
    @property
    def ds_trading_code(self):
        return f"{self.ds_trading.symbol}{self.ds_trading.timeframe}"\
            f"{self.ds_trading.dt_s}{self.ds_trading.dt_e}"
    
    @property
    def ds_dm_code(self):
        return f"{self.ds_dm.symbol}{self.ds_dm.timeframe}"\
            f"{self.ds_dm.dt_s}{self.ds_dm.dt_e}"
    
    @property
    def ds_fit_code(self):
        return f"{self.ds_fit.symbol}{self.ds_fit.timeframe}"\
            f"{self.ds_fit.dt_s}{self.ds_fit.dt_e}"

    
    @property
    def nb_buy_orders_open(self):
        return len([od for od in self.orders_open.values() if od.side == "buy"])
    @property
    def nb_buy_orders_executed(self):
        return len([od for od in self.orders_executed.values() if od.side == "buy"])
    @property
    def nb_sell_orders_open(self):
        return len([od for od in self.orders_open.values() if od.side == "sell"])
    @property
    def nb_sell_orders_executed(self):
        return len([od for od in self.orders_executed.values() if od.side == "sell"])

    def __init__(self, clean_db=False, **data: typing.Any):
        super().__init__(**data)

        self.exchange.connect()
        self.exchange.logger = self.logger

        if self.db:
            self.db.logger = self.logger
            self.db.connect()

        if self.db_trace:
            self.db_trace.logger = self.logger
            self.db_trace.connect()
        elif self.db:
            self.db_trace = self.db

    def reset(self):

        attr_reset = [
            "dt_ohlcv_current",
            "dt_ohlcv_closed",
            "dt_session_start",
            "dt_session_end",
            "quote_current",
            "orders_open",
            "orders_executed",
            "orders_cancelled",
            "progress",
        ]
        for attr in attr_reset:
            setattr(self, attr, self.__fields__[attr].default)

        self.portfolio.reset()
            
    def signal_handler(self, signum, frame):
        self.abort("Abort by user")
        sys.exit(1)

    def dict(self, orders_ids=False, **kwrds):

        exclude_attr = {
            "ohlcv_fit_dfd",
            "ohlcv_dm_dfd",
            "ohlcv_trading_dfd",
        }

        if kwrds["exclude"]:
            [kwrds["exclude"].add(attr) for attr in exclude_attr]
        else:
            kwrds["exclude"] = exclude_attr
            
        self_dict = super().dict(**kwrds)

        if orders_ids:

            for state in ["open", "executed", "cancelled"]:
                order_key = f"orders_{state}"
                self_dict[order_key] = list(getattr(self, order_key).keys())

        return self_dict

    def __str__(self):

        indent_str = 4*" "
        
        repr_liststr = []
        repr_liststr.append("Bot")
        attrs_liststr = [
            f"MOSAIC version: {MOSAIC_VERSION}",
            f"ID: {self.uid}",
            f"Name: {self.name}",
            f"Symbol: {self.symbol}",
            f"Timeframe: {self.timeframe}",
            f"Mode: {self.mode}",
        ]
        repr_liststr.append(
            indent("\n".join(attrs_liststr), indent_str)
        )
        if self.mode.startswith("bt"):
            repr_liststr.append(
                indent(f"Buy on: {self.bt_buy_on}", 2*indent_str)
            )
            repr_liststr.append(
                indent(f"Sell on: {self.bt_sell_on}", 2*indent_str)
            )

        # Session
        repr_liststr.append("")
        repr_liststr.append("Session")
        if self.dt_session_start:
            repr_liststr.append(
                indent(f"Started at: {self.dt_session_start}", indent_str)
            )
        if self.dt_session_end:
            repr_liststr.append(
                indent(f"Ended at: {self.dt_session_end}", indent_str)
            )
            repr_liststr.append(
                indent(f"Duration: {self.session_duration}", indent_str)
            )
            if self.mode.startswith("bt"):
                repr_liststr.append(
                    indent(f"OHLCV period: {self.ds_trading.dt_e - self.ds_trading.dt_s} | "
                           f"{self.ds_trading.dt_s} -> {self.ds_trading.dt_e}", indent_str)
                )
                

        else:
            repr_liststr.append(
                indent(f"DT OHLCV current: {self.dt_ohlcv_current}",
                       indent_str)
            )
            repr_liststr.append(
                indent(f"DT OHLCV closed: {self.dt_ohlcv_closed}",
                       indent_str)
            )
            
        repr_liststr.append(
            indent(f"Current quote price: {fmt_currency(self.quote_current)} {self.quote}",
                   indent_str)
        )
        repr_liststr.append(
            indent(f"# Open orders: {len(self.orders_open)}", indent_str)
        )
        for od in self.orders_open.values():
            repr_liststr.append(
                indent(f"{od.repr(sep=' ')}", indent_str)
            )
        
        repr_liststr.append(
            indent(f"# Cancelled orders: {len(self.orders_cancelled)}", indent_str)
        )

        repr_liststr.append("")
        repr_liststr.append("Exchange")
        repr_liststr.append(
            indent(self.exchange.__str__(), indent_str)
        )
        
        repr_liststr.append("")
        repr_liststr.append("Portfolio")
        repr_liststr.append(
            indent(self.portfolio.__str__(exclude_bot_uid=True), indent_str)
        )
        return "\n".join(repr_liststr)
        
    def __repr__(self):
        return self.__str__()
        
    
    def summary_header(self):
        return self.__str__()

    def summary_live(self,
                     custom_format={},
                     ):

        summary_str = f"""
        Trading
        Current time    : {self.dt_ohlcv_current}
        Quote price     : {fmt_currency(self.quote_current)} {self.quote}
        performance     : {self.portfolio.performance}
        """
        
        return self.summary_header() + '\n' + dedent(summary_str)
    

    def progress_update(self):

        if self.mode.startswith("bt") and (self.status != "waiting"):
            self.progress = \
                (self.dt_ohlcv_current - self.ds_trading.dt_s)/\
                (self.ds_trading.dt_e - self.ds_trading.dt_s)
        else:
            self.progress = None    


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
        
    def start(self, **kwrds):
        local_tz = pytz.timezone(get_localzone().key)
        
        self.dt_session_start = local_tz.localize(datetime.now())

        if not self.uid:
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

        # Init fees
        self.exchange.set_trading_fees(self.symbol)
        self.portfolio.fees_taker = self.exchange.fees_rates.taker
        
        #self.db_update()
        if self.logger:
            self.logger.info(self.summary_header())

        self.fit_dm(**kwrds)

        if self.ds_dm is None:
            self.ds_dm = self.ds_trading
            
        # Start session !
        getattr(self, f"start_{self.mode}")(**kwrds)
        
        self.finish()

    def finish(self):
        
        # Set date_end to the current timestamp
        local_tz = pytz.timezone(get_localzone().key)
        self.dt_session_end = local_tz.localize(datetime.now())

        # Set status to "finished"
        self.status = "finished"
        self.progress = 1
        
        #if self.db:
            #self.db_update()

        if self.logger:
            log_msg_str = f"Trading session {self.name} closed at {self.dt_session_end}"
            self.logger.info(log_msg_str)

    def abort(self, abort_message):
        """ Method used when the session est anormally interrupted
        """
        
        # Set date_end to the current timestamp
        local_tz = pytz.timezone(get_localzone().key)
        self.dt_session_end = local_tz.localize(datetime.now())

        # Set status to "aborted"
        self.status = "aborted"
        self.status_comment = abort_message

        if self.db:
            self.db_update()

        if self.logger:
            log_msg_str = f"Trading bot {self.name} aborted at {self.dt_session_end} : {abort_message}"
            self.logger.info(log_msg_str)

    def fit_dm(self, progress_mode=False, data_dir=".", **kwrds):

        if self.logger:
            log_msg_str = "Fitting decision model"
            self.logger.info(log_msg_str)

        if not (self.ds_fit_code in self.ohlcv_fit_dfd.keys()):
            self.ohlcv_fit_dfd[self.ds_fit_code] = \
                self.exchange.get_historic_ohlcv(
                    date_start=self.ds_fit.dt_s,
                    date_end=self.ds_fit.dt_e,
                    symbol=self.ds_fit.symbol,
                    timeframe=self.ds_fit.timeframe,
                    index="datetime",
                    data_dir=data_dir,
                    force_reload=False,
                    progress_mode=progress_mode,
                )

        ohlcv_fit_df = self.ohlcv_fit_dfd[self.ds_fit_code]
            
        self.decision_model.fit(ohlcv_fit_df)
        
    def start_btfast(self, progress_mode=False, data_dir=".", **kwrds):

        if self.logger:
            self.logger.info("Getting trading data")

        if not (self.ds_trading_code in self.ohlcv_trading_dfd.keys()):
            self.ohlcv_trading_dfd[self.ds_trading_code] = \
                self.exchange.get_historic_ohlcv(
                    date_start=self.ds_trading.dt_s,
                    date_end=self.ds_trading.dt_e,
                    symbol=self.ds_trading.symbol,
                    timeframe=self.timeframe,
                    index="datetime",
                    data_dir=data_dir,
                    force_reload=False,
                    progress_mode=progress_mode,
                )
        ohlcv_trading_df = self.ohlcv_trading_dfd[self.ds_trading_code]
        self.portfolio.quote_price_init = \
            ohlcv_trading_df[self.ohlcv_names.get("close")].iloc[0]
                
        if self.logger:
            self.logger.info("Getting decision model data")

        if self.ds_trading == self.ds_dm:
            ohlcv_dm_df = ohlcv_trading_df
        else:
            if not (self.ds_dm_code in self.ohlcv_dm_dfd.keys()):
                self.ohlcv_dm_dfd[self.ds_dm_code] = \
                    self.exchange.get_historic_ohlcv(
                        date_start=self.ds_dm.dt_s,
                        date_end=self.ds_dm.dt_e,
                        symbol=self.ds_dm.symbol,
                        timeframe=self.timeframe,
                        index="datetime",
                        data_dir=data_dir,
                        force_reload=False,
                        progress_mode=progress_mode
                    )
            ohlcv_dm_df = self.ohlcv_dm_dfd[self.ds_dm_code]
        
        decisions_df = \
            self.decision_model.predict(ohlcv_dm_df.shift(1), **kwrds)

        idx_pass = decisions_df["decision"] == "pass"

        decision_s = decisions_df["decision"].loc[~idx_pass]
        decision_s = decision_s.loc[decision_s.shift() != decision_s]

        idx_buy = decision_s == "buy"
        dt_buy = decision_s.index[idx_buy]

        idx_sell = decision_s == "sell"
        if len(dt_buy) > 0:
            idx_sell &= (decision_s.index >= dt_buy[0])
        dt_sell = decision_s.index[idx_sell]

        orders_list = []
        for self.dt_ohlcv_current in tqdm.tqdm(dt_buy,
                                               disable=not progress_mode,
                                               desc="Buy orders",
                                               ):
                                               
            order = self.buy(no_db=True)
            orders_list.append(order)

        for self.dt_ohlcv_current in tqdm.tqdm(dt_sell,
                                               disable=not progress_mode,
                                               desc="Sell orders",
                                               ):
            order = self.sell(no_db=True)
            orders_list.append(order)

        orders_list = sorted(orders_list,
                             key=lambda od: (od.dt_open, od.side == 'buy'))
        portfolio_list = []
        for od in tqdm.tqdm(orders_list,
                            disable=not progress_mode,
                            desc="Executing orders",
                            ):

            if od.side == "buy":

                od.update(
                    dt=od.dt_open,
                    quote_price=ohlcv_trading_df.loc[od.dt_open,
                                                     self.ohlcv_names.get(self.bt_buy_on)],
                    quote_amount=self.invest_model.get_buy_quote_amount(self.portfolio)
                )
            elif od.side == "sell":
                od.update(
                    dt=od.dt_open,
                    quote_price=ohlcv_trading_df.loc[od.dt_open,
                                                     self.ohlcv_names.get(self.bt_sell_on)],
                    base_amount=self.invest_model.get_sell_base_amount(self.portfolio),
                )
            else:
                raise ValueError(f"Order side {od.side} not supported") 

            od.execute()
            
            # Update buy and sell price
            self.portfolio.dt = od.dt_closed
            self.portfolio.quote_price = quote_current
            self.portfolio.update_order(od)
            
            portfolio_list.append(self.portfolio.dict())
            
            self.orders_executed[od.uid] = od

        # Register portfolio value at the last timestamp
        self.portfolio.dt = ohlcv_trading_df.index[-1]
        self.portfolio.quote_price = \
            ohlcv_trading_df.loc[self.portfolio.dt,
                                 self.ohlcv_names.get(self.bt_sell_on)]
        self.portfolio.update()
        portfolio_list.append(self.portfolio.dict())
            
        if self.db_trace:
            portfolio_index_var = ["bot_uid"]
            portfolio_df = \
                pd.DataFrame(portfolio_list)\
                  .drop_duplicates(subset=portfolio_index_var,
                                   keep="last")
                
            self.db_trace.put(endpoint="portfolio",
                              data=portfolio_df.to_dict("records"),
                              index=portfolio_index_var,
                              time_field="dt")
            
            # Use dt_closed as time field
            self.db.put(endpoint="orders",
                        data=[od.dict()
                              for od in self.orders_executed.values()],
                        index=["bot_uid"],
                        time_field="dt_closed")
        
        return

        
    def start_btclassic(self, progress_mode=False, data_dir=".", **kwrds):

        ohlcv_ori_df = \
            self.exchange.get_historic_ohlcv(
                date_start=self.ds_trading.dt_s,
                date_end=self.ds_trading.dt_e,
                symbol=self.ds_trading.symbol,
                timeframe=self.timeframe,
                index="datetime",
                data_dir=data_dir,
                force_reload=False,
                progress_mode=progress_mode
            )
        quote_current_s, ohlcv_closed_df = self.exchange.flatten_ohlcv(ohlcv_ori_df)

        self.portfolio.quote_price_init = quote_current_s.iloc[0]

        #self.ds_trading.dt_s = ohlcv_closed_df.index[0]
        #self.ds_trading.dt_e = ohlcv_closed_df.index[-1]

        tdelta = timeframe_to_timedelta(self.timeframe)
        # ohlcv_cur_df = \
        #     self.exchange.get_last_ohlcv(closed=False)

        self.dt_ohlcv_closed = None

        with tqdm.tqdm(total=len(quote_current_s), disable=not progress_mode) as pbar:
            for self.dt_ohlcv_current, self.quote_current in quote_current_s.items():
                
                if self.dt_ohlcv_current != self.dt_ohlcv_closed:
                    dt_start = self.dt_ohlcv_current - tdelta*self.decision_model.bw_length
                    ohlcv_cur_df = ohlcv_closed_df.loc[dt_start:self.dt_ohlcv_current]
                    decision_df = \
                        self.decision_model.predict(ohlcv_cur_df, **kwrds)\
                                           .loc[self.dt_ohlcv_current]
                    decision = decision_df["decision"]
                    
                    if self.logger:
                        self.logger.debug(f"DT current:     {self.dt_ohlcv_current}\n"
                                          f"Quote price:    {fmt_currency(self.quote_current)} {self.quote}\n"
                                          f"DT last closed: {self.dt_ohlcv_closed}\n"
                                          f"decision:         {decision}\n"
                                          f"OHLCV:\n"
                                          f"{ohlcv_cur_df}")

                    #decision = self.bot.tick(quote_cur)
                    # Create Buy / Sell order

                    # TODO DEBUG
                    if self.dt_ohlcv_current == quote_current_s.index[10]:
                        decision = "buy"
                    
                    if decision != "pass":
                        order = getattr(self, decision)()
                        self.register_order(order)

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
                self.portfolio.update()
                self.progress_update()
                if self.db:
                    self.db.update(endpoint="portfolio",
                                   data=self.portfolio.dict(),
                                   index=["bot_uid"],
                                   time_field="dt")
                                   
                    if (pbar.n % 1000) == 0:
                        self.db_update()
                    
                # Updating variables
                #ipdb.set_trace()
                if progress_mode:
                    update_console(self.__str__())
                    
                self.dt_ohlcv_closed = self.dt_ohlcv_current

                pbar.update()

        return


    def start_live(self, progress_mode=False, data_dir=".", **kwrds):

        self.dt_ohlcv_closed = None

        while True:

            ohlcv_current_df = \
                self.exchange.get_last_ohlcv(
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                    index="datetime",
                    nb_data=1,
                    closed=False,
                )

            self.dt_ohlcv_current = ohlcv_current_df.index[0]
            
            self.quote_current = \
                ohlcv_current_df.loc[self.dt_ohlcv_current,
                                     self.ohlcv_names.get("close")]

            if self.portfolio.quote_price_init is None:
                self.portfolio.quote_price_init = self.quote_current
            
            if self.dt_ohlcv_current != self.dt_ohlcv_closed:

                ohlcv_closed_cur_df = \
                    self.exchange.get_last_ohlcv(
                        symbol=self.symbol,
                        timeframe=self.timeframe,
                        index="datetime",
                        nb_data=self.decision_model.bw_length + 1,
                        closed=True,
                    )
                self.dt_ohlcv_closed = ohlcv_closed_cur_df.index[-1]
                signal, signal_score = \
                    self.decision_model.predict(ohlcv_closed_cur_df, **kwrds)\
                                       .replace({np.nan: None})\
                                       .iloc[-1]

                # Create Buy / Sell order
                if signal:
                    order = getattr(self, signal)()
                    self.register_order(order)


                # Update orders
                self.update_orders()
                
                # Updating portfolio
                self.portfolio.dt = self.dt_ohlcv_current
                self.portfolio.quote_price = self.quote_current
                self.portfolio.update()
                self.progress_update()
                if self.db:
                    self.db.update(endpoint="portfolio",
                                   data=self.portfolio.dict(),
                                   index=["bot_uid"],
                                   time_field="dt")

            if progress_mode:
                update_console(self.summary_live())
                
            self.live_sleeping(progress_mode=progress_mode)
                    
        return

    def live_sleeping(self, progress_mode=False):

        delta = timeframe_to_timedelta(self.ds_trading.timeframe)
        dt_ohlcv_next = self.dt_ohlcv_current + delta
        
        tz = pytz.timezone(self.dt_ohlcv_current.tz.key)
        dt_cur = tz.localize(datetime.now())

        if dt_cur > dt_ohlcv_next:
            return

        time_to_ohlcv_next = dt_ohlcv_next - dt_cur
        # sleep_msg = f"Sleeping {time_to_ohlcv_next}"
        # print(sleep_msg)
        
        time.sleep(time_to_ohlcv_next.total_seconds())

    
    def get_nb_buy_sell_orders_diff(self):

        nb_buy_orders = \
            self.nb_buy_orders_open + \
            self.nb_buy_orders_executed
        nb_sell_orders = \
            self.nb_sell_orders_open + \
            self.nb_sell_orders_executed

        return nb_buy_orders - nb_sell_orders

    
    def is_buy_allowed(self):
        
        return self.get_nb_buy_sell_orders_diff() <= self.diff_thresh_buy_sell_orders

    def is_sell_allowed(self):

        return self.get_nb_buy_sell_orders_diff() == self.diff_thresh_buy_sell_orders + 1

    def register_order(self, order, **kwrds):

        if (order.side == "sell" and self.is_sell_allowed()) or \
           (order.side == "buy" and self.is_buy_allowed()):

            self.orders_open[order.uid] = order

        else:

            if self.logger:
                self.logger.debug(f"Order {order.uid} of side {order.side} not allowed : Buy/Sell threshold not respected")
    
    def buy(self, no_db=False, **kwrds):

        order_specs = dict(
            bot_uid=self.uid,
            symbol=self.symbol,
            timeframe=self.ds_trading.timeframe,
            dt_open=self.dt_ohlcv_current,
            side="buy",
            quote_amount=self.invest_model.get_buy_quote_amount(self.portfolio),
            **self.order_model.dict_params(),
        )

        order = OrderBase.from_dict(order_specs)

        if no_db:
            order.db = None
        else:
            order.db = self.db

        if self.exchange:
            order.bkd = self.exchange

        order.test_mode = not (self.mode in ["live"])

        return order

    def sell(self, no_db=False, **kwrds):

        order_specs = dict(
            bot_uid=self.uid,
            symbol=self.symbol,
            timeframe=self.ds_trading.timeframe,
            dt_open=self.dt_ohlcv_current,
            side="sell",
            base_amount=self.invest_model.get_sell_base_amount(self.portfolio),
            **self.order_model.dict_params(),
        )
        
        order = OrderBase.from_dict(order_specs)
        if no_db:
            order.db = None
        else:
            order.db = self.db

        if self.exchange:
            order.bkd = self.exchange

        order.test_mode = not (self.mode in ["live"])
            
        return order

        
    def update_orders(self):

        # Here list is important in order to work on a
        # copy of the dict keys because we modify the structure
        # of buy_orders_open while scanning it.
        for od_uid in list(self.orders_open.keys()):
            od = self.orders_open[od_uid]
            od.update(
                dt=self.dt_ohlcv_current,
                quote_price=self.quote_current,
            )
            if od.is_executable():
                res = od.execute()
                self.portfolio.update_order(od)
                self.orders_executed[od_uid] = self.orders_open.pop(od_uid)

                # TODO : Check res to test order execution status

                
                # if isinstance(res, OrderBase):
                #     self.register_order(res)
                    
