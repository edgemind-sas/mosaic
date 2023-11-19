import pydantic
import typing
import pkg_resources
from datetime import datetime
import pandas as pd
import colored
import ccxt
import uuid
from ..core import ObjMOSAIC
from ..db.db_base import DBBase
from ..utils.data_management import \
    timeframe_to_timedelta, HyperParams, parse_value, fmt_currency
from .exchange import ExchangeBase


installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')
PandasSeries = typing.TypeVar('pandas.core.frame.Series')


class FeesValue(pydantic.BaseModel):
    value: float = pydantic.Field(None, description="Fees value")
    asset: str = pydantic.Field(None, description="Asset name")

    
class OrderParams(HyperParams):
    exec_bound_rate: float = pydantic.Field(
        0, description="Execution minimal bound rate")


class OrderBase(ObjMOSAIC):

    uid: str = pydantic.Field(None,
                              description="Unique id of the trade")

    bot_uid: str = pydantic.Field(None,
                                  description="Bot unique id")

    test_mode: bool = pydantic.Field(
        True, description="Indicates if order is really executed from backend")
    
    symbol: str = pydantic.Field(
        None, description="Trading symbol")
    
    timeframe: str = pydantic.Field(
        None, description="Trading timeframe")

    side: str = pydantic.Field(None,
                               description="Order side : long/short")

    quote_amount: float = pydantic.Field(
        None, description="Quote amount traded")

    base_amount: float = pydantic.Field(
        None, description="Base amount traded")

    quote_price: float = pydantic.Field(
        None, description="Asset price in quote currency (e.g. in USDT for BTC/USDT symbol)")

    quote_price_at_create: float = pydantic.Field(
        None, description="Quote price at order creation")
    
    quote_price_exec: float = pydantic.Field(
        None, description="Order quote price execution")

    quote_price_rate_open_exec: float = pydantic.Field(
        None, description="Rate between quote price at order opening and order execution")

    status: str = pydantic.Field(
        "open", description="Order status : open, executed, cancelled")

    dt: datetime = pydantic.Field(
        None,
        description="Order current datetime")
    
    dt_open: datetime = pydantic.Field(
        None,
        description="Order placing/opening datetime")

    dt_closed: datetime = pydantic.Field(
        None,
        description="Order execution/cancellation datetime")

    fees: FeesValue = pydantic.Field(FeesValue(), description="Trade fees")

    params: OrderParams = \
        pydantic.Field(OrderParams(),
                       description="Order parameters")
    
    bkd: ExchangeBase = pydantic.Field(
        None, description="Original orde backend")

    db: DBBase = pydantic.Field(
        None, description="Trading data backend")

    logger: typing.Any = pydantic.Field(
        None, description="Logger")

    model_config = pydantic.ConfigDict(validate_assignment=True)
    
    @pydantic.validator('uid', pre=True, always=True)
    def set_default_id(cls, uid):
        return uid or str(uuid.uuid4())

    @property
    def base(self):
        return self.symbol.split("/")[0]

    @property
    def quote(self):
        return self.symbol.split("/")[1]

    def __init__(self, **data: typing.Any):
        super().__init__(**data)

        self.update_db()

    def update(self, **new_data):

        # TODO : MOVE THIS BLOC AT OBJMOSAIC LEVEL
        if len(new_data) > 0:
            for field, value in new_data.items():
                setattr(self, field, value)

        if self.quote_price_at_create is None:
            self.quote_price_at_create = self.quote_price

        if self.quote_price_at_create is not None:
            sign = 2*(self.side == "buy") - 1
            self.quote_price_exec = \
                self.quote_price_at_create*(1 - sign*self.params.exec_bound_rate)
        if self.quote_price is not None:
            self.quote_price_rate_open_exec = \
                self.quote_price/self.quote_price_at_create - 1


    def dict(self, exclude={"bkd", "db", "logger"}, **kwrds):
        return super().dict(exclude=exclude, **kwrds)

    def dict_params(self):
        return self.dict(include={'params'})
    
    def update_db(self, **new_data):

        self.update(**new_data)
        
        if self.db:
            self.db.update(endpoint="orders",
                           data=self.dict(),
                           index=["bot_uid"])

    def __str__(self):
        return self.repr(sep="\n")
        
    def __repr__(self):
        return self.repr(sep=" ")

    def repr(self, sep="\n"):

        repr_list = []
        repr_list.append(colored.stylize(f"{type(self).__name__}",
                                         self.get_class_style()))

        repr_list.append("UID: " +
                         colored.stylize(f"{self.uid}",
                                         self.get_uid_style()))

        repr_list.append("Side/Status: " +
                         colored.stylize(f"{self.side}",
                                         self.get_side_style()) +
                         colored.stylize(" ",
                                         self.get_default_style()) +
                         colored.stylize(f"({self.status})",
                                         self.get_status_style()))
        
        if self.dt_open:
            repr_list.append("Opening date: " +
                             colored.stylize(f"{self.dt_open}",
                                             self.get_date_style()))
        if self.dt_closed:
            repr_list.append("Closing date: " +
                             colored.stylize(f"{self.dt_closed}",
                                             self.get_date_style()))

        if self.quote_price is not None:
            repr_list.append("QP: " +
                             colored.stylize(f"{fmt_currency(self.quote_price)}",
                                             self.get_default_style()) +
                             f" {self.quote}"
                             )

        if self.quote_amount is not None:
            repr_list.append("QA: " +
                             colored.stylize(f"{fmt_currency(self.quote_amount)}",
                                             self.get_default_style()) +
                             f" {self.quote}"
                             )

        if self.base_amount is not None:
            repr_list.append("BA: " +
                             colored.stylize(f"{fmt_currency(self.base_amount)}",
                                             self.get_default_style()) +
                             f" {self.base}"
                             )

        if self.fees.value is not None:
            repr_list.append("Fees: " +
                             colored.stylize(f"{fmt_currency(self.fees.value)}",
                                             self.get_default_style()) +
                             f" {self.fees.asset}"
                             )
        if self.quote_price_rate_open_exec is not None:
            repr_list.append("QP O/E: " +
                             colored.stylize(f"{self.quote_price_rate_open_exec:.2%}",
                                             self.get_default_style())
                             )
        if self.dt_closed is None and self.quote_price_at_create is not None:
            repr_list.append("QP@Create: " +
                             colored.stylize(f"{fmt_currency(self.quote_price_at_create)}",
                                             self.get_default_style()) +
                             f" {self.quote}"
                             )
            repr_list.append("QP Ex: " +
                             colored.stylize(f"{fmt_currency(self.quote_price_exec)}",
                                             self.get_default_style()) +
                             f" {self.quote}"
                             )

        repr_str = sep.join(repr_list)
        return repr_str

    def is_executable(self):

        exec_bound_cond = \
            self.quote_price <= self.quote_price_exec \
            if self.side == "buy" \
            else self.quote_price >= self.quote_price_exec

        exec_dt_cond = self.dt_open <= self.dt

        return exec_dt_cond & exec_bound_cond

    def get_default_style(self):
        return colored.attr("bold") + \
            colored.fg("blue")

    def get_status_style(self):
        if self.status == "open":
            style = colored.fg("white") + \
                colored.bg("blue")
        elif self.status == "executed":
            style = colored.fg("white") + \
                colored.bg("green")
        elif self.status == "cancelled":
            style = colored.fg("white") + \
                colored.bg("dark_orange")
        else:
            raise ValueError(f"Order status {self.status} not supported")

        return style

    def get_class_style(self):
        return colored.fg("white") + colored.bg(240) + colored.attr("bold")

    def get_uid_style(self):
        return self.get_default_style()

    def get_date_style(self):
        return colored.fg("white") #+ colored.bg(240) + colored.attr("bold")

    def get_side_style(self):

        if self.side == "buy":
            return colored.bg(6) + colored.fg("white")
        elif self.side == "sell":
            return colored.bg(125) + colored.fg("white")
        else:
            raise ValueError("Order side {self.side} not supported")

    def get_filling_rate_style(self):

        color_0 = 81
        color_1 = 76
        color_range = color_1 - color_0
        color_idx = color_0 + int(self.filling_rate*color_range)

        return colored.bg(color_idx) + colored.fg("white")

            
    def execute(self):
        return True
    
    # def get_order_id_backend(self):

    #     if self.exchange.name == "binance":
    #         return int(self.order_backend_id)
    #     else:
    #         return self.order_backend_id
        
        
    # def update_from_backend(self):

    #     fetch_nb_try = 0
    #     order_backend = None
    #     while (order_backend is None) and fetch_nb_try <= 5:

    #         fetch_nb_try += 1

    #         try:
    #             order_backend = \
    #                 self.exchange.conn.fetch_order(self.get_order_id_backend(),
    #                                                self.symbol)
    #         except ccxt.OrderNotFound:
    #             fetch_waiting = 2
    #             if self.logger:
    #                 self.logger.info(
    #                     f"Waiting {fetch_waiting} sec to fetch order - Try {fetch_nb_try}")
    #             time.sleep(fetch_waiting)

    #     if order_backend is None:
    #         raise ValueError(
    #             "Impossible to fetch order {self.get_order_id_backend()}")

    #     self.amount_base = order_backend["amount"]

    #     self.filling_rate = order_backend["filled"]/self.amount_base
    #     if self.filling_rate > 0.999 and not(self.ts_filled_on):
    #         self.ts_filled_on = order_backend["timestamp"]


