"""
Alias module for config_loader for backwards compatibility.
"""

from .config_loader import ConfigLoader, get_config, load_config, reset_configuration

__all__ = ["load_config", "get_config", "reset_configuration", "ConfigLoader"]
