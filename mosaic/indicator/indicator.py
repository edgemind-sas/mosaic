from pydantic import Field
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from ..core import ObjMOSAIC
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401
import numpy as np
import pandas as pd


class Indicator(ObjMOSAIC):
    """
    Technical indicator base class.
    """
    
    @property
    def bw_length(self):
        return 0

    @property
    def names_map(self):
        """Indicator names format mapping: To be overloaded"""
        return {}
    
    def names(self, names=None):

        if not names:
            var_names = list(self.names_map.values())
        elif isinstance(names, str):
            var_names = self.names_map[names]
        else:
            var_names = [self.names_map[name] for name in names]

        return var_names
    
    def compute(self, *data, **kwrds):
        pass

    def plotly(self, ohlcv_df, plot_ohlcv=False):

        var_open = self.ohlcv_names.get("open", "open")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_close = self.ohlcv_names.get("close", "close")

        if plot_ohlcv:
            fig = make_subplots(rows=2, cols=1,
                                shared_xaxes=True,
                                vertical_spacing=0.02)

            fig.add_trace(go.Candlestick(x=ohlcv_df.index,
                                         open=ohlcv_df[var_open],
                                         high=ohlcv_df[var_high],
                                         low=ohlcv_df[var_low],
                                         close=ohlcv_df[var_close], name="OHLC"),
                          row=1, col=1)
        else:
            fig = go.Figure()

        return fig


class IndicatorOHLCV(Indicator):

    variation_length: int = \
        Field(0, description="Length of data to compute indicator variation")
    
    ohlcv_names: dict = Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")

    @property
    def bw_length(self):
        return super().bw_length + self.variation_length

    def add_variation_names(self, names):
        names_var = \
            {f"{key}_var_{length + 1}": f"{name}_var_{length + 1}"
             for key, name in names.items()
             for length in range(self.variation_length)}

        return dict(names, **names_var)
    
    def compute_variation(self, indic_df, diff_var=[]):

        if self.variation_length == 0:
            return indic_df

        indic_df_list = [indic_df]

        pct_change_var = [var for var in indic_df.columns
                          if not (var in diff_var)]
        for length in range(self.variation_length):
            if len(pct_change_var) > 0:
                indic_pct_change_cur_df = \
                    indic_df[pct_change_var].pct_change(length + 1)\
                                            .replace([np.inf, -np.inf], np.nan)
                indic_pct_change_cur_df.columns = \
                    [f"{var}_var_{length + 1}"
                     for var in indic_pct_change_cur_df.columns]
                indic_df_list.append(indic_pct_change_cur_df)

            if len(diff_var) > 0:
                indic_diff_cur_df = \
                    indic_df[diff_var].diff(length + 1)\
                                      .replace([np.inf, -np.inf], np.nan)
                indic_diff_cur_df.columns = \
                    [f"{var}_var_{length + 1}"
                     for var in indic_diff_cur_df.columns]
                indic_df_list.append(indic_diff_cur_df)

        indic_df = pd.concat(indic_df_list,
                             axis=1)

        return indic_df


    # @property
    # def bw_length(self):
    #     length = (-self.horizon + 1) if self.horizon <= 0 else self.horizon
    #     return super().bw_length + length


# class Returns(ReturnsBaseIndicator):
    
#     @property
#     def names_map(self):
#         """Indicator names format mapping"""
#         return {
#             "ret": f"ret_{self.var}_{self.horizon}",
#         }
    
#     def compute(self, ohlcv_df: pd.DataFrame):

#         var = self.ohlcv_names.get(self.var)

#         indic_df = pd.DataFrame(index=ohlcv_df.index)

#         if self.horizon <= 0:
#             indic_df[self.names('ret')] = \
#                 ohlcv_df[var].pct_change(-self.horizon+1)
#         else:
#             indic_df[self.names('ret')] = \
#                 ohlcv_df[var].pct_change(self.horizon+1)\
#                              .shift(-self.horizon)
        
#         return indic_df


# class ReturnsRolling(ReturnsBaseIndicator):

#     var_ref: str = Field(
#         "close", description="Reference variable to compute returns")

#     fun: str = Field(
#         "max", description="Rolling function to be applied")

#     @property
#     def names_map(self):
#         """Indicator names format mapping"""
#         return {
#             "ret": f"ret_{self.fun}_{self.var_ref}_{self.var}_{self.horizon}",
#         }

#     def compute(self, ohlcv_df: pd.DataFrame):

#         # OHLCV variable identification
#         var_ref = self.ohlcv_names.get(self.var_ref)
#         var = self.ohlcv_names.get(self.var)

#         indic_df = pd.DataFrame(index=ohlcv_df.index)

#         if self.horizon >= 0:
#             ref_pm1 = ohlcv_df[var_ref].shift(1)
#             indic_rolling = ohlcv_df.rolling(abs(self.horizon)+1)[var]
#         else:
#             ref_pm1 = ohlcv_df[var_ref].shift(1-self.horizon)
#             indic_rolling = ohlcv_df.rolling(abs(self.horizon)+1)[var]

#         indic_rolling = getattr(indic_rolling, self.fun)()

#         if self.horizon >= 0:
#             indic_rolling = indic_rolling.shift(-self.horizon)
            
#         indic_df[self.names('ret')] = indic_rolling/ref_pm1 - 1

#         return indic_df

