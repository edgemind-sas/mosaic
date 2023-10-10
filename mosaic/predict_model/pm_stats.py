import pydantic
import typing
import statsmodels.api as sm

from .pm_base import PMReturns, PMReturnsUpDown

import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


class PMOLS(PMReturns):

    def fit(self, ohlcv_df, **kwrds):

        features_df, target_s = super().fit(ohlcv_df, **kwrds)

        features_df = sm.add_constant(features_df)

        mod = sm.OLS(target_s, features_df)
        self.bkd = mod.fit()

    def predict(self, ohlcv_df, **kwrds):

        features_df = sm.add_constant(self.compute_features(ohlcv_df))

        return self.bkd.predict(features_df)


class PMLogit(PMReturnsUpDown):

    def fit(self, ohlcv_df, **kwrds):

        features_df, target_s = super().fit(ohlcv_df, **kwrds)

        features_df = sm.add_constant(features_df)

        mod = sm.Logit(target_s, features_df)
        self.bkd = mod.fit()

    def predict(self, ohlcv_df, **kwrds):

        features_df = sm.add_constant(self.compute_features(ohlcv_df))

        return self.bkd.predict(features_df)
