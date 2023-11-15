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
        {'cls': 'OrderBase', 'params': {}}


def test_order_base_006(order_base_example_001):
    """test if the order is executable."""
    assert order_base_example_001.is_executable() is True


def test_order_base_007(order_base_example_001):
    """test execution of the order."""
    assert order_base_example_001.execute() is True



@pytest.fixture
def bot_order_trailing_market():
    bot_specs = {
        'cls': 'BotTrading',
        'name': 'bot_dummy',
        'mode': 'btclassic',
        'bt_buy_on': 'high',
        'bt_sell_on': 'low',
        'order_model': {'cls': 'OrderTrailingMarket'},
        'exchange': {'cls': 'ExchangeBase',
                     'name': 'test_exchange',
                     'fees_rates': {'taker': 0.002, 'maker': 0.002}},
    }
    bot = mtr.BotTrading.from_dict(bot_specs)
    return bot
    
def test_order_trailing_market_001(bot_order_trailing_market):

    class DMDummy(mdm.DMDR):

        def compute_signal_idx(self, features_df):
            idx_buy = pd.Series(False, index=features_df.index)
            idx_sell = pd.Series(False, index=features_df.index)

            ts_buy = pd.Timestamp('2023-06-01 00:05:00+0200')
            ts_sell = pd.Timestamp('2023-06-01 00:40:00+0200')
            if idx_buy.index[0] == ts_buy:
                idx_buy.loc[ts_buy] = True
            if idx_sell.index[0] == ts_sell:
                idx_sell.loc[ts_sell] = True

            return idx_buy, idx_sell

    bot_order_trailing_market.decision_model = DMDummy()

    ohlcv_dt_start = '2023-06-01 00:00:00+0200'
    ohlcv_trading_data = {}
    ohlcv_trading_data['open'] = [101, 102, 102, 108, 111, 110, 111, 114, 117, 120]
    nb_data = len(ohlcv_trading_data['open'])
    ohlcv_trading_data['low'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['high'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['close'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['volume'] = [1000]*nb_data
    ohlcv_dt = [pd.to_datetime(ohlcv_dt_start) +
                timedelta(minutes=x*5) for x in range(nb_data)]
    
    ohlcv_trading_df = pd.DataFrame(ohlcv_trading_data, index=ohlcv_dt)

    bot_order_trailing_market.start(
        ohlcv_trading_df=ohlcv_trading_df,
        ohlcv_dm_df=ohlcv_trading_df,
        data_dir=".",
        progress_mode=False,
    )

    orders_executed_list = list(bot_order_trailing_market.orders_executed.values())
    od_buy = orders_executed_list[0]
    orders_open_list = list(bot_order_trailing_market.orders_open.values())
    od_sell = orders_open_list[0]

    assert len(orders_executed_list) == 1
    assert od_buy.side == "buy"
    assert od_buy.dt_open == pd.Timestamp("2023-06-01 00:05:00+0200")
    assert od_buy.dt_closed == pd.Timestamp("2023-06-01 00:15:00+0200")
    assert len(orders_open_list) == 1
    assert od_sell.side == "sell"
    assert od_sell.dt_open == pd.Timestamp("2023-06-01 00:40:00+0200")
    assert od_sell.dt_closed is None


def test_order_trailing_market_002(bot_order_trailing_market):

    class DMDummy(mdm.DMDR):

        def compute_signal_idx(self, features_df):
            idx_buy = pd.Series(False, index=features_df.index)
            idx_sell = pd.Series(False, index=features_df.index)

            ts_buy = pd.Timestamp('2023-06-01 00:00:00+0200')
            ts_sell = pd.Timestamp('2023-06-01 00:15:00+0200')
            if idx_buy.index[0] == ts_buy:
                idx_buy.loc[ts_buy] = True
            if idx_sell.index[0] == ts_sell:
                idx_sell.loc[ts_sell] = True

            return idx_buy, idx_sell

    bot_order_trailing_market.decision_model = DMDummy()

    ohlcv_dt_start = '2023-06-01 00:00:00+0200'
    ohlcv_trading_data = {}
    ohlcv_trading_data['open'] = [101, 102, 102, 108, 111, 110, 111, 114, 117, 120]
    nb_data = len(ohlcv_trading_data['open'])
    ohlcv_trading_data['low'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['high'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['close'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['volume'] = [1000]*nb_data
    ohlcv_dt = [pd.to_datetime(ohlcv_dt_start) +
                timedelta(minutes=x*5) for x in range(nb_data)]
    
    ohlcv_trading_df = pd.DataFrame(ohlcv_trading_data, index=ohlcv_dt)

    bot_order_trailing_market.start(
        ohlcv_trading_df=ohlcv_trading_df,
        ohlcv_dm_df=ohlcv_trading_df,
        data_dir=".",
        progress_mode=False,
    )

    orders_executed_list = list(bot_order_trailing_market.orders_executed.values())
    od_buy = orders_executed_list[0]
    od_sell = orders_executed_list[1]

    assert len(orders_executed_list) == 2
    assert od_buy.side == "buy"
    assert od_buy.dt_open == pd.Timestamp("2023-06-01 00:00:00+0200")
    assert od_buy.dt_closed == pd.Timestamp("2023-06-01 00:05:00+0200")
    assert od_sell.side == "sell"
    assert od_sell.dt_open == pd.Timestamp("2023-06-01 00:15:00+0200")
    assert od_sell.dt_closed == pd.Timestamp("2023-06-01 00:25:00+0200")


def test_order_trailing_market_003(bot_order_trailing_market):

    class DMDummy(mdm.DMDR):

        def compute_signal_idx(self, features_df):
            idx_buy = pd.Series(False, index=features_df.index)
            idx_sell = pd.Series(False, index=features_df.index)

            ts_buy = pd.Timestamp('2023-06-01 00:00:00+0200')
            ts_sell = pd.Timestamp('2023-06-01 00:15:00+0200')
            if idx_buy.index[0] == ts_buy:
                idx_buy.loc[ts_buy] = True
            if idx_sell.index[0] == ts_sell:
                idx_sell.loc[ts_sell] = True

            return idx_buy, idx_sell

    bot_order_trailing_market.decision_model = DMDummy()

    ohlcv_dt_start = '2023-06-01 00:00:00+0200'
    ohlcv_trading_data = {}
    ohlcv_trading_data['open'] = [101, 103, 102, 108, 111, 110, 111, 114, 117, 120]
    nb_data = len(ohlcv_trading_data['open'])
    ohlcv_trading_data['low'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['high'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['close'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['volume'] = [1000]*nb_data
    ohlcv_dt = [pd.to_datetime(ohlcv_dt_start) +
                timedelta(minutes=x*5) for x in range(nb_data)]

    ohlcv_trading_data['low'][0] = 100
    ohlcv_trading_data['high'][0] = 100
    
    ohlcv_trading_df = pd.DataFrame(ohlcv_trading_data, index=ohlcv_dt)

    bot_order_trailing_market.start(
        ohlcv_trading_df=ohlcv_trading_df,
        ohlcv_dm_df=ohlcv_trading_df,
        data_dir=".",
        progress_mode=False,
    )

    orders_executed_list = list(bot_order_trailing_market.orders_executed.values())
    od_buy = orders_executed_list[0]
    od_sell = orders_executed_list[1]

    err_tol = 1e-6
    assert len(orders_executed_list) == 2
    assert od_buy.side == "buy"
    assert od_buy.dt_open == pd.Timestamp("2023-06-01 00:00:00+0200")
    assert od_buy.dt_closed == pd.Timestamp("2023-06-01 00:05:00+0200")
    assert od_buy.quote_price == 103
    assert abs(od_buy.quote_amount - 1) < err_tol
    assert abs(od_buy.base_amount - 0.00969) < err_tol

    assert od_sell.side == "sell"
    assert od_sell.dt_open == pd.Timestamp("2023-06-01 00:15:00+0200")
    assert od_sell.dt_closed == pd.Timestamp("2023-06-01 00:25:00+0200")
    assert od_sell.quote_price == 110
    assert abs(od_sell.quote_amount - 1.063693) < err_tol
    assert abs(od_sell.base_amount - 0.00969) < err_tol


def test_order_trailing_market_004(bot_order_trailing_market):

    class DMDummy(mdm.DMDR):

        def compute_signal_idx(self, features_df):
            idx_buy = pd.Series(False, index=features_df.index)
            idx_sell = pd.Series(False, index=features_df.index)

            ts_buy = pd.Timestamp('2023-06-01 00:00:00+0200')
            ts_sell = pd.Timestamp('2023-06-01 00:15:00+0200')
            if idx_buy.index[0] == ts_buy:
                idx_buy.loc[ts_buy] = True
            if idx_sell.index[0] == ts_sell:
                idx_sell.loc[ts_sell] = True

            return idx_buy, idx_sell

    bot_order_trailing_market.decision_model = DMDummy()

    ohlcv_dt_start = '2023-06-01 00:00:00+0200'
    ohlcv_trading_data = {}
    ohlcv_trading_data['open'] = [101, 95, 90, 108, 111, 110, 111, 114, 117, 120]
    nb_data = len(ohlcv_trading_data['open'])
    ohlcv_trading_data['low'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['high'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['close'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['volume'] = [1000]*nb_data
    ohlcv_dt = [pd.to_datetime(ohlcv_dt_start) +
                timedelta(minutes=x*5) for x in range(nb_data)]

    ohlcv_trading_data['low'][1] = 94
    ohlcv_trading_data['high'][1] = 97
    
    ohlcv_trading_df = pd.DataFrame(ohlcv_trading_data, index=ohlcv_dt)

    bot_order_trailing_market.start(
        ohlcv_trading_df=ohlcv_trading_df,
        ohlcv_dm_df=ohlcv_trading_df,
        data_dir=".",
        progress_mode=False,
    )

    orders_executed_list = list(bot_order_trailing_market.orders_executed.values())
    od_buy = orders_executed_list[0]
    od_sell = orders_executed_list[1]

    err_tol = 1e-6
    assert len(orders_executed_list) == 2
    assert od_buy.side == "buy"
    assert od_buy.dt_open == pd.Timestamp("2023-06-01 00:00:00+0200")
    assert od_buy.dt_closed == pd.Timestamp("2023-06-01 00:05:00+0200")
    assert od_buy.quote_price == 97
    assert abs(od_buy.quote_amount - 1) < err_tol
    assert abs(od_buy.base_amount - 0.010288) < err_tol

    assert od_sell.side == "sell"
    assert od_sell.dt_open == pd.Timestamp("2023-06-01 00:15:00+0200")
    assert od_sell.dt_closed == pd.Timestamp("2023-06-01 00:25:00+0200")
    assert od_sell.quote_price == 110
    assert abs(od_sell.quote_amount - 1.1294890) < err_tol
    assert abs(od_sell.base_amount - 0.010288) < err_tol


def test_order_trailing_market_005(bot_order_trailing_market):

    class DMDummy(mdm.DMDR):

        def compute_signal_idx(self, features_df):
            idx_buy = pd.Series(False, index=features_df.index)
            idx_sell = pd.Series(False, index=features_df.index)

            ts_buy = pd.Timestamp('2023-06-01 00:00:00+0200')
            ts_sell = pd.Timestamp('2023-06-01 00:15:00+0200')
            if idx_buy.index[0] == ts_buy:
                idx_buy.loc[ts_buy] = True
            if idx_sell.index[0] == ts_sell:
                idx_sell.loc[ts_sell] = True

            return idx_buy, idx_sell

    bot_order_trailing_market.decision_model = DMDummy()

    ohlcv_dt_start = '2023-06-01 00:00:00+0200'
    ohlcv_trading_data = {}
    ohlcv_trading_data['open'] = [101, 95, 90, 80, 110, 110, 111, 114, 110, 120]
    nb_data = len(ohlcv_trading_data['open'])
    ohlcv_trading_data['low'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['high'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['close'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['volume'] = [1000]*nb_data
    ohlcv_dt = [pd.to_datetime(ohlcv_dt_start) +
                timedelta(minutes=x*5) for x in range(nb_data)]
    
    ohlcv_trading_df = pd.DataFrame(ohlcv_trading_data, index=ohlcv_dt)

    bot_order_trailing_market.start(
        ohlcv_trading_df=ohlcv_trading_df,
        ohlcv_dm_df=ohlcv_trading_df,
        data_dir=".",
        progress_mode=False,
    )

    orders_executed_list = \
        list(bot_order_trailing_market.orders_executed.values())

    od_buy = orders_executed_list[0]

    err_tol = 1e-6
    
    assert len(bot_order_trailing_market.orders_open) == 0
    assert len(orders_executed_list) == 1
    
    assert od_buy.side == "buy"
    assert od_buy.dt_open == pd.Timestamp("2023-06-01 00:00:00+0200")
    assert od_buy.dt_closed == pd.Timestamp("2023-06-01 00:20:00+0200")
    assert od_buy.quote_price == 110
    assert abs(od_buy.quote_amount - 1) < err_tol
    assert abs(od_buy.base_amount - 0.0090727) < err_tol

def test_order_trailing_market_006(bot_order_trailing_market):

    class DMDummy(mdm.DMDR):

        def compute_signal_idx(self, features_df):
            idx_buy = pd.Series(False, index=features_df.index)
            idx_sell = pd.Series(False, index=features_df.index)

            ts_buy = pd.Timestamp('2023-06-01 00:00:00+0200')
            ts_sell = pd.Timestamp('2023-06-01 00:30:00+0200')
            if idx_buy.index[0] == ts_buy:
                idx_buy.loc[ts_buy] = True
            if idx_sell.index[0] == ts_sell:
                idx_sell.loc[ts_sell] = True

            return idx_buy, idx_sell

    bot_order_trailing_market.decision_model = DMDummy()

    bot_order_trailing_market.order_model.params.activation_rate = 0.002

    ohlcv_dt_start = '2023-06-01 00:00:00+0200'
    ohlcv_trading_data = {}
    ohlcv_trading_data['open'] = [101, 95, 95.10, 94, 94.50, 110, 111, 114, 117, 120]
    nb_data = len(ohlcv_trading_data['open'])
    ohlcv_trading_data['low'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['high'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['close'] = ohlcv_trading_data['open'].copy()
    ohlcv_trading_data['volume'] = [1000]*nb_data
    ohlcv_dt = [pd.to_datetime(ohlcv_dt_start) +
                timedelta(minutes=x*5) for x in range(nb_data)]

    ohlcv_trading_data['low'][7] = 113

    ohlcv_trading_df = pd.DataFrame(ohlcv_trading_data, index=ohlcv_dt)

    bot_order_trailing_market.start(
        ohlcv_trading_df=ohlcv_trading_df,
        ohlcv_dm_df=ohlcv_trading_df,
        data_dir=".",
        progress_mode=False,
    )

    orders_executed_list = list(bot_order_trailing_market.orders_executed.values())
    od_buy = orders_executed_list[0]
    od_sell = orders_executed_list[1]

    err_tol = 1e-6
    assert len(orders_executed_list) == 2
    
    assert od_buy.side == "buy"
    assert od_buy.dt_open == pd.Timestamp("2023-06-01 00:00:00+0200")
    assert od_buy.dt_closed == pd.Timestamp("2023-06-01 00:20:00+0200")
    assert od_buy.quote_price == 94.50
    assert abs(od_buy.quote_price_activation - 94.188) < err_tol
    assert abs(od_buy.quote_amount - 1) < err_tol
    assert abs(od_buy.base_amount - 0.010560) < err_tol

    assert od_sell.side == "sell"
    assert od_sell.dt_open == pd.Timestamp("2023-06-01 00:30:00+0200")
    assert od_sell.dt_closed == pd.Timestamp("2023-06-01 00:35:00+0200")
    assert od_sell.quote_price == 113
    assert abs(od_sell.quote_price_activation - 113.772) < err_tol
    assert abs(od_sell.quote_amount - 1.1909889) < err_tol
    assert abs(od_sell.base_amount - 0.01056084) < err_tol
