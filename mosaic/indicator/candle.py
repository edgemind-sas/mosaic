import typing
import pandas as pd
from pydantic import Field
from .indicator import IndicatorOHLCV
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


class Candle(IndicatorOHLCV):
    """This class allows to compute various indicators based on raw OHLCV data with very few loss of information"""
    remove_abs_value: bool = \
        Field(False, description="Indicates if absolute value must be removed")
    
    @property
    def bw_length(self):
        return super().bw_length
    
    @property
    def names_map(self):
        """Indicator names format mapping"""
        var_open = self.ohlcv_names.get("open", "open")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_volume = self.ohlcv_names.get("volume", "volume")

        names = {
            "body": "cdl_body",
            "sl": "cdl_sl",
            "su": "cdl_su",
            var_high: f"cdl_{var_high}",
            var_low: f"cdl_{var_low}",
        }
        names_rel = {f"{k}_r": f"{v}_r" for k, v in names.items()}
        names_all = dict(names, **names_rel)
        names_all[var_open] = f"cdl_{var_open}"
        names_all[var_volume] = f"cdl_{var_volume}"

        names_all = self.add_variation_names(names_all)
        
        return names_all
    
    def compute(self, ohlcv_df: pd.DataFrame):

        var_open = self.ohlcv_names.get("open", "open")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_close = self.ohlcv_names.get("close", "close")
        var_volume = self.ohlcv_names.get("volume", "volume")

        indic_df = ohlcv_df[[var_open, var_low, var_high, var_volume]]\
            .rename(columns=self.names_map)
        
        oc_df = ohlcv_df[[var_open, var_close]]
        min_o_c = oc_df.min(axis=1)
        max_o_c = oc_df.max(axis=1)
        indic_df[self.names("sl")] = min_o_c - ohlcv_df[var_low]
        indic_df[self.names("su")] = ohlcv_df[var_high] - max_o_c
        indic_df[self.names("body")] = \
            ohlcv_df[var_close] - ohlcv_df[var_open]

        var_list = ["body", "sl", "su"]
        for var in var_list:
            indic_df[self.names(f"{var}_r")] = \
                indic_df[self.names(var)]/ohlcv_df[var_open]

        var_list = [var_high, var_low]
        for var in var_list:
            indic_df[self.names(f"{var}_r")] = \
                indic_df[self.names(var)]/ohlcv_df[var_open] - 1

        indic_df = self.compute_variation(indic_df)
            
        return indic_df

