"""Configuration module for manuscript generation pipeline."""

from src.config.script_config import (
    DatasetConfig,
    ScriptConfig,
    get_default_scripts,
    resolve_script_font,
    resolve_script_input,
)
from src.config.settings import (
    BackgroundConfig,
    EffectsConfig,
    LayoutConfig,
    PageConfig,
)

__all__ = [
    "BackgroundConfig",
    "EffectsConfig",
    "LayoutConfig",
    "PageConfig",
    "ScriptConfig",
    "DatasetConfig",
    "get_default_scripts",
    "resolve_script_font",
    "resolve_script_input",
]
