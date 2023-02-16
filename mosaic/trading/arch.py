import logging
import pydantic
import typing
import pkg_resources
import pandas as pd
import numpy as np
import plotly.express as px

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

from .exchange import ExchangeBase
from ..core import ObjMOSAIC
from ..bot.bot_base import BotBase

PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')
PandasSeries = typing.TypeVar('pandas.core.frame.Series')




class DMConfig(pydantic.BaseModel):

    fit_horizon: int = pydantic.Field(
        None, description="Number of historical data used to adjust decision model ")

    predict_horizon: int = pydantic.Field(
        None, description="Number of decisions before updating decision model")


class TradingArch(pydantic.BaseModel):

    name: str = pydantic.Field(
        None, description="Name of the trading architecture")

    symbol: str = pydantic.Field(
        ..., description="Trading symbol")

    base: str = pydantic.Field(None, description="Base asset symbol")
    quote: str = pydantic.Field(None, description="Quote asset symbol")

    timeframe: str = pydantic.Field(
        ..., description="Trading timeframe")
    
    bot: BotBase = pydantic.Field(
        None, description="Bot")

    # ohlcv_df: PandasDataFrame = pydantic.Field(
    #     None, description="BT OHLCV data")

    # asset_norm: PandasSeries = pydantic.Field(
    #     None, description="Asset evolution normalized over the period")

    # dm_config: DMConfig = pydantic.Field(
    #     DMConfig(), description="Decision Model learning parameters")

    # ohlcv_names: dict = pydantic.Field(
    #     {v: v for v in ["open", "high", "low", "close", "volume"]},
    #     description="OHLCV variable name dictionnary")

    exchange: ExchangeBase = pydantic.Field(
        None, description="Trading architecture exchange")

    @pydantic.validator('base', always=True)
    def set_default_base(cls, base, values):
        return values.get("symbol").split("/")[0]

    @pydantic.validator('quote', always=True)
    def set_default_quote(cls, quote, values):
        return values.get("symbol").split("/")[1]


    def start_session(self, **kwrds):
        ipdb.set_trace()
        
