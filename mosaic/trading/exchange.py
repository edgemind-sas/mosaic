from __future__ import annotations

import logging
import pydantic
import typing

from datetime import datetime
import ccxt
import tqdm

import pandas as pd
from ..core import ObjMOSAIC

import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')
PandasSeries = typing.TypeVar('pandas.core.frame.Series')


class Portfolio(pydantic.BaseModel):
    balance: dict = pydantic.Field(
        {}, description="Asserts balance")
    in_orders: dict = pydantic.Field(
        {}, description="Assets in orders")

    def to_df(self):

        return pd.DataFrame(data={"balance": self.balance,
                                  "in_orders": self.in_orders})


class Fees(pydantic.BaseModel):
    taker: float = pydantic.Field(
        0.001, description="Taker fees (market orders)")
    maker: float = pydantic.Field(
        0.001, description="Maker fees (limit orders)")


class ExchangeErrors(pydantic.BaseModel):

    create_order_sell: int = pydantic.Field(
        0, description="Count sell order error")

    create_order_sell_tol: int = pydantic.Field(
        3, description="Count sell order error tolerance")

    def check(self):

        if self.create_order_sell > self.create_order_sell_tol:
            raise ValueError("create_order_sell reaches limits")

    def report_str(self):

        repr_strlist = []
        if self.create_order_sell > 0:

            repr_str = f"{'Order sell':<12}: "\
                f"{self.create_order_sell} "\
                f"({self.create_order_sell_tol})"

            repr_strlist.append(repr_str)

        return "\n".join(repr_strlist)


class ExchangeBase(ObjMOSAIC):
    name: str = pydantic.Field(
        "binance", description="Exchange name")


    # portfolio_init_from_exchange: bool = pydantic.Field(
    #     True,
    #     description="Init portfolio information from exchange")

    portfolio: Portfolio = pydantic.Field(
        Portfolio(),
        description="Portfolio information")

    # quote_currency_balance: float = pydantic.Field(
    #     0, description="Amount of quote currency available")
    # base_currency_balance: float = pydantic.Field(
    #     0, description="Amount of base currency available")

    # Add a method to initiate fees using self.bkd.fetch_trading_fee("BTC/USDT")
    fees: Fees = pydantic.Field(
        Fees(), description="Order fees")

    errors: ExchangeErrors = pydantic.Field(
        ExchangeErrors(), description="Exchange error tracking")

    ohlcv_names: dict = pydantic.Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")

    bkd: typing.Any = pydantic.Field(
        None, description="Exchange backend")

    # class Config:
    #     arbitrary_types_allowed = True

    @staticmethod
    def timeframe_to_seconds(timeframe):
        timeframe_to_sec = \
            {'s': 1, 'm': 60, 'h': 60*60, 'd': 24*60*60}
        timeframe_unit = timeframe[-1]
        timeframe_fact_str = timeframe[:-1]
        timeframe_fact = int(timeframe_fact_str)
        timeframe_nb_sec = timeframe_to_sec[timeframe_unit]

        return timeframe_fact*timeframe_nb_sec

    def get_portfolio_as_str(self):
        return self.portfolio.to_df().to_string()


class ExchangeOffline(ExchangeBase):

    ohlcv_df: PandasDataFrame = pydantic.Field(
        None, description="Exchange data")

    def get_ohlcv(self):

        var_open = self.ohlcv_names.get("open", "open")
        var_low = self.ohlcv_names.get("low", "low")
        var_high = self.ohlcv_names.get("high", "high")

        quote_current_s = self.ohlcv_df[[
            var_open, var_low, var_high,
        ]].stack().rename("quote")\
                      .reset_index(1, drop=True)

        return quote_current_s, self.ohlcv_df.shift(1)


    
class ExchangeOnline(ExchangeBase):

    use_testnet: bool = pydantic.Field(
        True, description="Indicates if we use testnet platform (if exchange has it)")

    live_api_key: str = pydantic.Field(
        None, description="Exchange API key")
    live_secret: str = pydantic.Field(
        None, description="Exchange API secret")
    testnet_api_key: str = pydantic.Field(
        None, description="Exchange API key")
    testnet_secret: str = pydantic.Field(
        None, description="Exchange API secret")


