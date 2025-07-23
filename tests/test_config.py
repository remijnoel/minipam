"""Test configuration management."""

import os
import tempfile
from pathlib import Path

import pytest

from src.minipam.config_loader import ConfigLoader, load_config, reset_configuration


class TestConfigLoader:
    """Test configuration loader."""

    def test_default_config(self):
        """Test loading default configuration."""
        loader = ConfigLoader()
        config = loader.load()

        assert config.server.host == "0.0.0.0"
        assert config.server.port == 8000
        assert not config.server.debug
        assert config.storage.type == "file"
        assert config.storage.path == "./data"
        assert config.auth.backend == "none"
        assert config.ui.enabled
        assert config.ui.path == "/"

    def test_yaml_config_file(self, temp_storage_dir):
        """Test loading YAML configuration file."""
        config_content = """
server:
  host: "127.0.0.1"
  port: 9000
  debug: true

storage:
  type: "memory"
  path: "/tmp/test"

auth:
  backend: "apikey"
  apikey:
    keys: ["test-key-1", "test-key-2"]

ui:
  enabled: false
  path: "/admin"
"""
        config_file = Path(temp_storage_dir) / "test.yaml"
        config_file.write_text(config_content)

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config.server.host == "127.0.0.1"
        assert config.server.port == 9000
        assert config.server.debug
        assert config.storage.type == "memory"
        assert config.storage.path == "/tmp/test"
        assert config.auth.backend == "apikey"
        assert config.auth.apikey.keys == ["test-key-1", "test-key-2"]
        assert not config.ui.enabled
        assert config.ui.path == "/admin"

    def test_json_config_file(self, temp_storage_dir):
        """Test loading JSON configuration file."""
        config_content = """{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false
  },
  "storage": {
    "type": "file",
    "path": "/var/lib/minipam"
  },
  "auth": {
    "backend": "oidc",
    "oidc": {
      "issuer_url": "https://auth.example.com",
      "client_id": "minipam-client"
    }
  }
}"""
        config_file = Path(temp_storage_dir) / "test.json"
        config_file.write_text(config_content)

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config.server.host == "0.0.0.0"
        assert config.server.port == 8080
        assert not config.server.debug
        assert config.storage.type == "file"
        assert config.storage.path == "/var/lib/minipam"
        assert config.auth.backend == "oidc"
        assert config.auth.oidc.issuer_url == "https://auth.example.com"
        assert config.auth.oidc.client_id == "minipam-client"

    def test_env_var_overrides(self):
        """Test environment variable overrides."""
        # Set environment variables
        env_vars = {
            "MINIPAM_SERVER_HOST": "192.168.1.100",
            "MINIPAM_SERVER_PORT": "9999",
            "MINIPAM_SERVER_DEBUG": "true",
            "MINIPAM_STORAGE_TYPE": "memory",
            "MINIPAM_AUTH_BACKEND": "apikey",
            "MINIPAM_AUTH_APIKEY_KEYS": "key1,key2,key3",
            "MINIPAM_UI_ENABLED": "false",
        }

        # Store original env vars
        original_env = {}
        for key in env_vars:
            original_env[key] = os.environ.get(key)
            os.environ[key] = env_vars[key]

        try:
            loader = ConfigLoader()
            config = loader.load()

            assert config.server.host == "192.168.1.100"
            assert config.server.port == 9999
            assert config.server.debug
            assert config.storage.type == "memory"
            assert config.auth.backend == "apikey"
            assert config.auth.apikey.keys == ["key1", "key2", "key3"]
            assert not config.ui.enabled

        finally:
            # Restore original env vars
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_env_var_types(self):
        """Test environment variable type conversion."""
        env_vars = {
            "MINIPAM_SERVER_PORT": "8080",  # int
            "MINIPAM_SERVER_DEBUG": "true",  # bool
            "MINIPAM_AUTH_OIDC_JWKS_CACHE_TTL": "300",  # int
            "MINIPAM_AUTH_APIKEY_KEYS": "key1,key2",  # list
        }

        original_env = {}
        for key in env_vars:
            original_env[key] = os.environ.get(key)
            os.environ[key] = env_vars[key]

        try:
            loader = ConfigLoader()
            config = loader.load()

            assert isinstance(config.server.port, int)
            assert config.server.port == 8080
            assert isinstance(config.server.debug, bool)
            assert config.server.debug is True
            assert isinstance(config.auth.oidc.jwks_cache_ttl, int)
            assert config.auth.oidc.jwks_cache_ttl == 300
            assert isinstance(config.auth.apikey.keys, list)
            assert config.auth.apikey.keys == ["key1", "key2"]

        finally:
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_config_precedence(self, temp_storage_dir):
        """Test configuration precedence (env > file > defaults)."""
        # Create config file
        config_content = """
server:
  host: "file-host"
  port: 7000
  debug: false

storage:
  type: "file"
  path: "/file/path"
"""
        config_file = Path(temp_storage_dir) / "test.yaml"
        config_file.write_text(config_content)

        # Set some env vars
        env_vars = {
            "MINIPAM_SERVER_HOST": "env-host",
            "MINIPAM_SERVER_PORT": "8000",
            # Note: debug not set in env, should come from file
        }

        original_env = {}
        for key in env_vars:
            original_env[key] = os.environ.get(key)
            os.environ[key] = env_vars[key]

        try:
            loader = ConfigLoader()
            config = loader.load(config_file)

            # Env var wins
            assert config.server.host == "env-host"
            assert config.server.port == 8000

            # File value wins over default
            assert not config.server.debug  # From file
            assert config.storage.type == "file"  # From file
            assert config.storage.path == "/file/path"  # From file

            # Default value (not in file or env)
            assert config.ui.enabled  # Default

        finally:
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_invalid_config_file(self, temp_storage_dir):
        """Test handling of invalid config files."""
        # Invalid YAML
        config_file = Path(temp_storage_dir) / "invalid.yaml"
        config_file.write_text("invalid: yaml: content [")

        loader = ConfigLoader()
        with pytest.raises(ValueError, match="Failed to parse configuration file"):
            loader.load(config_file)

    def test_missing_config_file(self):
        """Test handling of missing config files."""
        loader = ConfigLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("/nonexistent/config.yaml")

    def test_validation_errors(self):
        """Test configuration validation."""
        # Invalid storage type
        os.environ["MINIPAM_STORAGE_TYPE"] = "invalid-type"

        try:
            loader = ConfigLoader()
            with pytest.raises(ValueError, match="Storage type must be"):
                loader.load()
        finally:
            os.environ.pop("MINIPAM_STORAGE_TYPE", None)

        # Invalid auth backend
        os.environ["MINIPAM_AUTH_BACKEND"] = "invalid-backend"

        try:
            loader = ConfigLoader()
            with pytest.raises(ValueError, match="Auth backend must be"):
                loader.load()
        finally:
            os.environ.pop("MINIPAM_AUTH_BACKEND", None)


class TestConfigModule:
    """Test module-level config functions."""

    def test_load_config_function(self):
        """Test load_config function."""
        config = load_config()
        assert config.server.host == "0.0.0.0"

        # Should be able to get config after loading
        from src.minipam.config_loader import get_config

        config2 = get_config()
        assert config2.server.host == config.server.host

    def test_reset_configuration(self):
        """Test reset_configuration function."""
        # Load config
        config1 = load_config()

        # Reset and load again
        reset_configuration()
        config2 = load_config()

        # Should be equivalent but different instances
        assert config1.server.host == config2.server.host
        assert config1 is not config2
