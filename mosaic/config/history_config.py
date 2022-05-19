from datetime import date
from typing import List
from pydantic import BaseModel, Field


class HistoryConfig(BaseModel):

    exchange: List[str] = Field([])
    symbol: List[str] = Field([])
    base_pair: List[str] = Field([])
    interval: List[str] = Field([])
    start: date = Field(None)
    end: date = Field(None)
    collection: str = Field(None)
    measurement_name: str = Field(None)