class OrderMarket(OrderBase):

    def execute(self):

        super().execute()

        if self.side == "buy":
            self.base_amount = \
                self.quote_amount/self.quote_price
        elif self.side == "sell":
            self.quote_amount = \
                self.base_amount*self.quote_price
            
        if not self.test_mode:
            
            order = self.bkd.create_market_order(
                symbol=self.symbol,
                side=self.side,
                amount=self.base_amount,
            )

            self.uid = order["id"]
            self.base_amount = order["amount"]
            self.quote_amount = order["cost"]
            
            fees_base = self.bkd.get_order_fees(order, symbol=self.base)
            if fees_base > 0:
                self.fees.value = fees_base
                self.fees.asset = self.base
                self.base_amount -= self.fees.value

            fees_quote = self.bkd.get_order_fees(order, symbol=self.quote)
            if fees_quote > 0:
                self.fees.value = fees_quote
                self.fees.asset = self.quote
                self.quote_amount -= self.fees.value
            
            self.dt_closed = \
                parse_value(
                    datetime.fromisoformat(order["datetime"]
                                           .replace("Z", "+00:00")))

            self.status = "executed"

        else:
            if self.side == "buy":
                self.fees.value = self.base_amount*self.bkd.fees_rates.taker
                self.fees.asset = self.base
                self.base_amount -= self.fees.value
            elif self.side == "sell":
                self.fees.value = self.quote_amount*self.bkd.fees_rates.taker
                self.fees.asset = self.quote
                self.quote_amount -= self.fees.value

            self.dt_closed = self.dt
            self.status = "executed"

        self.update_db()

        return True


