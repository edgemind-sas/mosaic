import mosaic.indicator as mid
import mosaic.decision_model as mdm
import mosaic.trading as mtr
import pytest
from datetime import datetime, timedelta
import pkg_resources
import pandas as pd
import numpy as np
import os
import pathlib
import typing

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
EXPECTED_PATH = os.path.join(os.path.dirname(__file__), "expected")
pathlib.Path(DATA_PATH).mkdir(parents=True, exist_ok=True)
pathlib.Path(EXPECTED_PATH).mkdir(parents=True, exist_ok=True)



@pytest.fixture
def data_btc_usdc_20_df():

    data_filename = os.path.join(DATA_PATH, "data_btc_usdc_20.csv")
    data_df = pd.read_csv(data_filename, sep=",", index_col="timestamp")
    return data_df

# =============== Tests begin here ================== #

@pytest.fixture
def order_base_example_001():
    return mtr.OrderBase(uid='uid',
                         bot_uid='bot_uid',
                         test_mode=True,
                         symbol='BTC/ETH',
                         timeframe='1d',
                         side='buy',
                         quote_amount=0.5,
                         base_amount=2,
                         quote_price=0.3,
                         status='open',
                         dt_open=datetime.now(),
                         dt=datetime.now(),
                         )


def test_order_base_001(order_base_example_001):
    """test generation of default id."""
    assert isinstance(order_base_example_001.uid, str)


def test_order_base_002(order_base_example_001):
    """test base returns the correct base asset."""
    assert order_base_example_001.base == 'BTC'


def test_order_base_003(order_base_example_001):
    """test quote returns the correct quote asset."""
    assert order_base_example_001.quote == 'ETH'


def test_order_base_004(order_base_example_001):
    """test if the quote_price field is updated correctly."""
    order_base_example_001.update(quote_price=0.4)
    assert order_base_example_001.quote_price == 0.4


def test_order_base_005(order_base_example_001):
    """test dict_params returns the correct parameters.
    """
    assert order_base_example_001.dict_params() == \
        {'cls': 'OrderBase', 'params': {"exec_bound_rate": 0}}


def test_order_base_006(order_base_example_001):
    """test if the order is executable."""
    assert order_base_example_001.is_executable() is True


def test_order_base_007(order_base_example_001):
    """test execution of the order."""
    assert order_base_example_001.execute() is True


@pytest.fixture
def bot_order_market():
    bot_specs = {
        'cls': 'BotTrading',
        'name': 'bot_market',
        'mode': 'btclassic',
        'order_model': {
            'cls': 'OrderMarket',
        },
        'exchange': {
            'cls': 'ExchangeBase',
            'name': 'test_exchange',
        },
    }
    bot = mtr.BotTrading.from_dict(bot_specs)
    return bot


class DMDummyBuySell(mdm.DMDR):
    """A dummy decision model that produces buy and sell signals based on specified timestamps.

    This class is designed to simplify the testing of trading strategies by providing
    controlled buy and sell signals at predetermined times.

    Attributes:
        ts_buy (datetime): The predetermined timestamp to generate a buy signal.
        ts_sell (datetime): The predetermined timestamp to generate a sell signal.
        
    """

    ts_buy: datetime
    ts_sell: datetime

    def compute_signal_idx(self, features_df):
        """Computes the indices where buy and sell signals should be emitted."""

        idx_buy = pd.Series(False, index=features_df.index)
        idx_sell = pd.Series(False, index=features_df.index)

        if idx_buy.index[0] == self.ts_buy:
            idx_buy.loc[self.ts_buy] = True
        if idx_sell.index[0] == self.ts_sell:
            idx_sell.loc[self.ts_sell] = True

        return idx_buy, idx_sell


def prepare_simple_ohlc_data(data, dt_start, tdelta):
    """Prepares a simple OHLC DataFrame with identical open, high, low, and close values.

    This function creates a DataFrame intended for testing trading algorithms by using
    a list of price data and generating OHLC (open, high, low, close) values that are all
    equal to the price data provided.

    Args:
        data (List[float]): The price data for the OHLC values.
        dt_start (str or datetime): The start datetime of the OHLC data.
        tdelta (timedelta): The time interval between each data point.

    Returns:
        pd.DataFrame: A DataFrame with columns for 'open', 'high', 'low', 'close', each
        populated with the values from the data list, and a datetime index starting from
        `dt_start` with increments defined by `tdelta`.
    """
    nb_data = len(data)
    index = [pd.to_datetime(dt_start) +
             x*tdelta for x in range(nb_data)]

    ohlc_df = pd.DataFrame(
        {"open": data, "low": data, "high": data, "close": data},
        index=index)

    return ohlc_df


