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

        features_df, target_s = self.prepare_data_fit(ohlcv_df, **kwrds)

        features_df = sm.add_constant(features_df)

        mod = sm.OLS(target_s, features_df)
        self.bkd = mod.fit()

        return self

    def predict(self, ohlcv_df, **kwrds):

        features_df, _ = self.prepare_data_fit(ohlcv_df, **kwrds)

        features_df = sm.add_constant(features_df)

        target_pred_s = self.bkd.predict(features_df)

        if self.sk_preproc is not None:
            target_pred_s = self.sk_preproc.inverse_transform(target_pred_s)
        
        return target_pred_s


class PMLogit(PMReturnsUpDown):

    def fit(self, ohlcv_df, **kwrds):

        features_df, target_s = self.prepare_data_fit(ohlcv_df, **kwrds)

        features_df = sm.add_constant(features_df)

        mod = sm.Logit(target_s, features_df)
        self.bkd = mod.fit()

        return self

    def predict(self, ohlcv_df, **kwrds):

        features_df = sm.add_constant(self.prepare_features(ohlcv_df))

        return self.bkd.predict(features_df)
