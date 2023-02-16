import pydantic
from ..core import ObjMOSAIC
import pkg_resources
import datetime

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


class SignalBase(pydantic.BaseModel):

    time: datetime.datetime = pydantic.Field(
        ..., description="Signal datetime")

    signal: datetime.datetime = pydantic.Field(
        ..., description="Signal value")

class TradeBase(ObjMOSAIC):
    pass

class TradeLong(TradeBase):

    buy_time: datetime.datetime = pydantic.Field(
        None, description="Buy datetime")

    buy_price: float = pydantic.Field(
        None, description="Buy price")

    sell_time: datetime.datetime = pydantic.Field(
        None, description="Sell datetime")

    sell_price: datetime.datetime = pydantic.Field(
        None, description="Sell price")

    duration: datetime.timedelta = pydantic.Field(
        None, description="Trade duration")
    
    returns: datetime.datetime = pydantic.Field(
        None, description="Trade returns")


