from dataclasses import dataclass
from typing import Optional

from omegaconf import MISSING, OmegaConf
from omegaconf.errors import ConfigKeyError
import pytest
import yaml

from olpxek_bot.config import ConfigLoader, DefaultConfig


@dataclass
class DummyConfigGroup:
    mandatory_field: str = MISSING
    optional_field: int = 42


@dataclass
class _TestConfig(DefaultConfig):
    dummy: Optional[DummyConfigGroup] = None


def test_load_empty_config():
    loader = ConfigLoader(config_cls=_TestConfig)
    empty_config = OmegaConf.create({})
    conf = loader.make_structured_config(empty_config)
    assert conf.dummy is None


def test_load_yaml_config():
    loader = ConfigLoader(config_cls=_TestConfig)
    missing_mandatory_field_yaml = """
dummy:
  hello: hi
"""
    config = OmegaConf.create(yaml.safe_load(missing_mandatory_field_yaml))
    empty_config = OmegaConf.create(config)
    with pytest.raises(ConfigKeyError):
        conf = loader.make_structured_config(empty_config)

    normal_yaml = """
dummy:
  mandatory_field: hello
"""
    config = OmegaConf.create(yaml.safe_load(normal_yaml))
    conf = loader.make_structured_config(config)
    assert conf.dummy is not None
    assert conf.dummy.mandatory_field == "hello"
    assert conf.dummy.optional_field == 42
