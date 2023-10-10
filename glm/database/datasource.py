import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from pandas import Timedelta, Timestamp, to_timedelta
from ..indicator.indicator_message import IndicatorMessage


class DataSource(BaseModel):

    name: str = Field(None)


class InfluxDataSource(DataSource):

    tags: Dict[str, str] = Field({})
    """
    history_bw: int = Field(0)
    history_fw: int = Field(0)"""
    values: List[str] = Field(None)
    collection: str = Field(None)
    period: Timedelta = Field(None)
    key: str = Field(None)

    def __init__(self, **data):
        super().__init__(**data)
        if "period" in self.tags:
            self.period = to_timedelta(self.tags.get("period"))
        else:
            self.period = to_timedelta("0")

        self.key = f'{self.collection}.{self.name}'

        for tag in sorted(self.tags.keys()):
            self.key += f'.{tag}:{self.tags.get(tag)}'

    def get_str_info(self):

        str_info = []
        str_info.append(self.name)
        str_info.append(self.collection)
        tags_str = ':'.join(self.tags.values())
        str_info.append(tags_str)
        return "_".join(str_info)

    def accept(self, message: IndicatorMessage):

        if self.name != message.measurement:
            return False

        for key in self.tags.keys():
            if key not in message.tags.keys():
                return False
            if self.tags.get(key) != message.tags.get(key):
                return False
        return True

    def has_period(self):
        return self.period.total_seconds() > 0

    '''
    def real_start(self, start: Timestamp):
        return start - (self.period * self.history_bw)

    def real_stop(self, stop: Timestamp):
        return stop + (self.period * self.history_fw)
    '''
