import logging
from re import I
from typing import Any, Dict, List

from mosaic.indicator.indicator_message import IndicatorMessage
from pandas import DataFrame, Timestamp
from ..database import DbClient, InfluxDataSource
from ..database.df_utils import reindex_dataframe
from ..messaging import MessageProducer
from ..messaging import MessageConsumer
from mosaic.indicator import Indicator, ReturnsCloseIndicator
from pydantic import BaseModel, Field
import numpy as np
import io


class IndicatorWrapper(BaseModel):

    output: InfluxDataSource = Field(...)
    input: List[InfluxDataSource] = Field(...)
    class_name: str = Field(...)
    parameters: Dict[str, Any] = Field({})
    indicator_impl: Indicator = Field(None)

    def __init__(self, **data):
        super().__init__(**data)
        params = self.parameters.copy()
        params.update({"class_name": self.class_name})
        self.indicator_impl = Indicator.from_config(**params)

    def accept_message(self, message: IndicatorMessage):
        for source in self.input:
            if source.accept(message):
                return True
        return False


class IndicatorCompute(BaseModel):

    indicators: List[IndicatorWrapper] = Field(...)
    db_client: DbClient = Field(...)
    message_producer: MessageProducer = Field(...)
    message_consumer: MessageConsumer = Field(...)
    write_topic: str = Field("data-write")

    def treat_message(self, indicator: IndicatorWrapper, message: IndicatorMessage):

        sources_data = []

        for source in indicator.input:
            time = message.time - indicator.indicator_impl.history_fw*source.period

            real_start = time - \
                (source.period * indicator.indicator_impl.history_bw)
            real_stop = time + \
                (source.period * indicator.indicator_impl.history_fw)

            data = self.db_client.get_data(
                source=source, start=real_start, stop=real_stop)
            logging.info(data)
            sources_data.append(data)

        return indicator.indicator_impl.compute(*sources_data)

    def save_indicator(self, values: DataFrame, indicator: IndicatorWrapper):

        if len(values) == 0:
            return

        for (index, row) in values.dropna(how='all').iterrows():

            newIndicator = IndicatorMessage()
            newIndicator.tags = indicator.output.tags

            for key in row.dropna().to_dict().keys():
                value = row.dropna().to_dict().get(key)

                # when we are in caregorical column, force str
                if values[key].dtype.name == "category":
                    value = str(value)

                newIndicator.fields.update({key: value})

            newIndicator.measurement = indicator.output.name
            newIndicator.time = index

            logging.info(f'{index} : {newIndicator.to_line_protocol()}')

            self.message_producer.send_message(newIndicator.to_line_protocol(),
                                               topic=self.write_topic,
                                               key=indicator.output.key,
                                               headers={"collection": indicator.output.collection})

    def new_message(self, message):

        logging.info(f'Receive new message : {message}')
        im = IndicatorMessage.from_line_protocol(message.value)

        for indicator in self.indicators:
            if indicator.accept_message(im):

                logging.info(
                    f'Compute indicator @ {im.time} : {type(indicator.indicator_impl).__name__} ')
                data = self.treat_message(indicator, im)
                logging.info(data)
                self.save_indicator(data, indicator)
        self.message_producer.flush()

    def start(self):
        # list topics to listen to
        topics = []
        for indicator in self.indicators:
            for source in indicator.input:
                topics.append(source.name)

        logging.info(f'Listen to topics {topics}')

        self.message_consumer.listen(callback=self.new_message, topics=topics)


class IndicatorHistoryCompute(BaseModel):

    indicators: List[IndicatorWrapper] = Field(...)
    db_client: DbClient = Field(...)
    from_date: Timestamp = Field(...)
    to_date: Timestamp = Field(...)

    def save_indicator(self, values: DataFrame, indicator: IndicatorWrapper):

        if len(values) == 0:
            return

        self.db_client.write_df(values, datasource=indicator.output)

    def start(self):

        infos = []
        for indicator in self.indicators:
            sources_data = []

            for source in indicator.input:
                real_start = self.from_date - \
                    (source.period * indicator.indicator_impl.history_bw)
                real_stop = self.to_date + \
                    (source.period * indicator.indicator_impl.history_fw)

                data = self.db_client.get_data(
                    source=source, start=real_start, stop=real_stop)

                sources_data.append(data)
                logging.debug(data.to_string())

            result = indicator.indicator_impl.compute(*sources_data)

            # remove inf and - inf value
            result.replace([np.inf, -np.inf], np.nan, inplace=True)

            result = reindex_dataframe(
                result, self.from_date, self.to_date, indicator.output.period)

            logging.debug(result.to_string())

            self.save_indicator(result, indicator)
            infos.append(
                {"indicator": indicator, "dataframe": result})

        return infos
