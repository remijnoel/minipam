"""Viper-style configuration loader with environment variable overrides."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")


class StorageConfig(BaseModel):
    """Storage backend configuration."""

    type: str = Field(default="file", description="Storage type: file, memory")
    path: str = Field(default="./data", description="Storage path for file backend")


class APIKeyAuthConfig(BaseModel):
    """API key authentication configuration."""

    keys: List[str] = Field(default_factory=list, description="Valid API keys")


class OIDCAuthConfig(BaseModel):
    """OIDC authentication configuration."""

    issuer_url: str = Field(default="", description="OIDC issuer URL")
    client_id: str = Field(default="", description="OIDC client ID")
    client_secret: str = Field(default="", description="OIDC client secret")
    jwks_cache_ttl: int = Field(default=600, description="JWKS cache TTL in seconds")


class AuthConfig(BaseModel):
    """Authentication configuration."""

    backend: str = Field(default="none", description="Auth backend: none, apikey, oidc")
    apikey: APIKeyAuthConfig = Field(default_factory=APIKeyAuthConfig)
    oidc: OIDCAuthConfig = Field(default_factory=OIDCAuthConfig)


class UIConfig(BaseModel):
    """UI configuration."""

    enabled: bool = Field(default=True, description="Enable embedded UI")
    path: str = Field(default="/ui", description="UI path")


class AppConfig(BaseModel):
    """Complete application configuration."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    ui: UIConfig = Field(default_factory=UIConfig)

    @validator("storage")
    def validate_storage_type(cls, v: StorageConfig) -> StorageConfig:
        """Validate storage type."""
        if v.type not in ["file", "memory"]:
            raise ValueError("Storage type must be 'file' or 'memory'")
        return v

    @validator("auth")
    def validate_auth_backend(cls, v: AuthConfig) -> AuthConfig:
        """Validate auth backend."""
        if v.backend not in ["none", "apikey", "oidc"]:
            raise ValueError("Auth backend must be 'none', 'apikey', or 'oidc'")
        return v


class ConfigLoader:
    """
    Viper-style configuration loader.

    Loads configuration from:
    1. Environment variables (highest priority)
    2. Configuration file (YAML/JSON)
    3. Default values (lowest priority)
    """

    ENV_PREFIX = "MINIPAM_"

    def __init__(self) -> None:
        """Initialize the configuration loader."""
        self._config: Optional[AppConfig] = None

    def load(self, config_file: Optional[Union[str, Path]] = None) -> AppConfig:
        """
        Load configuration from file and environment variables.

        Args:
            config_file: Path to configuration file (YAML or JSON)

        Returns:
            Loaded and validated configuration

        Raises:
            ValueError: If configuration is invalid
            FileNotFoundError: If config file doesn't exist
        """
        # Start with defaults
        config_dict = self._get_default_config()

        # Override with file configuration
        if config_file:
            file_config = self._load_config_file(config_file)
            config_dict = self._deep_merge(config_dict, file_config)

        # Override with environment variables
        env_config = self._load_env_config()
        config_dict = self._deep_merge(config_dict, env_config)

        # Validate and create config object
        try:
            self._config = AppConfig(**config_dict)
            self._mask_secrets_in_logs()
            logger.info("Configuration loaded successfully")
            return self._config
        except Exception as e:
            raise ValueError(f"Invalid configuration: {e}")

    def get_config(self) -> AppConfig:
        """Get the loaded configuration."""
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load() first.")
        return self._config

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return AppConfig().dict()

    def _load_config_file(self, config_file: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file."""
        config_path = Path(config_file)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            content = config_path.read_text(encoding="utf-8")

            if config_path.suffix.lower() in [".yaml", ".yml"]:
                return yaml.safe_load(content) or {}
            elif config_path.suffix.lower() == ".json":
                return json.loads(content)
            else:
                # Try to parse as YAML first, then JSON
                try:
                    return yaml.safe_load(content) or {}
                except yaml.YAMLError:
                    return json.loads(content)

        except Exception as e:
            raise ValueError(f"Failed to parse configuration file {config_path}: {e}")

    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}

        for key, value in os.environ.items():
            if not key.startswith(self.ENV_PREFIX):
                continue

            # Remove prefix and convert to lowercase
            config_key = key[len(self.ENV_PREFIX) :].lower()

            # Convert underscores to nested dict structure
            nested_keys = config_key.split("_")
            current = config

            for nested_key in nested_keys[:-1]:
                if nested_key not in current:
                    current[nested_key] = {}
                current = current[nested_key]

            # Convert value to appropriate type
            final_key = nested_keys[-1]
            current[final_key] = self._convert_env_value(value)

        return config

    def _convert_env_value(self, value: str) -> Union[str, int, float, bool, List[str]]:
        """Convert environment variable string to appropriate type."""
        # Boolean values
        if value.lower() in ["true", "1", "yes", "on"]:
            return True
        elif value.lower() in ["false", "0", "no", "off"]:
            return False

        # Numeric values
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Array values (comma-separated)
        if "," in value:
            return [item.strip() for item in value.split(",") if item.strip()]

        # String value
        return value

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
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

    def _mask_secrets_in_logs(self) -> None:
        """Mask sensitive configuration values in logs."""
        if not self._config:
            return

        # Log non-sensitive configuration
        safe_config = self._config.dict()

        # Mask sensitive auth values
        if "auth" in safe_config:
            if "apikey" in safe_config["auth"] and safe_config["auth"]["apikey"].get(
                "keys"
            ):
                safe_config["auth"]["apikey"]["keys"] = ["***MASKED***"] * len(
                    safe_config["auth"]["apikey"]["keys"]
                )
            if "oidc" in safe_config["auth"] and safe_config["auth"]["oidc"].get(
                "client_secret"
            ):
                safe_config["auth"]["oidc"]["client_secret"] = "***MASKED***"

        logger.debug(f"Loaded configuration: {safe_config}")


# Global configuration instance
_config_loader = ConfigLoader()


def load_config(config_file: Optional[Union[str, Path]] = None) -> AppConfig:
    """Load application configuration."""
    return _config_loader.load(config_file)


def get_config() -> AppConfig:
    """Get the current application configuration."""
    return _config_loader.get_config()


def reset_configuration() -> None:
    """Reset configuration for testing purposes."""
    global _config_loader
    _config_loader = ConfigLoader()
