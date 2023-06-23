import os
import traceback
from dataclasses import asdict, dataclass, is_dataclass
from typing import Dict

import yaml

from mage_ai.shared.hash import merge_dict
from mage_ai.shared.strings import camel_to_snake_case


@dataclass
class BaseConfig:
    @classmethod
    def load(cls, config_path: str = None, config: Dict = None):
        config_class_name = cls.__name__
        config_class_key = camel_to_snake_case(config_class_name)
        if config is None:
            cls.config_path = config_path
            if cls.config_path is None:
                raise Exception(
                    'Please provide a config_path or a config dictionary to initialize'
                    f' an {config_class_name} object',
                )
            if not os.path.exists(cls.config_path):
                raise Exception(f'{config_class_name} {cls.config_path} does not exist.')
            with open(cls.config_path) as fp:
                config = yaml.full_load(fp) or {}

        if config_class_key in config:
            config = config[config_class_key]

        config = cls.parse_config(config)
        extra_config = cls.load_extra_config()
        config = merge_dict(config, extra_config)

        for config_key, config_value in config.items():
            config_key_type = cls.__annotations__.get(config_key, None)
            if config_key_type is None or config_value is None:
                continue
            if is_dataclass(config_key_type) and isinstance(config_value, dict):
                try:
                    config[config_key] = config_key_type.load(config=config_value)
                except Exception:
                    traceback.print_exc()
                    config[config_key] = None
        return cls(**config)

    @classmethod
    def parse_config(cls, config: Dict = None) -> Dict:
        return config

    @classmethod
    def load_extra_config(cls) -> Dict:
        return {}

    def to_dict(self) -> Dict:
        return asdict(self)
