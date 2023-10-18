import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import mosaic

import mosaic.trading as mtr

exchange = mtr.ExchangeCCXT(name="binance")
exchange.connect()

ohlcv_ex_df = \
    exchange.get_historic_ohlcv(
        date_start='2021-01-01 00:00:00',
        date_end='2021-01-02 00:00:00',
        symbol='BTC/USDC',
        timeframe='5m',
        index="datetime",
        data_dir=".",
        progress_mode=True,
    )



# Let's create a SRI indicator with a window length of 10 time units:

import mosaic.indicator as mid

indic_sri_ex = mid.SRI(length=10)



# We can compute de RSI indicators on the OHLCV data example using the =compute= method as follows:

sri_ex_df = \
    indic_sri_ex.compute(ohlcv_ex_df)




# The RSI indicator has the =plotly= method, which allows for graphical visualization of the values taken by the indicator on OHLCV data:

fig = indic_sri_ex.plotly(ohlcv_ex_df,
                          layout=dict(
                              title="BTC/USDC x Support Range Index"))

# Technical Environment

# The Python libraries used in the processes presented in this document are:

print(f"MOSAIC library version: {mosaic.__version__}")

lib_dict = [
    {"desc": "MOSAIC", "module": mosaic}
    ]

pd.DataFrame([{"Library": lib["desc"], "Version": getattr(lib["module"], "__version__")}
              for lib in lib_dict])\
  .style.hide(axis='index').to_html()
