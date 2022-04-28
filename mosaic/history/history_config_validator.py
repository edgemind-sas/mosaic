import ccxt
import logging
from mosaic.config.history_config import HistoryConfig


def validate_config(donwloader_config: HistoryConfig):

    for exchange_name in donwloader_config.exchange:

        # check exchange name exist
        if exchange_name not in ccxt.exchanges:
            raise(BaseException(
                f'Exchange "{exchange_name}" does not exist in ccxt'))

        # instanciate ccxt exchange
        ccxt_exchange = getattr(ccxt, exchange_name)()

        # check ccxt exchange has ohlcvt fetch api
        if not ccxt_exchange.has.get("fetchOHLCV"):
            raise(BaseException(
                f'Exchange "{exchange_name}" doesn\'t suuport fetchOHLCV'))

        for timeframe in donwloader_config.interval:
            if timeframe not in ccxt_exchange.timeframes:
                raise(BaseException(
                    f'Timeframe {timeframe} not supported by "{exchange_name}". \
                        Supported are : {ccxt_exchange.timeframes}'))

        ccxt_exchange.loadMarkets()

        for symbol in donwloader_config.symbol:
            for base_pair in donwloader_config.base_pair:
                if f'{symbol}/{base_pair}' not in ccxt_exchange.symbols:
                    raise(BaseException(
                        f'Symbol {symbol}/{base_pair} not supported by "{exchange_name}"'))

        logging.info("History configuration is OK")