@pytest.mark.parametrize("fees", [0, 0.001, 0.01])
def test_order_market_001(bot_order_market, fees):
    # Test data
    dt_start = '2023-06-01 00:00:00+0200'
    data = [101, 102, 102, 108, 111, 110, 111, 114, 117, 120]
    tdelta = timedelta(minutes=5)
    ts_buy = pd.Timestamp('2023-06-01 00:05:00+0200')
    ts_sell = pd.Timestamp('2023-06-01 00:40:00+0200')
    tol_abs = 1e-6
    fees = fees

    # expected results
    od_buy_dt_closed = ts_buy
    od_buy_quote_price = 102
    od_buy_quote_amount = 1
    od_buy_base_amount = (1 - fees) * od_buy_quote_amount/od_buy_quote_price
    
    od_sell_dt_closed = ts_sell
    od_sell_quote_price = 117
    od_sell_quote_amount = (1 - fees) * od_buy_base_amount*od_sell_quote_price
    
    
    # Run test
    bot_order_market.decision_model = \
        DMDummyBuySell(ts_buy=ts_buy, ts_sell=ts_sell)
    bot_order_market.exchange.fees_rates.taker = fees

    ohlcv_trading_df = \
        prepare_simple_ohlc_data(
            data=data,
            dt_start=dt_start,
            tdelta=tdelta,
        )
            
    bot_order_market.start(
        ohlcv_trading_df=ohlcv_trading_df,
        ohlcv_dm_df=ohlcv_trading_df,
    )

    orders_executed_list = list(bot_order_market.orders_executed.values())
    od_buy = orders_executed_list[0]
    od_sell = orders_executed_list[1]

    # Assertions
    assert len(orders_executed_list) == 2
    
    assert od_buy.side == "buy"
    assert od_buy.dt_open == ts_buy
    assert od_buy.dt_closed == od_buy_dt_closed
    assert od_buy.quote_price == od_buy_quote_price
    assert od_buy.quote_amount == pytest.approx(od_buy_quote_amount, tol_abs)
    assert od_buy.base_amount == pytest.approx(od_buy_base_amount, tol_abs)
    
    assert od_sell.side == "sell"
    assert od_sell.dt_open == ts_sell
    assert od_sell.dt_closed == od_sell_dt_closed
    assert od_sell.quote_price == od_sell_quote_price
    assert od_sell.quote_amount == pytest.approx(od_sell_quote_amount, tol_abs)
    assert od_sell.base_amount == od_buy.base_amount


@pytest.mark.parametrize("fees", [0, 0.1, 0.01])
def test_order_market_002(bot_order_market, fees):

    # Test data
    dt_start = '2023-06-01 00:00:00+0200'
    data = [101, 102, 101.70, 108, 111, 110, 111, 114, 117, 118]
    tdelta = timedelta(minutes=5)
    ts_buy = pd.Timestamp('2023-06-01 00:05:00+0200')
    ts_sell = pd.Timestamp('2023-06-01 00:40:00+0200')
    exec_bound_rate = 0.001
    tol_abs = 1e-6
    fees = fees
    

    # expected results
    od_buy_dt_closed = pd.Timestamp('2023-06-01 00:10:00+0200')
    od_buy_quote_price = 101.70
    od_buy_quote_amount = 1
    od_buy_base_amount = (1 - fees) * od_buy_quote_amount/od_buy_quote_price
    
    od_sell_dt_closed = pd.Timestamp('2023-06-01 00:45:00+0200')
    od_sell_quote_price = 118
    od_sell_quote_amount = (1 - fees) * od_buy_base_amount*od_sell_quote_price
    
    
    # Run test
    bot_order_market.decision_model = \
        DMDummyBuySell(ts_buy=ts_buy, ts_sell=ts_sell)
    bot_order_market.exchange.fees_rates.taker = fees
    bot_order_market.order_model.params.exec_bound_rate = exec_bound_rate
    
    ohlcv_trading_df = \
        prepare_simple_ohlc_data(
            data=data,
            dt_start=dt_start,
            tdelta=tdelta,
        )
            
    bot_order_market.start(
        ohlcv_trading_df=ohlcv_trading_df,
        ohlcv_dm_df=ohlcv_trading_df,
    )

    orders_executed_list = list(bot_order_market.orders_executed.values())
    od_buy = orders_executed_list[0]
    od_sell = orders_executed_list[1]
    
    # Assertions
    assert len(orders_executed_list) == 2
    
    assert od_buy.side == "buy"
    assert od_buy.dt_open == ts_buy
    assert od_buy.dt_closed == od_buy_dt_closed
    assert od_buy.quote_price == od_buy_quote_price
    assert od_buy.quote_amount == pytest.approx(od_buy_quote_amount, tol_abs)
    assert od_buy.base_amount == pytest.approx(od_buy_base_amount, tol_abs)
    
    assert od_sell.side == "sell"
    assert od_sell.dt_open == ts_sell
    assert od_sell.dt_closed == od_sell_dt_closed
    assert od_sell.quote_price == od_sell_quote_price
    assert od_sell.quote_amount == pytest.approx(od_sell_quote_amount, tol_abs)
    assert od_sell.base_amount == od_buy.base_amount


