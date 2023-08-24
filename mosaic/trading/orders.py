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

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')
PandasSeries = typing.TypeVar('pandas.core.frame.Series')


class OrderBase(ObjMOSAIC):

    uid: str = pydantic.Field(None,
                              description="Unique id of the trade")

    bot_uid: str = pydantic.Field(None,
                                      description="Bot unique id")

    side: str = pydantic.Field(...,
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

    bkd: typing.Any = pydantic.Field(
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
        
    def update_db(self):
        if self.db:
            exclude_attr = {"bkd", "db", "logger"}
            self.db.update(endpoint="orders",
                           data=self.dict(exclude=exclude_attr),
                           index=["uid", "bot_uid"])


    def __repr__(self):
        return self.repr(sep="\n")

    def repr(self, sep="\n"):

        repr_list = []
        repr_list.append("Order id: " +
                         colored.stylize(f"{self.uid}",
                                         self.get_id_style()))
        # if self.ts_open:
        #     repr_list.append("Opening date: " +
        #                      colored.stylize(f"{time.ctime(self.ts_open/1000)}",
        #                                      self.get_date_style()))

        # repr_list.append("Side/Status: " +
        #                  colored.stylize(f"{self.side}",
        #                                  self.get_default_style()) +
        #                  colored.stylize(f" ({self.status})",
        #                                  self.get_default_style()))

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

    def is_executable(self):
        raise NotImplementedError("This function must be implemented in class {}"
                                  .format(self.__class__))

    
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

    def get_trading_result_style(self):

        limit_checked = self.take_profit_check or self.stop_loss_check

        if self.result_net > 0:
            style = colored.fg("white") + colored.bg("green") \
                if limit_checked else colored.fg("green")

        else:
            style = colored.fg("white") + colored.bg("red") \
                if limit_checked else colored.fg("red")

        return style

    def get_tp_style(self):
        if self.take_profit_returns > 0:
            style = colored.fg("white") + colored.bg("green") \
                if self.take_profit_check \
                else colored.fg("green")
        else:
            style = colored.fg("white") + colored.bg("red") \
                if self.take_profit_check \
                else colored.fg("red")

        return style

    def get_sl_style(self):
        if self.stop_loss_returns > 0:
            style = colored.fg("white") + colored.bg("green") \
                if self.stop_loss_check \
                else colored.fg("green")
        else:
            style = colored.fg("white") + colored.bg("red") \
                if self.stop_loss_check \
                else colored.fg("red")

        return style

    def get_id_style(self):
        return colored.fg("white") + colored.bg(240) + colored.attr("bold")

    def get_date_style(self):
        return colored.fg("white") + colored.bg(240) + colored.attr("bold")

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

    def execute(self, dt, quote_price):
        
        if self.bkd is None:
            self.quote_price = quote_price
            self.dt_closed = dt
            self.status = "executed"

            
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


# class TradingBotPredictModels(pydantic.BaseModel):
#     close: dbm.MLModel = pydantic.Field(
#         None, description="Close value prediction model")
#     low: dbm.MLModel = pydantic.Field(
#         None, description="Low value prediction model")
#     high: dbm.MLModel = pydantic.Field(
#         None, description="High value prediction model")


# class TradingBot(pydantic.BaseModel):
#     name: str = pydantic.Field(
#         None, description="Trading bot name")

#     symbol: str = pydantic.Field(
#         ..., description="Trading symbol")

#     base: str = pydantic.Field(None, description="Base asset symbol")
#     quote: str = pydantic.Field(None, description="Quote asset symbol")

#     timeframe: str = pydantic.Field(
#         ..., description="Trading timeframe")

#     target_time_horizon: int = pydantic.Field(
#         1, description="Target time horizon")

#     stake_fixed: float = pydantic.Field(
#         None, description="Fixed buy stake")

#     stake_rate: float = pydantic.Field(
#         None, description="To compute stake as stake_rate of equivalent quote balance")

#     check_sl_on_closed: bool = pydantic.Field(
#         False, description="Indicates if SL threshold is checked based on closed timestamp close price (if True) or live current (close) price (if False)")

#     check_tp_on_closed: bool = pydantic.Field(
#         False, description="Indicates if TP threshold is checked based on closed timestamp close price (if True) or live current (close) price (if False)")

#     live_mode: bool = pydantic.Field(
#         True, description="Indicates if we are in live mode")

#     real_order_mode: bool = pydantic.Field(
#         False, description="Indicates if we execute real order on exchange")

#     exchange: ex.Exchange = pydantic.Field(
#         ex.Exchange(), description="Exchange backend")

#     ohlcv_historic_df: pd.DataFrame = pydantic.Field(
#         pd.DataFrame(columns=["datetime", "open",
#                               "high", "low", "close", "volume"]),
#         description="Historic OHLCV data")

#     ohlcv_closed_current: pd.Series = pydantic.Field(
#         None,
#         description="Current closed OHLCV data")

#     ohlcv_live_current: pd.Series = pydantic.Field(
#         None,
#         description="Current live OHLCV data")

#     ohlcv_analyser: ohlcvDataAnalyser = pydantic.Field(
#         ohlcvDataAnalyser(), description="Exchange backend")

#     predict_models: TradingBotPredictModels = pydantic.Field(
#         None, description="Prediction models")

#     predictions_current: dict = pydantic.Field(
#         {}, description="Current self.predictions_current")

#     # TODO : Maybe move that attribute in predict_model
#     reinforcement_learning: bool = pydantic.Field(
#         True, description="Indicates if predict model should be fit by reinforcement approach")

#     predict_nb_data_threshold: int = pydantic.Field(
#         30, description=f"Required number of data to considered"
#         f"the prediction model fitted and ready to make self.predictions_current")

#     got_new_ohlcv_closed: bool = pydantic.Field(
#         False, description="Indicates if the bot received new closed data at current tick")

#     timestamp_closed_current: int = pydantic.Field(
#         None, description="Last closed price timestamp")

#     timestamp_live_current: int = pydantic.Field(
#         None, description="Current timestamp")

#     trades_open: typing.Dict[str, TradeBase] = pydantic.Field(
#         {}, description="Dictionnary of open trades")

#     trades_closed: typing.Dict[str, TradeBase] = pydantic.Field(
#         {}, description="Dictionnary of closed trades")

#     loss_recovery_trying: bool = pydantic.Field(
#         False, description="Enable loss recovery strategy")

#     perf: TradingPerf = pydantic.Field(
#         TradingPerf(), description="Bot performance")

#     nb_ticks: int = pydantic.Field(
#         0, description="Number of ticks (closed timeframes processed)")

#     db_logs: dbd.DBBase = pydantic.Field(
#         dbd.DBBase(), description="Data backend to store bot logs")

#     class Config:
#         arbitrary_types_allowed = True

#     @pydantic.validator('predict_models', pre=True)
#     def validate_predict_model(cls, predict_models_specs, values):

#         target_time_horizon = values.get("target_time_horizon", 1)

#         # ipdb.set_trace()
#         predict_models = {}
#         for target in predict_models_specs:
#             # Automatically add target variable with respect to time horizon
#             predict_models_specs[target]["var_targets"] = \
#                 [f"ret_{target}_t{target_time_horizon}"]

#             predict_models[target] = dbm.create_mlmodel(
#                 **predict_models_specs[target])

#             if not(predict_models[target]):
#                 raise ValueError(
#                     "Prediction model must have a class attribute")

#         return predict_models

#     @pydantic.validator('db_logs', pre=True)
#     def validate_db_logs(cls, db_logs):

#         db_logs = dbd.create_db(**db_logs)

#         if not(db_logs):
#             raise ValueError("db_logs must have a 'cls' attribute")

#         db_logs.connect()

#         return db_logs

#     @pydantic.validator('base', always=True)
#     def set_default_base(cls, base, values):
#         return values.get("symbol").split("/")[0]

#     @pydantic.validator('quote', always=True)
#     def set_default_quote(cls, quote, values):
#         return values.get("symbol").split("/")[1]

#     def __init__(self, **data: typing.Any):
#         super().__init__(**data)

#         # Parametrize OHLCV Analyser
#         self.ohlcv_analyser.target_time_horizon = [self.target_time_horizon]
#         self.ohlcv_analyser.target_var_filter = re.compile("ret.")

#         assets_list = [self.base, self.quote]
#         self.exchange.init_portfolio(assets_list)

#         self.perf.fund_init = self.exchange.portfolio.balance[self.quote]

#     def report_str(self):

#         rep_list = []
#         rep_list.append(colored.stylize(
#             "Bot summary:", self.get_header_style()))

#         # TODO: Add info live/test/real money

#         rep_list.append("Initial fund: " +
#                         colored.stylize(
#                             f"{bu.fmt_currency(self.perf.fund_init):>8}",
#                             self.get_default_style()) +
#                         f" {self.quote}")

#         rep_list.append("Result      : " +
#                         colored.stylize(
#                             f"{bu.fmt_currency(self.perf.result):>8}",
#                             self.get_value_style(self.perf.result)) +
#                         f" {self.quote}")

#         rep_list.append("Result avg. : " +
#                         colored.stylize(
#                             f"{bu.fmt_currency(self.perf.result_avg):>8}",
#                             self.get_value_style(self.perf.result_avg)) +
#                         f" {self.quote}/tick")

#         rep_list.append("Returns     : " +
#                         colored.stylize(
#                             f"{self.perf.returns:8.3%}",
#                             self.get_value_style(self.perf.returns)))

#         rep_list.append("Returns avg.: " +
#                         colored.stylize(
#                             f"{self.perf.returns_avg:8.3%}",
#                             self.get_value_style(self.perf.returns_avg)) +
#                         " /tick")

#         rep_list.append("Returns min.: " +
#                         colored.stylize(
#                             f"{self.perf.returns_min:8.3%}",
#                             self.get_value_style(self.perf.returns_min)))

#         rep_list.append("Returns max.: " +
#                         colored.stylize(
#                             f"{self.perf.returns_max:8.3%}",
#                             self.get_value_style(self.perf.returns_max)))

#         current_loss_returns = self.get_current_loss_returns()
#         rep_list.append("Loss ret. t : " +
#                         colored.stylize(
#                             f"{current_loss_returns:8.3%}",
#                             self.get_value_style(current_loss_returns)))

#         rep_list.append("")

#         rep_list.append(colored.stylize(
#             "Period info:", self.get_header_style()))
#         rep_list.append("# Ticks     : " +
#                         colored.stylize(
#                             f"{self.nb_ticks:>8}",
#                             self.get_default_style()))

#         rep_list.append(f"{'PQ init.':<12}: " +
#                         colored.stylize(
#                             f"{bu.fmt_currency(self.perf.price_quote_init):>8}",
#                             self.get_default_style()) +
#                         f" {self.quote}")

#         rep_list.append(f"{'Ret. period.':<12}: " +
#                         colored.stylize(
#                             f"{self.perf.returns_quote_period:8.3%}",
#                             self.get_value_style(self.perf.returns_quote_period)))

#         rep_list.append("")

#         rep_list.append(colored.stylize(
#             "Current OHLCV data:", self.get_header_style()))
#         ohlcv_liststr = []
#         ohlcv_liststr.append(f"{'Datetime':12}: " +
#                              colored.stylize(
#                                  f"{str(self.ohlcv_live_current['datetime']):>8}",
#                                  self.get_default_style()))

#         ohlc_var = ["open", "high", "low", "close"]
#         for var in ohlc_var:
#             ohlcv_liststr.append(
#                 f"{var.capitalize():12}: " +
#                 colored.stylize(
#                     f"{bu.fmt_currency(self.ohlcv_live_current[var]):>8}",
#                     self.get_value_style(0)) +
#                 f" {self.quote}")

#         ohlcv_liststr.append(f"{'Volume':12}: " +
#                              colored.stylize(
#                                  f"{self.ohlcv_live_current['volume']:>8}",
#                                  self.get_value_style(0)))

#         rep_list.append("\n".join(ohlcv_liststr))

#         rep_list.append("")

#         rep_list.append(colored.stylize(
#             "Open trades:", self.get_header_style()))

#         if not(self.perf.price_quote_open_trades_max is None):
#             rep_list.append(f"{'PQ max.':<12}: " +
#                             colored.stylize(
#                                 f"{bu.fmt_currency(self.perf.price_quote_open_trades_max):>8}",
#                                 self.get_default_style()) +
#                             f" {self.quote}")
#         if self.perf.total_quote_open_trades > 0:
#             rep_list.append(f"{'TQ cum.':<12}: " +
#                             colored.stylize(
#                                 f"{bu.fmt_currency(self.perf.total_quote_open_trades):>8}",
#                                 self.get_default_style()) +
#                             f" {self.quote}")

#         rep_list.append("")

#         rep_list.extend([trade.report_oneliner()
#                          for trade in self.trades_open.values()])

#         rep_list.append("")

#         rep_list.append(colored.stylize(
#             "Errors:", self.get_header_style()))
#         rep_list.append(self.exchange.errors.report_str())

#         rep_str = "\n".join(rep_list)

#         return rep_str

#     def get_default_style(self):
#         return colored.attr("bold") + colored.fg("blue")

#     def get_header_style(self):
#         return colored.attr("underlined") + \
#             colored.attr("bold")

#     def get_value_style(self, val):
#         if val > 0:
#             style = colored.fg("green") + colored.attr("bold")
#         elif val < 0:
#             style = colored.fg("red") + colored.attr("bold")
#         else:
#             style = self.get_default_style()

#         return style

#     def tick(self, data_ohlcv_closed, data_ohlcv_live, logging=logging):

#         self.ohlcv_live_current = data_ohlcv_live.copy()

#         self.timestamp_closed_current = data_ohlcv_closed.name
#         self.timestamp_live_current = data_ohlcv_live.name

#         # Init: Init bot ohlcv historic data
#         if len(self.ohlcv_historic_df) == 0:
#             self.ohlcv_historic_df.index.name = "timestamp"
#             self.perf.price_quote_init = data_ohlcv_live["close"]

#         # If a current data timestamp is different from ohlcv current timestamp
#         # It means last ohlcv current is an historical data
#         self.got_new_ohlcv_closed = (self.ohlcv_closed_current is None) or \
#             (data_ohlcv_closed.name > self.ohlcv_closed_current.name)

#         if self.got_new_ohlcv_closed:

#             self.nb_ticks += 1
#             # self.got_new_ohlcv_closed = True

#             self.ohlcv_historic_df.loc[data_ohlcv_closed.name] = \
#                 data_ohlcv_closed.copy()

#             # Prepare OHLCV data
#             # self.ohlcv_analyser.prepare_data(self.ohlcv_historic_df,
#             #                                  logging=logging)
#             # Prepare OHLCV data
#             self.ohlcv_analyser.update_data(self.ohlcv_historic_df,
#                                             logging=logging)

#             # Fit model with available data
#             self.fit_predict_model(update_fit=self.reinforcement_learning,
#                                    logging=logging)

#             # We have new information so try to predict future
#             self.predict_returns(logging=logging)

#             self.create_long_trade()

#             # self.make_decision(self.predictions_current, logging=logging)

#             self.ohlcv_closed_current = data_ohlcv_closed.copy()

#             # Update portfolio status
#             self.log_portfolio(logging=logging)

#         # Update trades_open status
#         self.update_trades_open(logging=logging)

#         self.update_perf()

#         if self.real_order_mode:
#             self.exchange.errors.check()

#     def set_trade_total_quote(self, trade):
#         raise NotImplementedError("Must be overloaded")

#     def create_long_trade(self):

#         trade = TradeBase(
#             symbol=self.symbol,
#             side='long',
#             exchange=self.exchange,
#             # live_mode=self.live_mode,
#             take_profit_check_on_closed=self.check_tp_on_closed,
#             stop_loss_check_on_closed=self.check_sl_on_closed,
#             db_logs=self.db_logs)

#         if self.check_go_long(trade):

#             self.set_trade_total_quote(trade)

#             if self.get_portfolio_balance("quote") < trade.total_quote:
#                 trade.status = "NEM"
#                 trade.log()

#             # TODO: Mettre ici la mise minimal acceptée par l'exchange
#             elif trade.total_quote > 0:
#                 self.set_trade_bound(trade)
#                 self.buy(trade)

#     def buy(self, trade):

#         if self.live_mode:
#             price_quote_current = self.ohlcv_live_current["close"]
#         else:
#             price_quote_current = self.ohlcv_live_current["open"]

#         if self.real_order_mode:
#             # buy market order from backend
#             amount_base = trade.total_quote/price_quote_current

#             order = self.exchange.conn.create_order(
#                 symbol=self.symbol,
#                 type='market',
#                 side='buy',
#                 amount=amount_base)

#             trade.price_quote = order['average']
#             trade.total_quote = order['cost']
#             trade.amount_base = order['amount']

#         else:
#             trade.price_quote = price_quote_current
#             trade.amount_base = trade.total_quote / \
#                 trade.price_quote*(1 - self.exchange.fees.taker)

#         # Update portfolio
#         self.update_portfolio_balance("quote", -trade.total_quote)
#         self.update_portfolio_balance("base", trade.amount_base)

#         trade.status = "open"
#         trade.ts_open = self.ohlcv_live_current.name

#         new_trade_id = len(self.trades_open) + len(self.trades_closed)
#         trade.id = f"T{new_trade_id:010}"
#         self.trades_open[trade.id] = trade

#         # trade.log()

#     def sell(self, trade, mode=None):

#         if self.real_order_mode:

#             try:

#                 # Sell market order from backend
#                 order = self.exchange.conn.create_order(
#                     symbol=self.symbol,
#                     type='market',
#                     side='sell',
#                     amount=trade.amount_base)

#                 total_quote_current = order['cost']
#                 trade.result_net = total_quote_current - trade.total_quote
#                 trade.returns_net = trade.result_net/trade.total_quote

#                 # Reset selling error
#                 self.exchange.errors.create_order_sell = 0

#             except ccxt.InsufficientFunds:

#                 self.exchange.errors.create_order_sell += 1

#                 logging.error(
#                     f"Error {self.exchange.errors.create_order_sell} while trying to sell {trade.amount_base} {self.base}: {ccxt.InsufficientFunds}")

#         else:

#             # self.update_trade_result(trade, mode=mode)

#             if mode == "sl":
#                 price_quote_current = (
#                     1 + trade.stop_loss_returns)*trade.price_quote
#             elif mode == "tp":
#                 price_quote_current = (
#                     1 + trade.take_profit_returns)*trade.price_quote
#             else:
#                 raise ValueError(
#                     f"Sell mode {mode} not supported in test mode")

#             total_quote_current = trade.amount_base * \
#                 price_quote_current
#             total_quote_current_net = total_quote_current * \
#                 (1 - self.exchange.fees.taker)

#             trade.result = total_quote_current - trade.total_quote
#             trade.returns = trade.result/trade.total_quote
#             trade.result_net = total_quote_current_net - trade.total_quote
#             trade.returns_net = trade.result_net/trade.total_quote

#             # TODO: Compute fees at selling
#             # trade.fees += trade.total_quote*(1 - self.exchange.fees.taker)

#         # Update portfolio
#         self.update_portfolio_balance(
#             "quote", trade.total_quote + trade.result_net)
#         self.update_portfolio_balance("base", -trade.amount_base)

#         self.trades_open.pop(trade.id)
#         self.trades_closed[trade.id] = trade

#         trade.status = "closed"

#         # trade.log()

#         return True

#     def get_open_trades(self):
#         return [trade for trade in self.trades_open.values()
#                 if trade.status == "open"]

#     def has_open_trades(self):
#         return len(self.get_open_trades()) > 0

#     def update_trades_open(self, logging=logging):

#         trades_open_list = list(self.trades_open.values())

#         for trade in trades_open_list:

#             self.update_trade(trade)

#             # Update strategy
#             # if self.got_new_ohlcv_closed:
#             #     self.check_go_long(trade)

#             # self.update_trade(trade)

#             # Check if sell signal is up
#             if trade.stop_loss_check:
#                 self.sell(trade, mode="sl")
#             elif trade.take_profit_check:
#                 self.sell(trade, mode="tp")
#             else:
#                 pass
#                 # trade.log()

#             # logging.info(trade.repr(sep=" - "))

#     def check_take_profit(self, trade):

#         if self.live_mode:
#             close_price = min(self.ohlcv_live_current["open"],
#                               self.ohlcv_live_current["close"]) \
#                 if trade.take_profit_check_on_closed \
#                 else self.ohlcv_live_current["close"]
#         else:

#             close_price = self.ohlcv_live_current["open"] \
#                 if trade.take_profit_check_on_closed \
#                 else self.ohlcv_closed_current["high"]

#         tp_thresh_returns = close_price/trade.price_quote - 1

#         trade.take_profit_check = \
#             (tp_thresh_returns > trade.take_profit_returns) and \
#             ((trade.ts_open < self.ohlcv_live_current.name) or self.live_mode)

#     def check_stop_loss(self, trade):

#         if self.live_mode:
#             close_price = self.ohlcv_live_current["open"] \
#                 if trade.stop_loss_check_on_closed \
#                 else self.ohlcv_closed_current["low"]

#         else:
#             close_price = max(self.ohlcv_live_current["open"],
#                               self.ohlcv_live_current["close"]) \
#                 if trade.stop_loss_check_on_closed \
#                 else self.ohlcv_live_current["close"]

#         sl_thresh_returns = close_price/trade.price_quote - 1

#         trade.stop_loss_check = \
#             sl_thresh_returns < trade.stop_loss_returns and \
#             ((trade.ts_open < self.ohlcv_live_current.name) or self.live_mode)

#     def update_trade(self, trade):

#         if self.live_mode:
#             price_quote_current = self.ohlcv_live_current["close"]
#         else:
#             price_quote_current = self.ohlcv_live_current["open"]

#         total_quote_current = trade.amount_base * \
#             price_quote_current
#         total_quote_current_net = total_quote_current * \
#             (1 - self.exchange.fees.taker)

#         trade.result = total_quote_current - trade.total_quote
#         trade.returns = trade.result/trade.total_quote
#         trade.result_net = total_quote_current_net - trade.total_quote
#         trade.returns_net = trade.result_net/trade.total_quote

#         # total_quote_current = trade.amount_base * \
#         #     price_quote_current*(1 - self.exchange.fees.taker)

#         # trade.result = total_quote_current - trade.total_quote
#         # trade.returns = trade.result/trade.total_quote

#         self.check_take_profit(trade)
#         self.check_stop_loss(trade)

#         self.update_tp_if_checked(trade)

#     def update_tp_if_checked(self, trade):
#         """ Strategy to be applied if TP is checked"""

#         decision_d = dict({"timestamp": self.timestamp_live_current,
#                            "datetime": datetime.fromtimestamp(
#                                self.timestamp_live_current/1000).isoformat(),
#                            "tick_dt": datetime.now().isoformat(),
#                            "trade_id": trade.id})

#         if trade.take_profit_check:
#             # ipdb.set_trace()

#             trade.stop_loss_returns = trade.take_profit_returns
#             # Now, we trigger stop loss as soon as checked
#             trade.stop_loss_check_on_closed = False

#             trade.take_profit_returns = trade.returns + \
#                 (1 - self.exchange.fees.taker)**(-2) - 1

#             trade.take_profit_check = False

#             decision_d["decision"] = "update_tp_check"

#             self.db_logs.put(endpoint="strategy", data=decision_d)

#     # def update_trade_result(self, trade, mode=None):

#     #     if mode == "sl":
#     #         price_quote_current = (
#     #             1 + trade.stop_loss_returns)*trade.price_quote
#     #     elif mode == "tp":
#     #         price_quote_current = (
#     #             1 + trade.take_profit_returns)*trade.price_quote
#     #     else:
#     #         price_quote_current = self.ohlcv_live_current["close"]

#     #     total_quote_current = trade.amount_base * \
#     #         price_quote_current*(1 - self.exchange.fees.taker)

#     #     trade.result = total_quote_current - trade.total_quote
#     #     trade.returns = trade.result/trade.total_quote

#     def get_data_fit(self, var_target):
#         var_model = getattr(self.predict_models, var_target).var_extra + \
#             getattr(self.predict_models, var_target).var_features + \
#             getattr(self.predict_models, var_target).var_targets

#         var_ohlcv = [v for v in self.ohlcv_analyser.ohlcv_df.columns
#                      if v in var_model]
#         var_indic = [v for v in self.ohlcv_analyser.indic_df.columns
#                      if v in var_model]
#         var_target = [v for v in self.ohlcv_analyser.target_df.columns
#                       if v in var_model]

#         data_fit_df = pd.concat([self.ohlcv_analyser.ohlcv_df[var_ohlcv],
#                                  self.ohlcv_analyser.indic_df[var_indic],
#                                  self.ohlcv_analyser.target_df[var_target]],
#                                 axis=1)

#         return data_fit_df

#     def fit_predict_model(self, update_fit=False, logging=logging):

#         # TODO : OPTIMIZE THIS : WE BUILD THE ENTIRE DATA_FIT
#         # EACH TIME NEW OHLCV DATA IS STORED
#         # IF UPDATE_FIT = TRUE, WE ONLY NEED THE LAST DATA_FIT
#         ipdb.set_trace()
#         for var_target, model in self.predict_models:

#             data_fit_df = self.get_data_fit(var_target)

#             data_fit_no_na_df = data_fit_df.dropna()

#             if len(data_fit_no_na_df) > 0:
#                 if update_fit:
#                     # TODO: MAKE SOMETHING MORE ELEGANT THAN THAT
#                     # TODO: Change fit_parameters passing in MLModel class
#                     model.fit_parameters.update_fit = update_fit

#                     model.fit(data_fit_no_na_df.iloc[-1:])

#                     # print(self.predict_model.model.get_cct("ret_low_t5").sum())

#                     # ipdb.set_trace()

#                 else:
#                     model.fit(data_fit_no_na_df)

#             if len(data_fit_df) > 0:
#                 self.db_logs.put(endpoint=f"data_fit_{var_target}",
#                                  data=data_fit_no_na_df.iloc[-1:].assign(
#                                      datetime=pd.to_datetime(
#                                          data_fit_no_na_df.iloc[-1:].index,
#                                          unit="ms")))

#         # ipdb.set_trace()

#     def get_data_indic(self, var_target):
#         var_model = getattr(self.predict_models, var_target).var_extra + \
#             getattr(self.predict_models, var_target).var_features

#         var_indic = [v for v in self.ohlcv_analyser.indic_df.columns
#                      if v in var_model]

#         indic_df = self.ohlcv_analyser.indic_df.loc[:, var_indic]

#         return indic_df

#     def get_last_data_indic(self, var_target):

#         indic_df = self.get_data_indic(var_target)

#         # Note:
#         # last_ts is an index list containing only one index to
#         # ensure indic_cur_df is directly a DataFrame.
#         # Do not use intermediate Series to avoid dtypes problems.
#         last_ts = indic_df.index[-1:]
#         indic_cur_df = indic_df.loc[last_ts].dropna()

#         return indic_cur_df

#     def predict_returns(self, logging=logging):

#         thz = self.target_time_horizon

#         for var_target, model in self.predict_models:

#             if not(model):
#                 logging.debug("No prediction model provided")
#                 return None

#             if model.nb_data_fit < self.predict_nb_data_threshold:
#                 logging.debug("Insufficient number of fitting data")
#                 return None

#             indic_cur_df = self.get_last_data_indic(var_target)

#             if len(indic_cur_df) > 0:
#                 target_var_name = f"ret_{var_target}_t{thz}"
#                 self.predictions_current[var_target] = \
#                     model.predict(indic_cur_df)[target_var_name]["scores"]

#         return self.predictions_current

#     def get_current_loss_returns(self):

#         current_loss_returns = 0

#         for order in self.trades_open.values():
#             current_loss_returns += min(order.returns, 0)

#         return current_loss_returns

#     def update_portfolio(self, init=False, logging=logging):

#         assets_list = [self.base, self.quote]

#         if init:
#             self.exchange.init_portfolio(assets_list)
#         else:
#             self.exchange.update_portfolio(assets_list)

#     def get_portfolio_balance(self, currency):
#         currency_str = self.quote if currency == "quote" \
#             else self.base

#         return self.exchange.portfolio.balance[currency_str]

#     # def get_portfolio_in_orders(self, currency):
#     #     currency_str = self.quote if currency == "quote" \
#     #         else self.base

#         # return self.exchange.portfolio.balance[currency_str]

#     def update_portfolio_balance(self, currency, amount):
#         currency_str = self.quote if currency == "quote" \
#             else self.base

#         self.exchange.portfolio.balance[currency_str] += amount

#     # def update_portfolio_in_orders(self, currency, amount):
#     #     currency_str = self.quote if currency == "quote" \
#     #         else self.base

#     #     self.exchange.portfolio.in_orders[currency_str] += amount

#     def get_quote_equiv_balance(self):

#         quote_balance_cur = self.exchange.portfolio.balance[self.quote]
#         base_balance_cur = self.exchange.portfolio.balance[self.base]
#         quote_equiv_balance = quote_balance_cur + \
#             base_balance_cur * \
#             self.ohlcv_live_current["close"]*(1 - self.exchange.fees.taker)

#         return quote_equiv_balance

#     def log_portfolio(self, logging=logging):

#         # Register portfolio update event
#         portfolio_balance_dict = dict({"timestamp": self.timestamp_live_current,
#                                        "datetime": datetime.fromtimestamp(
#                                            self.timestamp_live_current/1000).isoformat(),
#                                        "tick_dt": datetime.now().isoformat(),
#                                        self.quote + "_price": self.ohlcv_live_current["close"]},
#                                       **self.exchange.portfolio.balance)

#         portfolio_balance_dict[self.quote +
#                                "_equiv"] = self.get_quote_equiv_balance()

#         # portfolio_in_orders_dict = \
#         #     dict({"timestamp": self.timestamp_live_current,
#         #           "datetime": datetime.fromtimestamp(
#         #               self.timestamp_live_current/1000).isoformat(),
#         #           "tick_dt": datetime.now().isoformat()},
#         #          **self.exchange.portfolio.in_orders)

#         self.db_logs.put(endpoint="portfolio", data=portfolio_balance_dict)

#         # self.portfolio_balance.append(portfolio_balance_dict)
#         # self.portfolio_in_orders.append(portfolio_in_orders_dict)
#     def pred_to_frame(self):

#         if len(self.predictions_current) > 0:
#             # thz = self.target_time_horizon
#             # close_dist = self.predictions_current[f"ret_close_t{thz}"]["scores"]
#             # low_dist = self.predictions_current[f"ret_low_t{thz}"]["scores"]
#             # high_dist = self.predictions_current[f"ret_high_t{thz}"]["scores"]

#             return pd.concat([self.predictions_current["close"]
#                               .stack()
#                               .rename("close"),
#                               self.predictions_current["low"]
#                               .stack()
#                               .rename("low"),
#                               self.predictions_current["high"]
#                               .stack()
#                               .rename("high")],
#                              axis=1)

#         else:
#             return None

#     def pred_describe(self, quantiles=[0.1, 0.25, 0.5, 0.75, 0.9]):

#         if len(self.predictions_current) > 0:
#             close_dist = self.predictions_current["close"]
#             low_dist = self.predictions_current["low"]
#             high_dist = self.predictions_current["high"]

#             close_desc = pd.concat([close_dist.E()] +
#                                    [close_dist.quantile(q) for q in quantiles],
#                                    axis=1)
#             low_desc = pd.concat([low_dist.E()] +
#                                  [low_dist.quantile(q) for q in quantiles],
#                                  axis=1)

#             high_desc = pd.concat([high_dist.E()] +
#                                   [high_dist.quantile(q) for q in quantiles],
#                                   axis=1)

#             return pd.concat([close_desc.stack().rename("close"),
#                               low_desc.stack().rename("low"),
#                               high_desc.stack().rename("high")],
#                              axis=1)

#         else:
#             return None

#     def get_pred_returns_dist(self, indic="close"):
#         return self.predictions_current.get(indic, None)

#     def update_perf(self):

#         quote_equiv = self.get_quote_equiv_balance()

#         nb_ticks = self.nb_ticks

#         self.perf.price_quote_open_trades_max = \
#             max([trade.price_quote for trade in self.trades_open.values()]) \
#             if len(self.trades_open) > 0 else None
#         self.perf.total_quote_open_trades = \
#             sum([trade.total_quote for trade in self.trades_open.values()])

#         self.perf.result = quote_equiv - self.perf.fund_init
#         self.perf.result_avg = self.perf.result/nb_ticks

#         self.perf.returns = self.perf.result/self.perf.fund_init
#         self.perf.returns_avg = self.perf.returns/nb_ticks

#         self.perf.returns_quote_period = \
#             self.ohlcv_live_current["close"]/self.perf.price_quote_init - 1

#         if self.perf.returns > self.perf.returns_max:
#             self.perf.returns_max = self.perf.returns

#         if self.perf.returns < self.perf.returns_min:
#             self.perf.returns_min = self.perf.returns


class OrderMarket(OrderBase):

    def is_executable(self):
        return True

    def execute(self, dt, quote_price):

        super().execute(dt, quote_price)

        if self.bkd is None:            
            if self.side == "buy":
                self.base_amount = \
                    (1 - self.fees)*self.quote_amount/self.quote_price
            elif self.side == "sell":
                self.quote_amount = \
                    (1 - self.fees)*self.base_amount*self.quote_price
            else:
                raise ValueError(f"Unrecognized order side {self.side}")

        else:
            if self.logger:
                self.logger.debug("À IMPLÉMENTER")

        self.update_db()

        return True



