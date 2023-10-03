import typing
import pandas as pd
from pydantic import Field
from .indicator import IndicatorOHLCV
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


class ReturnsBaseIndicator(IndicatorOHLCV):
    var: str = Field(
        "close", description="Variable name on which computing returns")

    horizon: int = \
        Field(0, description="Returns time step in past or future")
    
    @property
    def bw_length(self):
        length = (-self.horizon + 1) if self.horizon <= 0 else self.horizon
        return super().bw_length + length


class Returns(ReturnsBaseIndicator):
    
    names_fmt: dict = Field(
        {"ret": "ret_{var}_{horizon}"}, description="Names format mapping")
    
    def compute(self, ohlcv_df: pd.DataFrame):

        var = self.ohlcv_names.get(self.var)

        indic_df = pd.DataFrame(index=ohlcv_df.index)

        if self.horizon <= 0:
            indic_df[self.names[0]] = \
                ohlcv_df[var].pct_change(-self.horizon+1)
        else:
            indic_df[self.names[0]] = \
                ohlcv_df[var].pct_change(self.horizon+1)\
                             .shift(-self.horizon)
        
        return indic_df


class ReturnsRolling(ReturnsBaseIndicator):

    var_ref: str = Field(
        "close", description="Reference variable to compute returns")

    fun: str = Field(
        "max", description="Rolling function to be applied")

    names_fmt: dict = Field(
        {"ret": "ret_{fun}_{var_ref}_{var}_{horizon}"}, description="Names format mapping")

    def compute(self, ohlcv_df: pd.DataFrame):

        # OHLCV variable identification
        var_ref = self.ohlcv_names.get(self.var_ref)
        var = self.ohlcv_names.get(self.var)

        indic_df = pd.DataFrame(index=ohlcv_df.index)

        if self.horizon >= 0:
            ref_pm1 = ohlcv_df[var_ref].shift(1)
            indic_rolling = ohlcv_df.rolling(abs(self.horizon)+1)[var]
        else:
            ref_pm1 = ohlcv_df[var_ref].shift(1-self.horizon)
            indic_rolling = ohlcv_df.rolling(abs(self.horizon)+1)[var]

        indic_rolling = getattr(indic_rolling, self.fun)()

        if self.horizon >= 0:
            indic_rolling = indic_rolling.shift(-self.horizon)
            
        indic_df[self.names[0]] = indic_rolling/ref_pm1 - 1

        return indic_df

