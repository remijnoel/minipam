"""
Configuration loader for MiniPAM

Supports loading configuration from YAML or JSON files with intelligent defaults
and environment variable overrides.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

logger = logging.getLogger("minipam.config_loader")


class ConfigurationError(Exception):
    """Raised when there's an issue with configuration loading or validation"""

    pass


class ConfigLoader:
    """Configuration loader with support for YAML/JSON files and environment overrides"""

    def __init__(self):
        self.config: Dict[str, Any] = {}
        self._loaded_from: Optional[str] = None
        self._is_loaded = False

    def load_from_file(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from a file (YAML or JSON)"""
        config_path = Path(config_path)

        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Determine file type and parse accordingly
            if config_path.suffix.lower() in [".yaml", ".yml"]:
                if not HAS_YAML:
                    raise ConfigurationError(
                        "YAML support not available. Install PyYAML: pip install PyYAML"
                    )
                self.config = yaml.safe_load(content) or {}
            elif config_path.suffix.lower() == ".json":
                self.config = json.loads(content)
            else:
                # Try to detect format from content
                try:
                    self.config = json.loads(content)
                except json.JSONDecodeError:
                    if HAS_YAML:
                        self.config = yaml.safe_load(content) or {}
                    else:
                        raise ConfigurationError(
                            f"Could not parse config file {config_path}. "
                            "Ensure it's valid JSON or install PyYAML for YAML support."
                        )

            self._loaded_from = str(config_path)
            logger.info(f"Configuration loaded from {config_path}")
            self._is_loaded = True

            # Apply environment variable overrides
            self._apply_env_overrides()

            return self.get_config()

        except (yaml.YAMLError if HAS_YAML else Exception, json.JSONDecodeError) as e:
            raise ConfigurationError(
                f"Error parsing configuration file {config_path}: {e}"
            )

    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration"""
        # Map environment variables to config paths
        env_mappings = {
            "MINIPAM_STORAGE_TYPE": ["storage", "type"],
            "MINIPAM_STORAGE_FILE_PATH": ["storage", "file", "path"],
            "MINIPAM_SERVER_HOST": ["server", "host"],
            "MINIPAM_SERVER_PORT": ["server", "port"],
            "MINIPAM_SERVER_LOG_LEVEL": ["server", "log_level"],
            "MINIPAM_DEBUG": ["debug"],
            # Authentication configuration
            "MINIPAM_AUTH_BACKEND": ["auth", "backend"],
            "MINIPAM_JWT_SECRET": ["auth", "jwt", "secret"],
            "MINIPAM_JWT_ALGORITHM": ["auth", "jwt", "algorithm"],
            "MINIPAM_JWT_EXPIRY_HOURS": ["auth", "jwt", "expiry_hours"],
            # OIDC configuration
            "MINIPAM_OIDC_CLIENT_ID": ["auth", "oidc", "client_id"],
            "MINIPAM_OIDC_CLIENT_SECRET": ["auth", "oidc", "client_secret"],
            "MINIPAM_OIDC_ISSUER_URL": ["auth", "oidc", "issuer_url"],
            "MINIPAM_OIDC_REDIRECT_URI": ["auth", "oidc", "redirect_uri"],
            "MINIPAM_OIDC_SCOPE": ["auth", "oidc", "scope"],
            "MINIPAM_OIDC_ROLE_CLAIM": ["auth", "oidc", "role_claim"],
            "MINIPAM_OIDC_ROLE_MAPPING": ["auth", "oidc", "role_mapping"],
            "MINIPAM_OIDC_DEFAULT_ROLE": ["auth", "oidc", "default_role"],
            # Legacy environment variables for backward compatibility
            "USE_FILE_BACKEND": ["storage", "type"],  # Maps to 'file' if 'true'
            "CIDR_FILE_PATH": ["storage", "file", "path"],
            "HOST": ["server", "host"],
            "PORT": ["server", "port"],
            "LOG_LEVEL": ["server", "log_level"],
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Special handling for legacy USE_FILE_BACKEND
                if env_var == "USE_FILE_BACKEND":
                    if value.lower() == "true":
                        value = "file"
                    else:
                        continue  # Don't override if not 'true'

                # Special handling for port (convert to int)
                if config_path[-1] in ("port", "expiry_hours"):
                    try:
                        value = int(value)
                    except ValueError:
                        logger.warning(
                            "Invalid integer value in %s: %s", env_var, value
                        )
                        continue

                # Special handling for debug (convert to bool)
                if config_path[-1] == "debug":
                    value = str(value).lower() in ("true", "1", "yes", "on")

                # Set the value in config
                self._set_nested_value(self.config, config_path, value)
                logger.debug(
                    "Applied environment override: %s -> %s = %s",
                    env_var,
                    ".".join(map(str, config_path)),
                    value,
                )

        # Handle API key environment variables (MINIPAM_API_KEY_<USERNAME>=<key>:<role>)
        for env_var, env_value in os.environ.items():
            if env_var.startswith("MINIPAM_API_KEY_"):
                username = env_var[len("MINIPAM_API_KEY_") :].lower()
                if ":" in env_value:
                    # Ensure auth.api_keys section exists
                    if "auth" not in self.config:
                        self.config["auth"] = {}
                    if "api_keys" not in self.config["auth"]:
                        self.config["auth"]["api_keys"] = {}

                    self.config["auth"]["api_keys"][username] = env_value
                    logger.debug("Applied API key for user: %s", username)

    def _set_nested_value(self, config: Dict[str, Any], path: list, value: Any):
        """Set a nested value in the configuration dictionary"""
        for key in path[:-1]:
            config = config.setdefault(key, {})
        config[path[-1]] = value

    def get_default_config(self) -> Dict[str, Any]:
        """Get the default configuration"""
        return {
            "server": {"host": "0.0.0.0", "port": 8000, "log_level": "info"},
            "storage": {
                "type": "memory",  # 'memory' or 'file'
                "file": {"path": "cidrs.json"},
            },
            "debug": False,
            "cors": {"enabled": True, "origins": ["*"]},
            "ui": {"enabled": True, "path": "webui/dist"},
            "auth": {
                "backend": "none",
                "jwt": {
                    "secret": None,
                    "algorithm": "HS256",
                    "expiry_hours": 8,
                },
                "api_keys": {},
                "oidc": {
                    "client_id": "",
                    "client_secret": "",
                    "issuer_url": "",
                    "redirect_uri": "http://localhost:8000/auth/callback/oidc",
                    "scope": "openid profile email",
                    "role_claim": "groups",
                    "role_mapping": "",
                    "default_role": "readonly",
                },
            },
        }

    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration, merging with defaults"""
        default_config = self.get_default_config()
        # Deep merge user config over defaults
        merged_config = self._deep_merge(default_config, self.config)
        return merged_config

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def validate_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Validate the configuration"""
        if config is None:
            config = self.get_config()

        # Validate storage configuration
        storage_type = config.get("storage", {}).get("type", "memory")
        if storage_type not in ["memory", "file"]:
            raise ConfigurationError(
                f"Invalid storage type: {storage_type}. Must be 'memory' or 'file'"
            )

        if storage_type == "file":
            file_path = config.get("storage", {}).get("file", {}).get("path")
            if not file_path:
                raise ConfigurationError("File storage requires a file path")

        # Validate server configuration
        server_config = config.get("server", {})
        port = server_config.get("port")
        if not isinstance(port, int) or not (1 <= port <= 65535):
            raise ConfigurationError(
                f"Invalid port: {port}. Must be an integer between 1 and 65535"
            )

        log_level = server_config.get("log_level", "").lower()
        valid_log_levels = ["debug", "info", "warning", "error", "critical"]
        if log_level not in valid_log_levels:
            raise ConfigurationError(
                f"Invalid log level: {log_level}. Must be one of {valid_log_levels}"
            )

        return True

    def save_example_config(self, path: Union[str, Path], config_format: str = "yaml"):
        """Save an example configuration file"""
        config = self.get_default_config()
        path = Path(path)

        if config_format.lower() == "yaml":
            if not HAS_YAML:
                raise ConfigurationError(
                    "YAML support not available. Install PyYAML: pip install PyYAML"
                )
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        logger.info("Example configuration saved to %s", path)


# --- Singleton Instance ---
config_loader = ConfigLoader()


# --- Public Functions ---
def load_configuration(
    config_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Load configuration from file or return defaults"""
    if config_path:
        return config_loader.load_from_file(config_path)

    # If no path is provided and config is not loaded, apply env vars over defaults
    if not config_loader._is_loaded:
        config_loader._apply_env_overrides()
        config_loader._is_loaded = True

    return config_loader.get_config()


def get_config() -> Dict[str, Any]:
    """Get the current configuration, loading if necessary."""
    if not config_loader._is_loaded:
        load_configuration()
    return config_loader.get_config()


def validate_config(config: Optional[Dict[str, Any]] = None) -> bool:
    """Validate configuration"""
    return config_loader.validate_config(config)


def save_example_config(path: Union[str, Path], config_format: str = "yaml"):
    """Save an example configuration file"""
    config_loader.save_example_config(path, config_format)


# --- Configuration Accessor Functions ---
def _get_config_value(path: list, default_value: Any = None) -> Any:
    """Get a configuration value using a list of keys."""
    config = get_config()
    for key in path:
        if isinstance(config, dict) and key in config:
            config = config[key]
        else:
            return default_value
    return config


def get_storage_config() -> Dict[str, Any]:
    """Get storage configuration"""
    return _get_config_value(["storage"], {})


def get_server_config() -> Dict[str, Any]:
    """Get server configuration"""
    return _get_config_value(["server"], {})


def get_cors_config() -> Dict[str, Any]:
    """Get CORS configuration"""
    return _get_config_value(["cors"], {})


def get_ui_config() -> Dict[str, Any]:
    """Get UI configuration"""
    return _get_config_value(["ui"], {})


def get_auth_config() -> Dict[str, Any]:
    """Get authentication configuration"""
    return _get_config_value(["auth"], {})


def get_auth_backend() -> str:
    """Get the authentication backend name"""
    return _get_config_value(["auth", "backend"], "none")


def get_jwt_config() -> Dict[str, Any]:
    """Get JWT configuration"""
    return _get_config_value(["auth", "jwt"], {})


def get_api_keys_config() -> Dict[str, str]:
    """Get API keys configuration"""
    return _get_config_value(["auth", "api_keys"], {})


def get_oidc_config() -> Dict[str, Any]:
    """Get OIDC configuration"""
    return _get_config_value(["auth", "oidc"], {})


def get_debug_mode() -> bool:
    """Get debug mode status"""
    return _get_config_value(["debug"], False)
