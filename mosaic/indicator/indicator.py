import logging
from typing import Any, Dict
from pydantic import BaseModel, Field

from ..db_bakend.query_indicator import InfluxIndicatorQueryClient
from .query.query_builder import QueryBuilder

from .indicator_source import IndicatorSource
from .indicator_config import IndicatorConfig


class Indicator(BaseModel):

    config: IndicatorConfig = Field(None)

    sources: Dict[str, IndicatorSource] = Field({})

    servers_config: Dict = Field(None)

    query_client: InfluxIndicatorQueryClient = Field(None)

    query_builder: QueryBuilder = Field(None)

    def __init__(self, indicator_config: IndicatorConfig, servers_config: Dict):

        super().__init__()

        self.config = indicator_config

        # for each source in config, create a source with callback
        for name in self.config.source:
            sourceConfig = self.config.source.get(name)
            self.sources.update(
                {name: IndicatorSource(name=name, config=sourceConfig)})

        self.servers_config = servers_config

        self.query_client = InfluxIndicatorQueryClient(
            self.servers_config["db_server_config"])
        self.query_builder = QueryBuilder()

    def get_sources_data(self,  time):

        sourceData: Dict[str, Any] = {}

        db_config = self.servers_config["db_server_config"]

        for source in self.sources.values():
            query = self.query_builder.buildQuery(
                source=source, bucket=db_config["bucket"], time=time)
            result = self.query_client.queryAsDataFrame(query=query)
            sourceData.update({source.name: result})

        return sourceData

    def compute_indicator(self, sourceData: Dict[str, Any]):
        logging.error(
            "Generic indicator type doesn't have a compute indicator implementation")
        return {}
