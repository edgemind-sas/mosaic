from typing import Dict, List
from pydantic import BaseModel, Field


class IndicatorSourceConfig(BaseModel):
    id: str = Field(...)
    tags: Dict[str, str] = Field(None)
    history_bw: int = Field(0)
    history_fw: int = Field(0)
    value: List[str] = Field([])


class IndicatorConfig(BaseModel):

    name: str = Field(...)
    description: str = Field(None)
    tags: Dict[str, str] = Field(None)
    source: Dict[str, IndicatorSourceConfig] = Field(None)
