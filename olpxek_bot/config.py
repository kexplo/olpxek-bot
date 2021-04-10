from dataclasses import dataclass
from typing import cast, Optional, Type

from omegaconf import MISSING, OmegaConf


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
        schema = OmegaConf.structured(self.config_cls)
        config = OmegaConf.load(self.config_filename)
        merged = OmegaConf.merge(schema, config)
        return cast(DefaultConfig, merged)

    def default_config(self) -> DefaultConfig:
        config = OmegaConf.structured(self.config_cls)
        return cast(DefaultConfig, config)
