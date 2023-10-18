import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import mosaic

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
    buy_threshold=0.05,
    sell_threshold=0.125,
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

import pandas as pd

idx_buy = \
    dm.pm_buy.compute_returns(ohlcv_test_df)
idx_sell = \
    dm.pm_sell.compute_returns(ohlcv_test_df)
decisions_true = pd.Series("pass",
                           index=ohlcv_test_df.index,
                           dtype="object",
                           name="decision_true")
decisions_true.loc[idx_buy] = "buy"
decisions_true.loc[idx_sell] = "sell"

decisions_mod = dm.predict(ohlcv_test_df)

decisions_confmat = pd.crosstab(decisions_mod["decision"], decisions_true)
decisions_confmat



# We can also visually represent the results of the decision model using the `plotly` method. The
# following code displays the decisions for the first 3600 timestamps:

fig = dm.plotly(
    ohlcv_test_df.iloc[:3600],
    layout=dict(
        title="Decision model results")
)
