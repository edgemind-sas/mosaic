

from pandas import DataFrame, Timestamp
import pandas as pd
from .indicator_source import IndicatorSource
import logging


class IndicatorResultValidator:

    def validate_dataframe(self, source: IndicatorSource, time: Timestamp, res: DataFrame):

        # get all expected date in a list
        period_string = source.config.tags.get("period")
        period = pd.to_timedelta(period_string)

        start_time: Timestamp = time - (period * source.config.history_bw)
        nb_steps = source.config.history_bw + source.config.history_fw
        step_times = []
        for i in range(nb_steps+1):
            step_times.append(start_time + period*i)

        # check that dataframe has this count and ordered valu
        if(len(res) != len(step_times)):
            logging.info(
                f'Expected {len(step_times)} values but dataframe has {len(res)}')
            return False

        for index, expectedtime in enumerate(step_times):
            if res.loc[index, "time"] != expectedtime:
                logging.info(
                    f'Expected row n°{index} time to be {expectedtime} \
                        but was {res.loc[index, "time"]}')
                return False

        # optionally check fields colums and value not null
        return True
