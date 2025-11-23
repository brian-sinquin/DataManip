"""Configuration package for DataManip."""

from .app_config import get_config
from .model_config import ModelConfig

__all__ = ['get_config', 'ModelConfig']
