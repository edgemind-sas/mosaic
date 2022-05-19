

from pandas import DataFrame, Timestamp
import pandas as pd
from .indicator_source import IndicatorSource
import logging


class IndicatorResultValidator:

    def validate_dataframe(self, source: IndicatorSource, time: Timestamp, res: DataFrame):

        # get all expected date in a list
        period_string = source.config.tags.get("period")
        period = pd.to_timedelta(period_string)

        start_time: Timestamp = time - (period * source.get_history_bw())
        nb_steps = source.get_history_bw() + source.get_history_fw()
        step_times = []
        for i in range(nb_steps+1):
            step_times.append(start_time + period*i)

        # check that dataframe has this count and ordered valu
        if res.empty or len(res) != len(step_times):
            logging.info(
                f'Expected {len(step_times)} values but dataframe has {len(res)}')
            return False

        for index, expectedtime in enumerate(step_times):
            if res.index[index] != expectedtime:
                logging.info(
                    f'Expected row n°{index} time to be {expectedtime} \
                        but was {res.loc[index].index}')
                return False

        # optionally check fields colums and value not null
        return True