class OrderTrailingMarketParams(OrderParams):

    exec_trailing_rate: float = pydantic.Field(
        None, description="Execution trailing rate")


class OrderTrailingMarket(OrderMarket):

    is_trailing_activated: bool = pydantic.Field(
        False, description="Indicate if order is in trailing mode")

    quote_price_trailing_bound: float = pydantic.Field(
        None, description="Current execution trailing bound")

    params: OrderTrailingMarketParams = \
        pydantic.Field(OrderTrailingMarketParams(),
                       description="Order parameters")
        
    def repr(self, sep="\n"):
        
        repr_list = [super().repr(sep=sep)]

        if self.is_trailing_activated:
            repr_list.append("Exec. Rate: " +
                             colored.stylize(f"{self.params.exec_trailing_rate}",
                                             self.get_default_style())
                             )

            repr_list.append("QPTB: " +
                             colored.stylize(f"{fmt_currency(self.quote_price_trailing_bound)}",
                                             self.get_default_style()) +
                             f" {self.quote}"
                             )
            
        repr_str = sep.join(repr_list)
        return repr_str

    
    def update(self, **new_data):

        super().update(**new_data)

        if self.params.exec_trailing_rate is None:
            self.params.exec_trailing_rate = self.params.exec_bound_rate
        
        if (not self.is_trailing_activated) and \
           (self.quote_price_at_create is not None) and \
           super().is_executable():
            self.is_trailing_activated = True
            sign = 2*(self.side == "buy") - 1
            self.quote_price_trailing_bound = \
                self.quote_price*(1 + sign*self.params.exec_trailing_rate)

        if self.quote_price_trailing_bound is not None:

            sign = 2*(self.side == "buy") - 1
            quote_price_trailing_bound_th = \
                self.quote_price*(1 + sign*self.params.exec_trailing_rate)

            if self.side == "buy":
                if self.quote_price_trailing_bound > quote_price_trailing_bound_th:
                    self.quote_price_trailing_bound = quote_price_trailing_bound_th
            else:
                if self.quote_price_trailing_bound < quote_price_trailing_bound_th:
                    self.quote_price_trailing_bound = quote_price_trailing_bound_th

    def is_executable(self):
        if self.is_trailing_activated:
            exec_order = \
                self.quote_price >= self.quote_price_trailing_bound \
                if self.side == "buy" \
                else self.quote_price <= self.quote_price_trailing_bound
        else:
            exec_order = False
            
        return exec_order
