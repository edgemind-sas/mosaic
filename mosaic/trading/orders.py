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
import hashlib
from ..utils.data_management import \
    timeframe_to_timedelta, HyperParams, parse_value
from .exchange import ExchangeBase


installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')
PandasSeries = typing.TypeVar('pandas.core.frame.Series')


class OrderParams(HyperParams):
    pass
    # auto_reverse_order_horizon: int = pydantic.Field(
    #     0, description="Sell horizon time units", ge=0)
    

class OrderBase(ObjMOSAIC):

    uid: str = pydantic.Field(None,
                              description="Unique id of the trade")

    bot_uid: str = pydantic.Field(None,
                                      description="Bot unique id")

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
        None, description="Price of one base currency in quote currency (e.g. in USDT/BTC for BTC/USDT symbol)")

    # bot: TradingBot = pydantic.Field(
    #     TradingBot(), description="Parent trading robot")

    status: str = pydantic.Field(
        "open", description="Order status : open, executed, cancelled")

    dt_open: datetime = pydantic.Field(
        None,
        description="Order placing/opening UTC timestamp ")

    dt_closed: datetime = pydantic.Field(
        None,
        description="Order execution/cancellation UTC timestamp")

    fees: float = pydantic.Field(0, description="Trade fees")

    params: OrderParams = \
        pydantic.Field(OrderParams(),
                       description="Order parameters")
    
    bkd: ExchangeBase = pydantic.Field(
        None, description="Original orde backend")

    db: DBBase = pydantic.Field(
        None, description="Trading data backend")

    logger: typing.Any = pydantic.Field(
        None, description="Logger")

    @pydantic.validator('uid', pre=True, always=True)
    def set_default_id(cls, uid):
        return uid or str(uuid.uuid4())

    # @pydantic.validator('base', always=True)
    # def set_default_base(cls, base, values):
    #     return values.get("symbol").split("/")[0]

    # @pydantic.validator('quote', always=True)
    # def set_default_quote(cls, quote, values):
    #     return values.get("symbol").split("/")[1]

    def __init__(self, **data: typing.Any):
        super().__init__(**data)

        self.update_db()

    def dict(self, exclude={"bkd", "db", "logger"}, **kwrds):

        return super().dict(exclude=exclude, **kwrds)
        
    def dict_params(self):
        return self.dict(include={'params'})
    
    def update_db(self):
        if self.db:
            self.db.update(endpoint="orders",
                           data=self.dict(),
                           index=["uid", "bot_uid"])

    def __repr__(self):
        return self.repr(sep="\n")

    def repr(self, sep="\n"):

        repr_list = []
        repr_list.append("Order id: " +
                         colored.stylize(f"{self.uid}",
                                         self.get_id_style()))

        repr_list.append("Side/Status: " +
                         colored.stylize(f"{self.side}",
                                         self.get_default_style()) +
                         colored.stylize(f" ({self.status})",
                                         self.get_default_style()))

        if self.dt_open:
            repr_list.append("Opening date: " +
                             colored.stylize(f"{self.dt_open}",
                                             self.get_date_style()))
        if self.dt_closed:
            repr_list.append("Closing date: " +
                             colored.stylize(f"{self.dt_closed}",
                                             self.get_date_style()))
        
        # repr_list.append("Total quote: " +
        #                  colored.stylize(f"{bu.fmt_currency(self.total_quote)} {self.quote}",
        #                                  self.get_default_style()))


        repr_str = sep.join(repr_list)
        return repr_str

    def report_oneliner(self):

        repr_str = ""
        repr_str += colored.stylize(f"{self.id:<12}: ",
                                    self.get_id_style())

        # repr_str += " TQ: " + \
        #     colored.stylize(f"{bu.fmt_currency(self.total_quote):8} {self.quote}",
        #                     self.get_default_style())

        # repr_str += " PQ: " + \
        #     colored.stylize(f"{bu.fmt_currency(self.price_quote):8} {self.quote}",
        #                     self.get_default_style())

        return repr_str

    # def json(self, exclude=None, **kwargs):
    #     exclude_attr = {"parent_order",
    #                     "take_profit_order",
    #                     "stop_loss_order"}

    #     json_expr =
    #     return super().json(exclude=exclude_attr), **kwargs)

    # def dict(self, exclude=None, **kwargs):
    #     exclude_attr = {
    #         "bkd",
    #         "logger",
    #         }

    #     dict_export = super().dict(exclude=exclude_attr, **kwargs)

    #     # Add base and quote currencies
    #     # dict_export["base"] = self.base
    #     # dict_export["quote"] = self.quote

    #     # dict_export["fee_currency"] = self.fee["currency"]
    #     # dict_export["fee_cost"] = self.fee["cost"]

    #     # dict_export["parent_order"] = \
    #     #     self.parent_order.id if self.parent_order else None

    #     # dict_export["take_profit_order"] = \
    #     #     self.take_profit_order.id if self.take_profit_order else None

    #     # dict_export["stop_loss_order"] = \
    #     #     self.stop_loss_order.id if self.stop_loss_order else None

    #     return dict_export

    # def to_frame(self):

    #     # ipdb.set_trace()
    #     var_order = [
    #         "id",
    #         "symbol",
    #         "side",
    #         "status",
    #         "amount_base",
    #         "base",
    #         "total_quote",
    #         "price_quote",
    #         "result",
    #         "result_net",
    #         "quote",
    #         "returns",
    #         "returns_net",
    #         "ts_created",
    #         "ts_open",
    #         "take_profit_returns",
    #         "stop_loss_returns",
    #     ]

    #     return pd.DataFrame([self.dict()])[var_order].set_index("id")

    def is_executable(self, dt):
        return self.dt_open <= dt

    
    # def log(self, endpoint_base="orders"):

    #     order_df = self.to_frame()

    #     self.db_logs.put(endpoint=endpoint_base + "_status",
    #                      data=order_df,
    #                      update=True)

    #     self.db_logs.put(endpoint=endpoint_base + "_history",
    #                      data=order_df,
    #                      update=False)

    def get_default_style(self):
        return colored.attr("bold") + \
            colored.fg("blue")

    def get_status_style(self):
        if self.status == "open":
            style = colored.fg("white") + \
                colored.bg("green")
        elif self.status == "executed":
            style = colored.fg("white") + \
                colored.bg("blue")
        elif self.status == "cancelled":
            style = colored.fg("white") + \
                colored.bg("dark_orange")
        else:
            raise ValueError(f"Order status {self.status} not supported")

        return style

    def get_id_style(self):
        return colored.fg("white") + colored.bg(240) + colored.attr("bold")

    def get_date_style(self):
        return colored.fg("white") #+ colored.bg(240) + colored.attr("bold")

    def get_side_style(self):

        if self.side == "long":
            return colored.bg(6) + colored.fg("white")
        elif self.side == "short":
            return colored.bg(125) + colored.fg("white")
        else:
            raise ValueError("Order side {self.side} not supported")

    def get_filling_rate_style(self):

        color_0 = 81
        color_1 = 76
        color_range = color_1 - color_0
        color_idx = color_0 + int(self.filling_rate*color_range)

        return colored.bg(color_idx) + colored.fg("white")

    def execute_pre(self, dt, quote_price):

        self.quote_price = quote_price
        
        if self.bkd is None:
            self.dt_closed = dt
            self.status = "executed"

    def execute_order(self, dt, quote_price):
        return True
            
    # def create_reverse_order(self, dt, quote_price):

    #     side = "buy" if self.side == "sell" else "sell"

    #     timeframe_delta = timeframe_to_timedelta(self.timeframe)

    #     delta = timeframe_delta*self.params.auto_reverse_order_horizon
    #     dt_open = self.dt_closed + delta
        
    #     order = self.__class__(
    #         bot_uid=self.bot_uid,
    #         symbol=self.symbol,
    #         dt_open=dt_open,
    #         fees=self.fees,
    #         side=side,
    #         db=self.db,
    #         **self.dict_params(),
    #     )
    #     # Inhibate auto reverse order horizon for autogenerated orders
    #     order.params.auto_reverse_order_horizon = None
        
    #     if side == "buy":
    #         order.quote_amount = self.quote_amount
    #     else:
    #         order.base_amount = self.base_amount

    #     return order

    def execute(self, dt, quote_price):
        self.execute_pre(dt, quote_price)

        order_status = self.execute_order(dt, quote_price)

        return order_status
    
        # if self.status == "executed" and self.params.auto_reverse_order_horizon:
        #     order_rev = self.create_reverse_order(dt, quote_price)
        #     return order_rev
        # else:
        #     return order_status

    def get_order_id_backend(self):

        if self.exchange.name == "binance":
            return int(self.order_backend_id)
        else:
            return self.order_backend_id
 
    def update_from_backend(self):

        fetch_nb_try = 0
        order_backend = None
        while (order_backend is None) and fetch_nb_try <= 5:

            fetch_nb_try += 1

            try:
                order_backend = \
                    self.exchange.conn.fetch_order(self.get_order_id_backend(),
                                                   self.symbol)
            except ccxt.OrderNotFound:
                fetch_waiting = 2
                if self.logger:
                    self.logger.info(
                        f"Waiting {fetch_waiting} sec to fetch order - Try {fetch_nb_try}")
                time.sleep(fetch_waiting)

        if order_backend is None:
            raise ValueError(
                "Impossible to fetch order {self.get_order_id_backend()}")

        self.amount_base = order_backend["amount"]

        self.filling_rate = order_backend["filled"]/self.amount_base
        if self.filling_rate > 0.999 and not(self.ts_filled_on):
            self.ts_filled_on = order_backend["timestamp"]