@pytest.mark.parametrize("fees", [0, 0.1, 0.01])
def test_order_market_003(bot_order_market, fees):

    # Test data
    dt_start = '2023-06-01 00:00:00+0200'
    data = [101, 102, 101.70, 108, 111, 110, 111, 114, 117, 117]
    tdelta = timedelta(minutes=5)
    ts_buy = pd.Timestamp('2023-06-01 00:05:00+0200')
    ts_sell = pd.Timestamp('2023-06-01 00:40:00+0200')
    exec_bound_rate = 0.001
    tol_abs = 1e-6
    fees = fees
    

    # expected results
    od_buy_dt_closed = pd.Timestamp('2023-06-01 00:10:00+0200')
    od_buy_quote_price = 101.70
    od_buy_quote_amount = 1
    od_buy_base_amount = (1 - fees) * od_buy_quote_amount/od_buy_quote_price    
    
    # Run test
    bot_order_market.decision_model = \
        DMDummyBuySell(ts_buy=ts_buy, ts_sell=ts_sell)
    bot_order_market.exchange.fees_rates.taker = fees
    bot_order_market.order_model.params.exec_bound_rate = exec_bound_rate
    
    ohlcv_trading_df = \
        prepare_simple_ohlc_data(
            data=data,
            dt_start=dt_start,
            tdelta=tdelta,
        )
            
    bot_order_market.start(
        ohlcv_trading_df=ohlcv_trading_df,
        ohlcv_dm_df=ohlcv_trading_df,
    )

    orders_open_list = list(bot_order_market.orders_open.values())
    orders_executed_list = list(bot_order_market.orders_executed.values())
    od_buy = orders_executed_list[0]
    
    # Assertions
    assert len(orders_open_list) == 1
    assert len(orders_executed_list) == 1
    
    assert od_buy.side == "buy"
    assert od_buy.dt_open == ts_buy
    assert od_buy.dt_closed == od_buy_dt_closed
    assert od_buy.quote_price == od_buy_quote_price
    assert od_buy.quote_amount == pytest.approx(od_buy_quote_amount, tol_abs)
    assert od_buy.base_amount == pytest.approx(od_buy_base_amount, tol_abs)
    

