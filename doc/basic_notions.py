# This code retrieves historic OHLCV data for the "BTC/USDC" symbol from the "binance"
# exchange and stores it in a DataFrame called `ohlcv_format_ex_df`. 

# Imports the necessary libraries, including `pandas`, `plotly`, and the MOSAIC library.
import pandas as pd
import plotly.io as pio
import mosaic
import mosaic.utils as mut
import mosaic.indicator as mid
import mosaic.trading as mtr

# Creates an instance of the `mtr.ExchangeCCXT` class, representing the "binance"
# exchange, and establishes a connection to it.
exchange = mtr.ExchangeCCXT(name="binance")
exchange.connect()

# Initializes a `mut.DSOHLCV` (Data Source OHLCV object),
# specifying the symbol ("BTC/USDC"), timeframe ("5m"), and a date range for the data.
ds_ex = mut.DSOHLCV(
    symbol="BTC/USDC",
    timeframe="5m",
    dt_start='2021-01-01 01:00:00',
    dt_end='2021-01-02 01:00:00',
)

# Uses the `exchange.get_historic_ohlcv()` method to retrieve the
# historic OHLCV (Open, High, Low, Close, Volume) data for the
# specified symbol and timeframe from the "binance" exchange.
# The data is stored in a DataFrame called `ohlcv_format_ex_df`.
ohlcv_format_ex_df = \
    exchange.get_historic_ohlcv(
        date_start=ds_ex.dt_s,
        date_end=ds_ex.dt_e,
        symbol=ds_ex.symbol,
        timeframe=ds_ex.timeframe,
        index="datetime",
        data_dir=".",
        force_reload=False,
        progress_mode=True,
    ).drop("timestamp", axis=1)

# Take a sample of 5 time intervals for the examples in the document
data_ohlcv_ex_5 = ohlcv_format_ex_df.head()

fig = mut.plotly_ohlcv(data_ohlcv_ex_5,
                       layout=dict(title="Example of OHLC data on BTC/USDC pair",
                                   yaxis_title="USDC",
                                   xaxis_title="Time"))

fig

# The code concatenates the returns calculated at different horizons (-3, -2, -1, 0, 1, 2, 3)
# into a single DataFrame. 
# Each return at a specific horizon is calculated using the MOSAIC `mid.Returns()` class with
# the specified horizon value. The `.compute` method computes the returns from the `data_ohlcv_ex_5` data. 
ref_df = pd.concat([
    mid.Returns(horizon=h).compute(data_ohlcv_ex_5)\
    for h in [-3,-2,-1,0,1,2,3]], axis=1)

# The code creates a DataFrame `ret_df` by concatenating the rolling maximum returns calculated
# at different horizons (-3, 0, 1, 2) along the columns.
# Each rolling maximum return at a specific horizon is calculated using the MOSAIC `mid.ReturnsRolling()` class.
# The `fun="max"` parameter specifies that the maximum value should be calculated, and the `var="high"` parameter indicates that the calculation should be based on the "high" variable.
# The `.compute` method computes the rolling maximum returns using the `data_ohlcv_ex_5` data. 
ret_high_df = pd.concat([
    mid.ReturnsRolling(fun="max", var="high", horizon=h).compute(data_ohlcv_ex_5)\
    for h in [-3,0,1,2]], axis=1)

ret_high_df.style.format('{0:.3%}',  na_rep='').to_html()

# Identical approach but this time to compute rolling low returns
ret_low_df = pd.concat([
    mid.ReturnsRolling(fun="min", var="low", horizon=h).compute(data_ohlcv_ex_5)\
    for h in [-3,0,1,2]], axis=1)

print(f"MOSAIC library version: {mosaic.__version__}")

lib_dict = [
    {"desc": "MOSAIC", "module": mosaic}
    ]

pd.DataFrame([{"Library": lib["desc"], "Version": getattr(lib["module"], "__version__")}
              for lib in lib_dict])\
  .style.hide(axis='index').to_html()