class ExchangeCCXT(ExchangeOnline):
    
    def init_portfolio(self, assets_list):
        if self.portfolio_init_from_exchange:
            self.update_portfolio(assets_list)
        else:
            [(self.portfolio.balance.setdefault(asset, 0),
              self.portfolio.in_orders.setdefault(asset, 0))
             for asset in assets_list]

            # Remove asset not in assets list
            self.portfolio.balance = \
                {asset: val for asset, val in self.portfolio.balance.items()
                 if asset in assets_list}

    def update_portfolio(self, assets_list):

        balance_all = self.bkd.fetch_balance()

        self.portfolio.balance = \
            {asset: balance_all.get(asset, {}).get("free", 0)
             for asset in assets_list}
        self.portfolio.in_orders = \
            {asset: balance_all.get(asset, {}).get("used", 0)
             for asset in assets_list}

    def connect(self, logging=logging):
        if self.use_testnet:
            self.bkd = getattr(ccxt, self.name)({
                'apiKey': self.testnet_api_key,
                'secret': self.testnet_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }})
            ipdb.set_trace()
            self.bkd.set_sandbox_mode(True)

            logging.info(f"Connected to the {self.name} testnet exchange")
        else:
            self.bkd = getattr(ccxt, self.name)({
                'apiKey': self.live_api_key,
                'secret': self.live_secret,
                'enableRateLimit': True})

        return self.bkd

    def set_trading_fees(self, symbol):
        fees_info_all = self.bkd.fetch_trading_fees()

        self.fees.maker = fees_info_all[symbol]["maker"]
        self.fees.taker = fees_info_all[symbol]["taker"]

    def get_last_ohlcv(self,
                       symbol="BTC/USDT",
                       timeframe="1h",
                       nb_data=2,
                       closed=True,
                       logging=logging):

        data_ohlcv_var = ["timestamp", "open",
                          "high", "low", "close", "volume"]

        data_ohlcv = self.bkd.fetch_ohlcv(symbol=symbol,
                                           timeframe=timeframe,
                                           limit=nb_data)

        data_ohlcv_df = pd.DataFrame(
            data_ohlcv, columns=data_ohlcv_var)
        data_ohlcv_df["datetime"] = \
            pd.to_datetime(data_ohlcv_df["timestamp"], unit="ms")

        data_ohlcv_df.set_index("timestamp", inplace=True)

        if closed:
            return data_ohlcv_df.iloc[:-1]
        else:
            return data_ohlcv_df

    def get_historic_ohlcv(self,
                           date_start,
                           date_end=datetime.utcnow(),
                           symbol="BTC/USDT",
                           timeframe="1h",
                           logging=logging,
                           progress_mode=False):

        ts_start = date_start if isinstance(date_start, int) \
            else self.bkd.parse8601(date_start)
        ts_end = date_end if isinstance(date_end, int) \
            else self.bkd.parse8601(date_end)

        # TODO: change to exchange static attribute
        fetch_limit = 500

        timedelta_sec = self.timeframe_to_seconds(timeframe)
        timedelta_ms = 1000*timedelta_sec
        fetch_limit_delta_ms = fetch_limit*timedelta_ms
        period_range = \
            range(ts_start, ts_end, fetch_limit_delta_ms)

        data_ohlcv_var = ["timestamp", "open",
                          "high", "low", "close", "volume"]

        data_ohlcv_df_list = []
        for ts_s in tqdm.tqdm(period_range,
                              disable=not(progress_mode),
                              desc=f"Fetching {symbol} OHLCV {timeframe} data"):

            ts_e = min(ts_s + fetch_limit_delta_ms,
                       ts_end)
            limit = (ts_e - ts_s)//timedelta_ms

            dt_s = datetime.utcfromtimestamp(ts_s/1000)
            dt_e = datetime.utcfromtimestamp(ts_e/1000)

            logging.debug(
                f"Fetch {timeframe} {symbol} data between {dt_s} and {dt_e}")
            data_ohlcv = self.bkd.fetch_ohlcv(symbol,
                                               timeframe=timeframe,
                                               since=ts_s,
                                               limit=limit)

            data_ohlcv_cur_df = pd.DataFrame(
                data_ohlcv, columns=data_ohlcv_var)
            data_ohlcv_cur_df["datetime"] = \
                pd.to_datetime(data_ohlcv_cur_df["timestamp"], unit="ms")

            data_ohlcv_df_list.append(data_ohlcv_cur_df)

        data_ohlcv_df = pd.concat(
            data_ohlcv_df_list, axis=0, ignore_index=True).set_index("timestamp")

        return data_ohlcv_df

    def get_next_historic_ohlcv(self,
                                date_start,
                                nb_data=1,
                                symbol="BTC/USDT",
                                timeframe="1h",
                                logging=logging,
                                progress_mode=False):

        timedelta_sec = self.timeframe_to_seconds(timeframe)
        timedelta_ms = 1000*timedelta_sec
        # ipdb.set_trace()
        ts_start = date_start if isinstance(date_start, int) \
            else self.bkd.parse8601(date_start)
        ts_end = ts_start + nb_data*timedelta_ms

        data_ohlcv_df = \
            self.get_historic_ohlcv(
                date_start=ts_start,
                date_end=ts_end,
                symbol=symbol,
                timeframe=timeframe,
                logging=logging,
                progress_mode=progress_mode)

        return data_ohlcv_df
