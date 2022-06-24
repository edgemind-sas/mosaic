import logging
from typing import Dict, List

from ..indicator.config.server_config import ServerConfig
from .indicator_wrapper import IndicatorWrapper
from ..exchange.exchange import ExchangeConfig
from pydantic import BaseSettings, Field
import yaml


class MosaicSettings(BaseSettings):

    indicators: List[IndicatorWrapper] = Field([])

    server: ServerConfig = Field(None)

    history: ExchangeConfig = Field(None)


class MosaicConfig():

    __instance = None

    settings: MosaicSettings = None

    def history_config(self):
        return self.settings.history

    def indicators(self):
        return self.settings.indicators

    def server_config(self):
        return self.settings.server

    def __new__(cls, *args, **kwargs):
        if MosaicConfig.__instance is None:
            MosaicConfig.__instance = super(
                MosaicConfig, cls).__new__(cls, *args, **kwargs)
        return MosaicConfig.__instance

    def from_dict(self, config: Dict) -> MosaicSettings:
        self.settings = MosaicSettings.parse_obj(config)
        return self.settings

    def from_yaml_filename(self, yaml_filename):
        with open(yaml_filename, 'r', encoding="utf-8") as yaml_file:
            try:
                config = yaml.load(yaml_file, Loader=yaml.FullLoader)

                self.from_dict(config=config)

            except yaml.YAMLError as exc:
                logging.error(exc)
                exit(-1)

    def get(self) -> MosaicSettings:
        return self.settings
