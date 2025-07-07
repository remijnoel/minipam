"""
Unit tests for minipam.config module
"""

import os
from unittest.mock import patch

import pytest

from minipam.config import CIDR_FILE_PATH, HOST, LOG_LEVEL, PORT, USE_FILE_BACKEND


class TestConfig:
    """Test cases for configuration module"""

    def test_default_values(self):
        """Test that default configuration values are set correctly"""
        # We can't test the actual values since they might be set by environment
        # but we can test that the variables exist and are of correct type
        assert isinstance(USE_FILE_BACKEND, bool)
        assert isinstance(CIDR_FILE_PATH, str)
        assert isinstance(HOST, str)
        assert isinstance(PORT, int)
        assert isinstance(LOG_LEVEL, str)

    @patch.dict(os.environ, {"USE_FILE_BACKEND": "true"})
    def test_file_backend_enabled(self):
        """Test that file backend can be enabled via environment variable"""
        # Need to reload the module to pick up the environment change
        import importlib

        import minipam.config

        importlib.reload(minipam.config)

        assert minipam.config.USE_FILE_BACKEND is True

    @patch.dict(os.environ, {"USE_FILE_BACKEND": "false"})
    def test_file_backend_disabled(self):
        """Test that file backend can be disabled via environment variable"""
        # Need to reload the module to pick up the environment change
        import importlib

        import minipam.config

        importlib.reload(minipam.config)

        assert minipam.config.USE_FILE_BACKEND is False

    @patch.dict(os.environ, {"CIDR_FILE_PATH": "/custom/path/cidrs.json"})
    def test_custom_file_path(self):
        """Test that custom file path can be set via environment variable"""
        # Need to reload the module to pick up the environment change
        import importlib

        import minipam.config

        importlib.reload(minipam.config)

        assert minipam.config.CIDR_FILE_PATH == "/custom/path/cidrs.json"

    @patch.dict(os.environ, {"HOST": "localhost"})
    def test_custom_host(self):
        """Test that custom host can be set via environment variable"""
        # Need to reload the module to pick up the environment change
        import importlib

        import minipam.config

        importlib.reload(minipam.config)

        assert minipam.config.HOST == "localhost"

    @patch.dict(os.environ, {"PORT": "9000"})
    def test_custom_port(self):
        """Test that custom port can be set via environment variable"""
        # Need to reload the module to pick up the environment change
        import importlib

        import minipam.config

        importlib.reload(minipam.config)

        assert minipam.config.PORT == 9000

    @patch.dict(os.environ, {"LOG_LEVEL": "debug"})
    def test_custom_log_level(self):
        """Test that custom log level can be set via environment variable"""
        # Need to reload the module to pick up the environment change
        import importlib

        import minipam.config

        importlib.reload(minipam.config)

        assert minipam.config.LOG_LEVEL == "debug"