@pytest.mark.parametrize("fees", [0, 0.1, 0.01])
def test_order_market_004(bot_order_market, fees):

    # Test data
    dt_start = '2023-06-01 00:00:00+0200'
    data = [101, 102, 103, 104, 102, 101, 111, 114, 117, 118]
    tdelta = timedelta(minutes=5)
    ts_buy = pd.Timestamp('2023-06-01 00:05:00+0200')
    ts_sell = pd.Timestamp('2023-06-01 00:15:00+0200')
    exec_bound_rate = 0.001
    tol_abs = 1e-6
    fees = fees
    

    # expected results
    od_buy_dt_open = ts_buy
    od_buy_dt_closed = pd.Timestamp('2023-06-01 00:25:00+0200')
    od_buy_quote_price = 101
    od_buy_quote_amount = 1
    od_buy_base_amount = (1 - fees) * od_buy_quote_amount/od_buy_quote_price

    od_sell_dt_open = None
    od_sell_dt_closed = None
    od_sell_quote_price = None
    od_sell_quote_amount = None
    
    # Run test
    bot_order_market.decision_model = \
        DMDummyBuySell(ts_buy=ts_buy, ts_sell=ts_sell)
    bot_order_market.exchange.fees_rates.taker = fees
    bot_order_market.order_model.params.exec_bound_rate = exec_bound_rate
    
    ohlcv_trading_df = \
        prepare_simple_ohlc_data(
            data=data,
            dt_start=dt_start,
            tdelta=tdelta,
        )
            
    bot_order_market.start(
        ohlcv_trading_df=ohlcv_trading_df,
        ohlcv_dm_df=ohlcv_trading_df,
    )
    
    orders_open_list = list(bot_order_market.orders_open.values())
    orders_executed_list = list(bot_order_market.orders_executed.values())
    if od_buy_dt_open and od_buy_dt_closed:
        od_buy = orders_executed_list[0]
        if od_sell_dt_open and not od_sell_dt_closed:
            od_sell = orders_open_list[0]
        elif od_sell_dt_closed:
            od_sell = orders_executed_list[1]
        else:
            od_sell = None
    elif od_buy_dt_open:
        od_buy = od_sell = orders_open_list[0]
        od_sell = None
    else:
        od_buy = None
        od_sell = None
        
    # Assertions
    if od_buy:
        assert od_buy.side == "buy"
        assert od_buy.dt_open == od_buy_dt_open
        assert od_buy.dt_closed == od_buy_dt_closed
        assert od_buy.quote_price == od_buy_quote_price
        if od_buy.dt_closed is not None:
            assert od_buy.quote_amount == pytest.approx(od_buy_quote_amount, tol_abs)
            assert od_buy.base_amount == pytest.approx(od_buy_base_amount, tol_abs)

    if od_sell:
        assert od_sell.side == "sell"
        assert od_sell.dt_open == od_sell_dt_open
        assert od_sell.dt_closed == od_sell_dt_closed
        assert od_sell.quote_price == od_sell_quote_price
        if od_sell.dt_closed is not None:
            assert od_sell.quote_amount == pytest.approx(od_sell_quote_amount, tol_abs)
            assert od_sell.base_amount == od_buy.base_amount


def test_order_market_005(bot_order_market):

    # Test data
    dt_start = '2023-06-01 00:00:00+0200'
    data = [101, 102, 103, 104, 102, 102, 111, 114, 117, 118]
    tdelta = timedelta(minutes=5)
    ts_buy = pd.Timestamp('2023-06-01 00:05:00+0200')
    ts_sell = pd.Timestamp('2023-06-01 00:15:00+0200')
    exec_bound_rate = 0.001
    tol_abs = 1e-6
    fees = 0.001
    

    # expected results
    od_buy_dt_open = ts_buy
    od_buy_dt_closed = None
    od_buy_quote_price = 118
    od_buy_quote_amount = 1
    od_buy_base_amount = None

    od_sell_dt_open = None
    od_sell_dt_closed = None
    od_sell_quote_price = None
    od_sell_quote_amount = None
    
    # Run test
    bot_order_market.decision_model = \
        DMDummyBuySell(ts_buy=ts_buy, ts_sell=ts_sell)
    bot_order_market.exchange.fees_rates.taker = fees
    bot_order_market.order_model.params.exec_bound_rate = exec_bound_rate
    
    ohlcv_trading_df = \
        prepare_simple_ohlc_data(
            data=data,
            dt_start=dt_start,
            tdelta=tdelta,
        )
            
    bot_order_market.start(
        ohlcv_trading_df=ohlcv_trading_df,
        ohlcv_dm_df=ohlcv_trading_df,
    )
    
    orders_open_list = list(bot_order_market.orders_open.values())
    orders_executed_list = list(bot_order_market.orders_executed.values())
    if od_buy_dt_open and od_buy_dt_closed:
        od_buy = orders_executed_list[0]
        if od_sell_dt_open and not od_sell_dt_closed:
            od_sell = orders_open_list[0]
        elif od_sell_dt_closed:
            od_sell = orders_executed_list[1]
        else:
            od_sell = None
    elif od_buy_dt_open:
        od_buy = od_sell = orders_open_list[0]
        od_sell = None
    else:
        od_buy = None
        od_sell = None
        
    # Assertions
    if od_buy:
        assert od_buy.side == "buy"
        assert od_buy.dt_open == od_buy_dt_open
        assert od_buy.dt_closed == od_buy_dt_closed
        assert od_buy.quote_price == od_buy_quote_price
        if od_buy.dt_closed is not None:
            assert od_buy.quote_amount == pytest.approx(od_buy_quote_amount, tol_abs)
            assert od_buy.base_amount == pytest.approx(od_buy_base_amount, tol_abs)

    if od_sell:
        assert od_sell.side == "sell"
        assert od_sell.dt_open == od_sell_dt_open
        assert od_sell.dt_closed == od_sell_dt_closed
        assert od_sell.quote_price == od_sell_quote_price
        if od_sell.dt_closed is not None:
            assert od_sell.quote_amount == pytest.approx(od_sell_quote_amount, tol_abs)
            assert od_sell.base_amount == od_buy.base_amount

    
