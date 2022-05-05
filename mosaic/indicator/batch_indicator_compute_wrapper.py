import logging
from typing import Dict
from mosaic.config.mosaic_config import MosaicConfig
from mosaic.db_bakend.write_indicator import InfluxIndicatorWriter
from pandas import DataFrame, Timestamp
from pydantic import BaseModel, Field
from ..indicator import Indicator
import time


class BatchIndicatorComputeWrapper(BaseModel):

    indicator: Indicator = Field(None)
    sources_data: Dict = None

    def __init__(self,  indicator: Indicator, start: Timestamp, stop: Timestamp):
        super().__init__()
        self.indicator = indicator

        self.batch_compute(start, stop)

    def batch_compute(self, start: Timestamp, stop: Timestamp):

        start_time = time.time()

        self.sources_data: dict[str, DataFrame] = self.indicator.get_sources_data_for_period(
            start, stop)

        logging.info(
            f'--- get_sources_data_for_period ---  {time.time() - start_time}')

        start_time = time.time()

        # compute all point
        result: DataFrame = self.indicator.compute_indicator_batch(
            self.sources_data, start, stop)

        logging.info(
            f'--- compute_indicator_batch ---  {time.time() - start_time}')

        logging.info(f'Compute {len(result)} data')
        logging.info(f'{result} data')

        start_time = time.time()

        # save them to influx
        fixtags = self.indicator.config.tags

        writer = InfluxIndicatorWriter(fixtags)

        writer.write_df(result, self.indicator.config.name)

        logging.info(f'--- write_df ---  {time.time() - start_time}')
