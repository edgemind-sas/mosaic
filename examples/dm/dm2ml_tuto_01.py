import mosaic.indicator as mid

indic_1 = mid.SRI(length=5)
indic_2 = mid.MFI(length=5)

import mosaic.predict_model as mpr

pm_up = mpr.PMLogit(
    returns_horizon=15,
    direction="up",
    threshold=0.00001,
    features=[indic_1, indic_2],
)

pm_down = mpr.PMLogit(
    returns_horizon=15,
    direction="down",
    threshold=0.00001,
    features=[indic_1, indic_2],
)

import mosaic.decision_model as mdm

dm = mdm.DM2ML(
    pm_buy=pm_up,
    pm_sell=pm_down,
    buy_threshold=0.01,
    sell_threshold=0.01,
    )

import mosaic.trading as mtr

exchange = mtr.ExchangeCCXT(name="binance")
exchange.connect()

ohlcv_fit_df = \
    exchange.get_historic_ohlcv(
        date_start='2023-10-01 00:00:00',
        date_end='2023-10-10 00:00:00',
        symbol='BTC/FDUSD',
        timeframe='1s',
        index="datetime",
        data_dir=".",
        progress_mode=True,
    )

dm.fit(ohlcv_fit_df)

print(dm.pm_buy.bkd.summary())

print(dm.pm_sell.bkd.summary())

ohlcv_test_df = \
    exchange.get_historic_ohlcv(
        date_start='2023-10-10 00:00:00',
        date_end='2023-10-15 00:00:00',
        symbol='BTC/FDUSD',
        timeframe='1s',
        index="datetime",
        data_dir=".",
        progress_mode=True,
    )

dm.predict(ohlcv_test_df.head(50))
