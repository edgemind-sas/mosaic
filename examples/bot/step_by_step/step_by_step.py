import pandas as pd

ohlcv_df = pd.read_csv("ohlcv.csv", index_col="datetime")

import mosaic.indicator as mid

indic_rsi = mid.RSI(length=10)

indic_rsi.compute(ohlcv_df)

import mosaic.predict_model as mpr

pm_up = mpr.PMLogit(
    returns_horizon=5,
    direction="up",
    threshold=0.00001,
    features=[indic_rsi],
)

pm_up.compute_returns(ohlcv_df)

pm_up.fit(ohlcv_df)

pm_up.bkd.summary()

pm_up.predict(ohlcv_df)

indic_mfi_5 = mid.MFI(length=5)
indic_mfi_20 = mid.MFI(length=20)

pm_down = mpr.PMLogit(
    returns_horizon=5,
    direction="down",
    threshold=0.00001,
    features=[indic_mfi_5, indic_mfi_20],
)

pm_down.fit(ohlcv_df)

pm_down.bkd.summary()

import mosaic.decision_model as mdm

dm = mdm.DM2ML(
    pm_buy=pm_up,
    pm_sell=pm_down,
    buy_threshold=0.01,
    sell_threshold=0.01,
    )

dm.predict(ohlcv_df).head(50)

import mosaic.trading as mtr

exchange = mtr.ExchangeCCXT(
    name="binance",
    fees_rates=dict(
        taker=0,
        maker=0,
    ))

import mosaic.utils as mut

ds_fit = mut.DSOHLCV(
    symbol="BTC/FDUSD",
    timeframe="1s",
    dt_start="2023-09-14 00:00:00",
    dt_end="2023-09-15 00:00:00",
)

ds_trading = mut.DSOHLCV(
    symbol="BTC/FDUSD",
    timeframe="1s",
    dt_start="2023-09-15 00:00:00",
    dt_end="2023-09-16 00:00:00",
)

bot = mtr.BotTrading(
    name="test",
    ds_trading=ds_trading,
    ds_fit=ds_fit,
    decision_model=dm,
    exchange=exchange,
)

bot.start(progress_mode=True)

print(bot.portfolio.report())
