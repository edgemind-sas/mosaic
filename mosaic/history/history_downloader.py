import ccxt
import logging
import pandas as pd

from mosaic.config.history_config import HistoryConfig
from pandas import Timestamp
from mosaic.db_bakend import InfluxIndicatorWriter


def download_from_exchange(ccxt_exchange, timeframe, symbol, base_pair, start, end):

    ohlcv = []

    logging.info(
        f'Download {ccxt_exchange.id} {timeframe} {symbol}/{base_pair}')

    end_time_in_ms = int(end.value / 1000000)
    start_in_ms = int(start.value / 1000000)

    while start_in_ms < end_time_in_ms:
        ohlcv.extend(ccxt_exchange.fetchOHLCV(
            f'{symbol}/{base_pair}', timeframe, start_in_ms, 2000))
        logging.info(
            f'from {Timestamp(start_in_ms*1000000)} to \
                {Timestamp(ohlcv[len(ohlcv)-1][0]*1000000)} : {len(ohlcv)}')
        start_in_ms = ohlcv[len(ohlcv)-1][0]

    df = pd.DataFrame(
        ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    df['time'] = df['time'].astype('datetime64[ms]')
    df.set_index("time", inplace=True)

    df.drop(df.loc[df.index > end].index, inplace=True)

    return df


def start_download(downloader_config: HistoryConfig):

    start = Timestamp(downloader_config.start)
    end = Timestamp(downloader_config.end)
    for exchange_name in downloader_config.exchange:

        # instanciate ccxt exchange
        ccxt_exchange = getattr(ccxt, exchange_name)()
        ccxt_exchange.enableRateLimit = True
        for timeframe in downloader_config.interval:
            for symbol in downloader_config.symbol:
                for base_pair in downloader_config.base_pair:

                    df = download_from_exchange(
                        ccxt_exchange, timeframe, symbol, base_pair, start, end)

                    df.info()

                    logging.info(f'\n {df.head()} \n\n{df.tail()}')

                    fixtags = {"symbol": f'{symbol}/{base_pair}',
                               "base": symbol,
                               "quote": base_pair,
                               "period": timeframe,
                               "exchange": exchange_name}
                    writer = InfluxIndicatorWriter(fixtags=fixtags)
                    writer.write_df(df, data_frame_measurement_name="ohlcv4",
                                    collection=downloader_config.collection)
