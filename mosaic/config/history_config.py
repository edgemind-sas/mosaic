from datetime import date, datetime
from typing import Dict, List
from pydantic import BaseModel, Field
from pandas import Timestamp


class HistoryConfig(BaseModel):

    exchange: List[str] = Field([])
    symbol: List[str] = Field([])
    base_pair: List[str] = Field([])
    interval: List[str] = Field([])
    start: date = Field(None)
    end: date = Field(None)
