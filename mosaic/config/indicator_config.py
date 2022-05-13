from typing import Any, Dict, List
from pydantic import BaseModel, Field


class IndicatorSourceConfig(BaseModel):
    name: str = Field(...)
    tags: Dict[str, str] = Field(None)
    history_bw: int = Field(0)
    history_fw: int = Field(0)
    values: List[str] = Field(None)
    collection: str = Field(None)


class IndicatorConfig(BaseModel):

    name: str = Field(...)
    description: str = Field(None)
    tags: Dict[str, str] = Field(None)
    source: Dict[str, IndicatorSourceConfig] = Field(None)
    parameters: Dict[str, Any] = Field(None)
    collection: str = Field(None)
