import typing
import pandas as pd
from pydantic import Field, PrivateAttr
from ..indicator import ReturnsCloseIndicator, ReturnsHighIndicator, ReturnsLowIndicator
from . import ScoreOHLCV

import pkg_resources

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

PandasSeries = typing.TypeVar('pandas.core.frame.Series')
PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')


class WERScore(ScoreOHLCV):
    horizon: typing.List[int] = \
        Field([0], description="Returns time steps in past or future")
    period_name: str = \
        Field("period", description="Returns period column index name")
    period_fmt: str = \
        Field(None, description="Returns columns format")
    returns_hlc: typing.Dict[str, PandasDataFrame] = \
        Field({}, description="Returns dictionnary")

    def compute_returns_hlc(self, ohlcv_df: pd.DataFrame):

        returns_hlc = {}
        self.returns_hlc["high"] = ReturnsHighIndicator(
            horizon=self.horizon,
            period_name=self.period_name,
            period_fmt=self.period_fmt,
            ohlcv_names=self.ohlcv_names).compute(ohlcv_df)
        self.returns_hlc["low"] = ReturnsLowIndicator(
            horizon=self.horizon,
            period_name=self.period_name,
            period_fmt=self.period_fmt,
            ohlcv_names=self.ohlcv_names).compute(ohlcv_df)
        self.returns_hlc["close"] = ReturnsCloseIndicator(
            horizon=self.horizon,
            period_name=self.period_name,
            period_fmt=self.period_fmt,
            ohlcv_names=self.ohlcv_names).compute(ohlcv_df)

        return self.returns_hlc

    def fit(self, ohlcv_df: pd.DataFrame):

        self.compute_returns_hlc(ohlcv_df)

    def compute(self,
                indic=None,
                level_high: float = 0.5,
                level_low: float = 0.5):
        """
        level_high: [0,1] = High returns expected level
        level_low: [0,1] = Low returns expected level
        """
        ret_df_d = {k: data.dropna()
                    for k, data in self.returns_hlc.items()}

        if not(indic is None):
            indic_names = list(indic.columns) if isinstance(indic, pd.DataFrame)\
                else [indic.name]

            ret_indic_df_d = {ret_name: ret_df.join(indic).dropna()
                              for ret_name, ret_df in ret_df_d.items()}

            for ret_name, ret_df in ret_indic_df_d.items():
                col_index_name = ret_df_d[ret_name].columns.name
                ret_df.set_index(indic_names, inplace=True)
                ret_df.columns.name = col_index_name

            ret_grp_d = {ret_name: ret_df.reset_index().groupby(indic_names)
                         for ret_name, ret_df in ret_indic_df_d.items()}

            rho_high_base = ret_grp_d["high"].quantile(level_high)
            rho_high = rho_high_base.loc[ret_indic_df_d["high"].index]
            rho_low_base = ret_grp_d["low"].quantile(1 - level_low)
            rho_low = rho_low_base.loc[ret_indic_df_d["low"].index]
            rho_close_base = ret_grp_d["close"].mean()

        else:
            ret_indic_df_d = ret_df_d
            ret_grp_d = ret_df_d

            rho_high_base = ret_grp_d["high"].quantile(level_high)
            rho_high = rho_high_base
            rho_low_base = ret_grp_d["low"].quantile(1 - level_low)
            rho_low = rho_low_base
            rho_close_base = ret_grp_d["close"].mean()

        idx_pi_pm = \
            (ret_indic_df_d["high"] > rho_high) & \
            (ret_indic_df_d["low"] < rho_low)
        # idx_pi_plus = \
        #     (ret_indic_df_d["high"] > rho_high) & \
        #     (ret_indic_df_d["low"] > rho_low)
        # idx_pi_minus = \
        #     (ret_indic_df_d["high"] < rho_high) & \
        #     (ret_indic_df_d["low"] < rho_low)
        # idx_pi_c = \
        #     (ret_indic_df_d["high"] < rho_high) & \
        #     (ret_indic_df_d["low"] > rho_low)

        if not(indic is None):
            idx_pi_pm_grp = idx_pi_pm.reset_index().groupby(indic_names)
            # idx_pi_plus_grp = idx_pi_plus.groupby(idx_pi_plus.index)
            # idx_pi_minus_grp = idx_pi_minus.groupby(idx_pi_minus.index)
            # idx_pi_c_grp = idx_pi_c.groupby(idx_pi_c.index)
        else:
            idx_pi_pm_grp = idx_pi_pm
            # idx_pi_plus_grp = idx_pi_plus
            # idx_pi_minus_grp = idx_pi_minus
            # idx_pi_c_grp = idx_pi_c

        pi_pm = idx_pi_pm_grp.mean()
        # pi_plus = idx_pi_plus_grp.mean()
        # pi_minus = idx_pi_minus_grp.mean()
        # pi_c_check = idx_pi_c_grp.mean()

        pi_high = 1 - level_high - 0.5*pi_pm
        pi_low = 1 - level_low - 0.5*pi_pm
        pi_c = level_high + level_low + pi_pm - 1

        # Check
        # check_ones = pi_plus + pi_minus + pi_pm + pi_c
        # check_true = pi_c == pi_c_check
        # check_ones_bis = pi_high + pi_low + pi_c

        wer = rho_high_base*pi_high + rho_low_base*pi_low + rho_close_base*pi_c

        return wer


class PWERScore(WERScore):

    def compute(self,
                indic,
                level_high: float = 0.5,
                level_low: float = 0.5):
        """
        level_high: [0,1] = High returns expected level
        level_low: [0,1] = Low returns expected level
        """

        wer_ref = super().compute(level_high=level_high,
                                  level_low=level_low)
        wer_indic = super().compute(level_high=level_high,
                                    level_low=level_low,
                                    indic=indic)
        pwer = wer_indic - wer_ref

        return pwer


class AWERScore(WERScore):

    def compute(self,
                indic=None,
                level_risk: float = 0.5):
        """
        level_risk: [0,1] = High returns expected level
        """

        return super().compute(
            indic=indic,
            level_high=level_risk,
            level_low=1-level_risk)


class PAWERScore(AWERScore):

    def compute(self,
                indic,
                level_risk: float = 0.5):
        """
        level_risk: [0,1] = High returns expected level
        """

        awer_ref = super().compute(level_risk=level_risk)
        awer_indic = super().compute(level_risk=level_risk,
                                     indic=indic)
        pawer = awer_indic - awer_ref

        return pawer
