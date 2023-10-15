from dataclasses import dataclass
from typing import cast, Optional, Type, Union

from omegaconf import DictConfig, ListConfig, MISSING, OmegaConf


@dataclass
class Sentry:
    dsn: str = MISSING


@dataclass
class Kimp:
    exchange_rate_api_url: str = MISSING
    exchange_rate_result_ref_key: str = MISSING


@dataclass
class DefaultConfig:
    sentry: Optional[Sentry] = None
    kimp: Optional[Kimp] = None


class ConfigLoader:
    def __init__(
        self,
        config_filename: str = "config.yaml",
        config_cls: Type[DefaultConfig] = DefaultConfig,
    ) -> None:
        self.config_filename = config_filename
        self.config_cls = config_cls

    def load_config(self) -> DefaultConfig:
        config = OmegaConf.load(self.config_filename)
        return self.make_structured_config(config)

    def make_structured_config(self, config: Union[DictConfig, ListConfig]) -> DefaultConfig:
        schema = OmegaConf.structured(self.config_cls)
        merged = OmegaConf.merge(schema, config)
        return cast(DefaultConfig, merged)

    def default_config(self) -> DefaultConfig:
        config = OmegaConf.structured(self.config_cls)
        return cast(DefaultConfig, config)