@pytest.fixture
def bot_order_trailing_market():
    bot_specs = {
        'cls': 'BotTrading',
        'name': 'bot_trailing_market',
        'mode': 'btclassic',
        'order_model': {'cls': 'OrderTrailingMarket'},
        'exchange': {'cls': 'ExchangeBase',
                     'name': 'test_exchange',
                     },
    }
    bot = mtr.BotTrading.from_dict(bot_specs)
    return bot


def test_order_trailing_market_001(bot_order_trailing_market):

    # Test data
    dt_start = '2023-06-01 00:00:00+0200'
    data = [101, 100, 99, 98, 99, 101, 111, 114, 117, 115]
    tdelta = timedelta(minutes=5)
    ts_buy = pd.Timestamp('2023-06-01 00:05:00+0200')
    ts_sell = pd.Timestamp('2023-06-01 00:30:00+0200')
    exec_bound_rate = 0.01
    exec_trailing_rate = None
    tol_abs = 1e-6
    fees = 0.002
    

    # expected results
    od_buy_dt_open = ts_buy
    od_buy_dt_closed = pd.Timestamp('2023-06-01 00:20:00+0200')
    od_buy_quote_price = 99
    od_buy_quote_amount = 1
    od_buy_base_amount = (1 - fees) * od_buy_quote_amount/od_buy_quote_price

    od_sell_dt_open = ts_sell
    od_sell_dt_closed = pd.Timestamp('2023-06-01 00:45:00+0200')
    od_sell_quote_price = 115
    od_sell_quote_amount = (1 - fees) * od_buy_base_amount*od_sell_quote_price
    
    # Run test
    bot = bot_order_trailing_market
    bot.decision_model = \
        DMDummyBuySell(ts_buy=ts_buy, ts_sell=ts_sell)
    bot.exchange.fees_rates.taker = fees
    bot.order_model.params.exec_bound_rate = exec_bound_rate
    bot.order_model.params.exec_trailing_rate = exec_trailing_rate
    
    ohlcv_trading_df = \
        prepare_simple_ohlc_data(
            data=data,
            dt_start=dt_start,
            tdelta=tdelta,
        )
            
    bot.start(
        ohlcv_trading_df=ohlcv_trading_df,
        ohlcv_dm_df=ohlcv_trading_df,
    )
    
    orders_open_list = list(bot.orders_open.values())
    orders_executed_list = list(bot.orders_executed.values())
    if od_buy_dt_open and od_buy_dt_closed:
        od_buy = orders_executed_list[0]
        if od_sell_dt_open and not od_sell_dt_closed:
            od_sell = orders_open_list[0]
        elif od_sell_dt_closed:
            od_sell = orders_executed_list[1]
        else:
            od_sell = None
    elif od_buy_dt_open:
        od_buy = od_sell = orders_open_list[0]
        od_sell = None
    else:
        od_buy = None
        od_sell = None

    # Assertions
    if od_buy:
        assert od_buy.side == "buy"
        assert od_buy.dt_open == od_buy_dt_open
        assert od_buy.dt_closed == od_buy_dt_closed
        assert od_buy.quote_price == od_buy_quote_price
        if od_buy.dt_closed is not None:
            assert od_buy.quote_amount == pytest.approx(od_buy_quote_amount, tol_abs)
            assert od_buy.base_amount == pytest.approx(od_buy_base_amount, tol_abs)

    if od_sell:
        assert od_sell.side == "sell"
        assert od_sell.dt_open == od_sell_dt_open
        assert od_sell.dt_closed == od_sell_dt_closed
        assert od_sell.quote_price == od_sell_quote_price
        if od_sell.dt_closed is not None:
            assert od_sell.quote_amount == pytest.approx(od_sell_quote_amount, tol_abs)
            assert od_sell.base_amount == od_buy.base_amount



