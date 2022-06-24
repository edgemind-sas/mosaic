import logging
from typing import Any, List, Union

import ccxt
import numpy as np
from pandas import DataFrame, Timestamp, to_datetime
from pydantic import BaseModel, Field


class Exchange(BaseModel):

    name: str = Field(None)
    symbol: List[str] = Field([])
    base_pair: List[str] = Field([])
    interval: List[str] = Field([])

    ccxt_exchange: Any = Field(None)

    def __init__(self, **data):

        super().__init__(**data)

        self.ccxt_exchange = getattr(ccxt, self.name)()
        self.ccxt_exchange.enableRateLimit = True

        self.validate_config()

    def validate_config(self):

        # check exchange name exist
        if self.name not in ccxt.exchanges:
            raise(BaseException(
                f'Exchange "{self.name}" does not exist in ccxt'))

        # check ccxt exchange has ohlcvt fetch api
        if not self.ccxt_exchange.has.get("fetchOHLCV"):
            raise(BaseException(
                f'Exchange "{self.name}" doesn\'t suuport fetchOHLCV'))

        for timeframe in self.interval:
            if timeframe not in self.ccxt_exchange.timeframes:
                raise(BaseException(
                    f'Timeframe "{timeframe}" not supported by "{self.name}". \
                        Supported are : {self.ccxt_exchange.timeframes}'))

        self.ccxt_exchange.loadMarkets()

        for symbol in self.symbol:
            for base_pair in self.base_pair:
                if f'{symbol}/{base_pair}' not in self.ccxt_exchange.symbols:
                    raise(BaseException(
                        f'Symbol {symbol}/{base_pair} not supported by "{self.name}"'))

        logging.info("Exchange configuration is OK")

    def _download_from_exchange(self, timeframe, symbol, base_pair,
                                start: Timestamp, end: Timestamp,
                                fetch_count=2000):

        ohlcv = []

        logging.info(
            f'Download {self.ccxt_exchange.id} {timeframe} {symbol}/{base_pair}')

        end_time_in_ms = int(end.value / 1000000)
        start_in_ms = int(start.value / 1000000)

        while start_in_ms < end_time_in_ms:

            new_ohlcv = self.ccxt_exchange.fetchOHLCV(
                f'{symbol}/{base_pair}', timeframe, start_in_ms, fetch_count)

            if len(new_ohlcv) == 0:
                break

            last_value = new_ohlcv[len(new_ohlcv)-1][0]

            if len(new_ohlcv) == 1 and Timestamp(start_in_ms) == Timestamp(last_value):
                break

            ohlcv.extend(new_ohlcv)

            start_in_ms = last_value

        df = DataFrame(
            ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = df['time'].astype('datetime64[ms]')
        df.set_index("time", inplace=True)

        # drop data after end
        df.drop(df.loc[df.index > np.datetime64(end)].index, inplace=True)

        return df

    def download_history(self,
                         start: Union[str, Timestamp],
                         end: Union[str, Timestamp]):

        start = to_datetime(start, utc=True)
        end = to_datetime(end, utc=True)

        return_structure = []

        for timeframe in self.interval:
            for symbol in self.symbol:
                for base_pair in self.base_pair:

                    df = self._download_from_exchange(
                        timeframe, symbol, base_pair, start, end)

                    return_structure.append(
                        {
                            "exchange": self.name,
                            "period": timeframe,
                            "symbol": symbol,
                            "base_pair": base_pair,
                            "dataframe": df
                        }
                    )
        return return_structure

    def _default_callback(messages):
        for m in messages:
            logging.info(m)

    def download_live(self, callback=_default_callback):

        symbols = {}

        for symbol in self.symbol:
            for base_pair in self.base_pair:
                symbols.update(
                    {f'{symbol}/{base_pair}': {"base": symbol, "quote": base_pair}})

        while True:

            try:
                data = self.ccxt_exchange.fetchTickers(symbols.keys())

                messages = []

                for symbol in symbols.keys():
                    symbol_data = data[symbol]
                    ts = Timestamp(
                        symbol_data["timestamp"], unit="ms", tz="utc")
                    message = {
                        "exchange": self.name,
                        "base": symbols.get(symbol)["base"],
                        "quote": symbols.get(symbol)["quote"],
                        "price": symbol_data["last"],
                        "timestamp": ts
                    }
                    messages.append(message)

                callback(messages)

            except Exception as e:

                logging.info("Error")
                logging.error(e)
                continue

    @classmethod
    def available_exchange(basecls, search_symbols=["BTC/USDT", "BTC/USDC"]):

        exchange_count = len(ccxt.exchanges)

        logging.info(f'using ccxt v{ccxt.__version__}')
        logging.info(f'Total exchange : {exchange_count}')
        logging.info(f'Searching available exchange for  : {search_symbols}\n')

        i = 0
        available_exchanges = {}
        for exchange in ccxt.exchanges:

            i += 1
            logging.info(f'Scaning exchange {i}/{exchange_count} : {exchange}')
            ccxt_exchange = getattr(ccxt, exchange)()

            try:
                ccxt_exchange.loadMarkets()
            except Exception as e:
                logging.info(f'Error during loading market')
                continue

            if ccxt_exchange.has.get("fetchOHLCV"):

                allfound = True
                for base_pair in search_symbols:
                    if base_pair not in ccxt_exchange.symbols:
                        allfound = False
                        logging.info(
                            f'Base pair {base_pair} not available for this exchange')

                if allfound:
                    if ccxt_exchange.timeframes:
                        available_exchanges.update(
                            {exchange: ccxt_exchange.timeframes})

                        logging.info(
                            f'OHLCV available for timeframes \
                                {list(ccxt_exchange.timeframes.keys())}')
                    else:
                        logging.info(
                            f'No timeframe available')

            else:
                logging.info(f'No ohlcv api')

        return available_exchanges
