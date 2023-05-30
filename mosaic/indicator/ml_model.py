import pydantic
from datetime import datetime
import typing
import pandas as pd
import pkg_resources

from .indicator import Indicator

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


# TODO : Remove the Indicator dependancy
# TODO : Add the from_dict method
class MLModel(Indicator):
    """ML model schema."""

    var_features: typing.List[str] = pydantic.Field(
        default=[], description="List of features variables")

    var_targets: typing.List[str] = pydantic.Field(
        default=[], description="List of target variables")

    nb_data_fit: int = pydantic.Field(
        0, description="Number of data used to fit the model")

    def fit(self, data: pd.DataFrame, **kwds):
        raise NotImplementedError("Need to be overloaded")

    def predict_quantile(self, level, data: pd.DataFrame, logger=None, **kwds):
        raise NotImplementedError("Need to be overloaded")


class ReturnsHLCModel(MLModel):
    """ML model schema."""

    def compute(self, *data):
        nb_data_ori = self.nb_data_fit
        self.fit(data[0])
        nb_data_new = self.nb_data_fit

        ret = pd.Series(range(nb_data_ori, nb_data_new),
                        index=data[0].index, name="nb_data_fit")

        print(data)

        return ret.to_frame()

    def fit(self, data: pd.DataFrame, **kwds):
        self.nb_data_fit += len(data)
