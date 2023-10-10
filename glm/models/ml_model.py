import pydantic
from datetime import datetime
import typing
import pandas as pd
import pkg_resources

from ..indicator import Indicator

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


# TODO:Convert as a classmethod
# Maybe overload the from_dict pydantic method
def create_mlmodel(**specs):

    MLModel_sub_dict = {cls.__name__: cls for cls in get_subclasses(MLModel)}

    model_classname = specs.pop("cls")
    model_cls = MLModel_sub_dict.get(model_classname)

    if model_cls is None:
        raise ValueError(f"{model_classname} is not a subclass of MLModel")

    model = model_cls(**specs)

    return model


class ReturnsHLCModel(Indicator):
    """ML model schema."""

    var_features: typing.List[str] = pydantic.Field(
        default=[], description="List of features variables")

    var_targets: typing.List[str] = pydantic.Field(
        default=[], description="List of target variables")

    nb_data_fit: int = pydantic.Field(
        0, description="Number of data used to fit the model")

    def compute(self, data: pd.DataFrame):
        self.fit(data)
        return self.nb_data_fit

    def fit(self, data: pd.DataFrame, **kwds):
        self.nb_data_fit += len(data)

    def predict_quantile(self, level, data: pd.DataFrame, logger=None, **kwds):
        raise NotImplementedError("Need to be overloaded")
