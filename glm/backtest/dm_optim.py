import pydantic
import typing
import pandas as pd
import pkg_resources
import tqdm
from .bt_signals import BTLong
from ..utils import compute_combinations
#from ..decision_model.dm_long import DMLong

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

PandasSeries = typing.TypeVar('pandas.core.frame.Series')
PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')


