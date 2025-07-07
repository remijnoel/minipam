"""
Configuration module for CIDR Management Service

This module provides configuration management with support for:
- Configuration files (YAML/JSON)
- Environment variable overrides
- Intelligent defaults
- Multiple storage backends
"""

from typing import Any, Dict, Optional

from .config_loader import get_config as get_loaded_config
from .config_loader import load_config

# Global configuration - will be set when load_configuration is called
_config: Optional[Dict[str, Any]] = None


def load_configuration(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or environment variables"""
    global _config
    _config = load_config(config_path)
    return _config


def get_config() -> Dict[str, Any]:
    """Get the current configuration, loading defaults if not already loaded"""
    global _config
    if _config is None:
        _config = get_loaded_config()
    return _config


# Legacy configuration access (for backward compatibility)
def _get_config_value(path: list, default_value: Any = None) -> Any:
    """Get a configuration value using dot notation path"""
    config = get_config()

    for key in path:
        if isinstance(config, dict) and key in config:
            config = config[key]
        else:
            return default_value

    return config


# Environment-based configuration (legacy support)
USE_FILE_BACKEND = _get_config_value(["storage", "type"]) == "file"
CIDR_FILE_PATH = _get_config_value(["storage", "file", "path"], "cidrs.json")

# Server configuration
HOST = _get_config_value(["server", "host"], "0.0.0.0")
PORT = _get_config_value(["server", "port"], 8000)
LOG_LEVEL = _get_config_value(["server", "log_level"], "info")

# Debug mode
DEBUG_MODE = _get_config_value(["debug"], False)


def get_storage_config() -> Dict[str, Any]:
    """Get storage configuration"""
    return _get_config_value(
        ["storage"], {"type": "memory", "file": {"path": "cidrs.json"}}
    )


def get_server_config() -> Dict[str, Any]:
    """Get server configuration"""
    return _get_config_value(
        ["server"], {"host": "0.0.0.0", "port": 8000, "log_level": "info"}
    )


def get_cors_config() -> Dict[str, Any]:
    """Get CORS configuration"""
    return _get_config_value(["cors"], {"enabled": True, "origins": ["*"]})


def get_ui_config() -> Dict[str, Any]:
    """Get UI configuration"""
    return _get_config_value(["ui"], {"enabled": True, "path": "webui/dist"})
