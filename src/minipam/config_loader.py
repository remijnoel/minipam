"""
Configuration loader for MiniPAM.

This module handles loading and parsing configuration from files and environment variables.
Environment variables always take precedence over configuration files.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number."""
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


class StorageConfig(BaseModel):
    """Storage configuration."""

    type: str = Field(default="memory", description="Storage backend type")
    path: Optional[str] = Field(None, description="Storage path for file backend")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate storage type."""
        valid_types = ["memory", "file"]
        if v not in valid_types:
            raise ValueError(f"Storage type must be one of: {valid_types}")
        return v


class APIKeyConfig(BaseModel):
    """API Key configuration."""
    
    keys: List[str] = Field(default_factory=list, description="List of valid API keys")


class OIDCConfig(BaseModel):
    """OIDC configuration."""
    
    issuer_url: Optional[str] = Field(None, description="OIDC issuer URL")
    client_id: Optional[str] = Field(None, description="OIDC client ID")
    client_secret: Optional[str] = Field(None, description="OIDC client secret")
    jwks_cache_ttl: int = Field(default=300, description="JWKS cache TTL in seconds")


class AuthConfig(BaseModel):
    """Authentication configuration."""

    backend: str = Field(default="none", description="Authentication backend")
    apikey: Optional[APIKeyConfig] = Field(None, description="API key configuration")
    oidc: Optional[OIDCConfig] = Field(None, description="OIDC configuration")

    @field_validator("backend")
    @classmethod
    def validate_backend(cls, v: str) -> str:
        """Validate authentication backend."""
        valid_backends = ["none", "apikey", "oidc"]
        if v not in valid_backends:
            raise ValueError(f"Auth backend must be one of: {valid_backends}")
        return v


class UIConfig(BaseModel):
    """UI configuration."""

    enabled: bool = Field(default=True, description="Enable web UI")
    path: str = Field(default="/ui", description="UI path")


class AppConfig(BaseModel):
    """Application configuration."""

    server: ServerConfig = Field(
        default_factory=lambda: ServerConfig(), description="Server configuration"
    )
    storage: StorageConfig = Field(
        default_factory=lambda: StorageConfig(), description="Storage configuration"
    )
    auth: AuthConfig = Field(
        default_factory=lambda: AuthConfig(), description="Authentication configuration"
    )
    ui: UIConfig = Field(
        default_factory=lambda: UIConfig(), description="UI configuration"
    )


class ConfigLoader:
    """Configuration loader with environment variable support."""

    def __init__(self):
        self._config: Optional[AppConfig] = None
        self._env_prefix = "MINIPAM_"

    def load_config(self, config_path: Optional[str] = None) -> AppConfig:
        """Load configuration from file and environment variables."""
        # Start with default config
        config_dict = self._get_default_config()

        # Load from file if provided
        if config_path:
            file_config = self._load_from_file(config_path)
            config_dict = self._merge_configs(config_dict, file_config)

        # Override with environment variables
        env_config = self._load_from_env()
        config_dict = self._merge_configs(config_dict, env_config)

        # Parse and validate
        self._config = AppConfig(**config_dict)
        return self._config

    def get_config(self) -> AppConfig:
        """Get current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def load(self, config_path: Optional[str] = None) -> AppConfig:
        """Load configuration - alias for load_config."""
        return self.load_config(config_path)

    def reset_config(self) -> None:
        """Reset configuration - useful for testing."""
        self._config = None

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "server": {"host": "0.0.0.0", "port": 8000, "debug": False},
            "storage": {"type": "file", "path": "./data"},
            "auth": {"backend": "none", "apikey": None, "oidc": None},
            "ui": {"enabled": True, "path": "/ui"},
        }

    def _load_from_file(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(path, "r") as f:
                if path.suffix.lower() in [".yml", ".yaml"]:
                    return yaml.safe_load(f) or {}
                elif path.suffix.lower() == ".json":
                    return json.load(f) or {}
                else:
                    raise ValueError(f"Unsupported config file format: {path.suffix}")
        except Exception as e:
            raise ValueError(f"Failed to parse configuration file: {e}")

    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}

        # Server configuration
        server_config = {}
        if host := os.getenv(f"{self._env_prefix}SERVER_HOST"):
            server_config["host"] = host
        if port := os.getenv(f"{self._env_prefix}SERVER_PORT"):
            server_config["port"] = int(port)
        if debug := os.getenv(f"{self._env_prefix}SERVER_DEBUG"):
            server_config["debug"] = debug.lower() in ["true", "1", "yes"]
        if server_config:
            config["server"] = server_config

        # Storage configuration
        storage_config = {}
        if storage_type := os.getenv(f"{self._env_prefix}STORAGE_TYPE"):
            storage_config["type"] = storage_type
        if storage_path := os.getenv(f"{self._env_prefix}STORAGE_PATH"):
            storage_config["path"] = storage_path
        if storage_config:
            config["storage"] = storage_config

        # Authentication configuration
        auth_config = {}
        if auth_backend := os.getenv(f"{self._env_prefix}AUTH_BACKEND"):
            auth_config["backend"] = auth_backend

        # API Key configuration
        apikey_config = {}
        if apikey_keys := os.getenv(f"{self._env_prefix}AUTH_APIKEY_KEYS"):
            apikey_config["keys"] = [key.strip() for key in apikey_keys.split(",")]
        if apikey_config:
            auth_config["apikey"] = apikey_config

        # OIDC configuration
        oidc_config = {}
        if oidc_issuer := os.getenv(f"{self._env_prefix}AUTH_OIDC_ISSUER_URL"):
            oidc_config["issuer_url"] = oidc_issuer
        if oidc_client_id := os.getenv(f"{self._env_prefix}AUTH_OIDC_CLIENT_ID"):
            oidc_config["client_id"] = oidc_client_id
        if oidc_client_secret := os.getenv(
            f"{self._env_prefix}AUTH_OIDC_CLIENT_SECRET"
        ):
            oidc_config["client_secret"] = oidc_client_secret
        if oidc_jwks_cache_ttl := os.getenv(f"{self._env_prefix}AUTH_OIDC_JWKS_CACHE_TTL"):
            oidc_config["jwks_cache_ttl"] = int(oidc_jwks_cache_ttl)
        if oidc_config:
            auth_config["oidc"] = oidc_config

        if auth_config:
            config["auth"] = auth_config

        # UI configuration
        ui_config = {}
        if ui_enabled := os.getenv(f"{self._env_prefix}UI_ENABLED"):
            ui_config["enabled"] = ui_enabled.lower() in ["true", "1", "yes"]
        if ui_path := os.getenv(f"{self._env_prefix}UI_PATH"):
            ui_config["path"] = ui_path
        if ui_config:
            config["ui"] = ui_config

        # Special handling for ENABLE_NOAUTH (backwards compatibility)
        if os.getenv("ENABLE_NOAUTH", "").lower() in ["true", "1", "yes"]:
            if "auth" not in config:
                config["auth"] = {}
            config["auth"]["backend"] = "none"

        return config

    def _merge_configs(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge two configuration dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result


# Global configuration loader instance
_config_loader = ConfigLoader()


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load application configuration."""
    return _config_loader.load_config(config_path)


def get_config() -> AppConfig:
    """Get current application configuration."""
    return _config_loader.get_config()


def reset_configuration() -> None:
    """Reset configuration - useful for testing."""
    _config_loader.reset_config()