# # TODO: add print method to show stats
# class TradingPerf(pydantic.BaseModel):
#     fund_init: float = pydantic.Field(
#         0, description="Initial fund")

#     price_quote_init: float = pydantic.Field(
#         None, description="Initial price quote")

#     result: float = pydantic.Field(
#         0, description="Current result")

#     result_avg: float = pydantic.Field(
#         0, description="Current result per tick")

#     returns: float = pydantic.Field(
#         0, description="Current bot returns")

#     returns_avg: float = pydantic.Field(
#         0, description="Current returns per tick")

#     returns_min: float = pydantic.Field(
#         0, description="Current min returns")

#     returns_max: float = pydantic.Field(
#         0, description="Current max returns")

#     returns_quote_period: float = pydantic.Field(
#         0, description="Returns quote price during the period")

#     price_quote_open_trades_max: float = pydantic.Field(
#         None, description="Current price quote max in open trades")

#     total_quote_open_trades: float = pydantic.Field(
#         None, description="Current total quote in open trades")



class OrderMarket(OrderBase):

    def is_executable(self, dt):
        return super().is_executable(dt)

    def execute_order(self, dt, quote_price):

        super().execute_order(dt, quote_price)

        if self.side == "buy":
            self.base_amount = \
                self.quote_amount/self.quote_price
            
            if not (self.bkd is None):
                order = self.bkd.bkd.create_market_buy_order(
                    self.symbol, self.base_amount)
                self.uid = order["id"]
                self.base_amount = order["amount"]
                self.quote_amount = order["cost"]

                # try:
                #     print('Order successfully created:', order)
                # except ccxt.NetworkError as e:
                #     print('Network error:', e)
                # except ccxt.ExchangeError as e:
                #     print('Exchange error:', e)
                # except ccxt.BaseError as e:
                #     print('CCXT base error:', e)
                dt_closed = \
                    parse_value(
                        datetime.fromisoformat(order["datetime"]
                                               .replace("Z", "+00:00")))

                self.dt_closed = dt_closed
                self.status = "executed"

            else:
                self.base_amount *= (1 - self.fees)
            
        elif self.side == "sell":
            self.quote_amount = \
                self.base_amount*self.quote_price

            if not (self.bkd is None):
                order = self.bkd.bkd.create_market_sell_order(
                    self.symbol, self.base_amount)
                self.uid = order["id"]
                self.base_amount = order["amount"]
                self.quote_amount = order["cost"]

                dt_closed = \
                    parse_value(
                        datetime.fromisoformat(order["datetime"]
                                               .replace("Z", "+00:00")))
                self.dt_closed = dt
                self.status = "executed"

            else:
                self.quote_amount *= (1 - self.fees)

        else:
            raise ValueError(f"Unrecognized order side {self.side}")

        self.update_db()

        return True
