from dataclasses import dataclass
from mage_ai.shared.config import BaseConfig
from typing import Dict
# import traceback

ECS_CONTAINER_METADATA_URI_VAR = 'ECS_CONTAINER_METADATA_URI_V4'


@dataclass
class K8sResourceConfig(BaseConfig):
    cpu: str
    memory: str


@dataclass
class K8sExecutorConfig(BaseConfig):
    resource_limits: Dict = None
    resource_requests: Dict = None

    @classmethod
    def load(cls, config_path: str = None, config: Dict = None):
        return super().load(config_path=config_path, config=config)
