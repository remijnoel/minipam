"""
Unit tests for the MiniPAM CLI
"""

import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from minipam.cli import cli


class TestCLI:
    """Test cases for the CLI commands"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    def test_health_command(self):
        """Test the health command"""
        with patch("minipam.cli.APIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.health_check.return_value = {
                "status": "healthy",
                "backend": "memory",
            }
            mock_client_class.return_value = mock_client

            result = self.runner.invoke(cli, ["ctl", "health"])

            assert result.exit_code == 0
            assert "API Status: healthy" in result.output
            assert "Backend: memory" in result.output

    def test_health_command_json(self):
        """Test the health command with JSON output"""
        with patch("minipam.cli.APIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.health_check.return_value = {
                "status": "healthy",
                "backend": "memory",
            }
            mock_client_class.return_value = mock_client

            result = self.runner.invoke(cli, ["ctl", "--format", "json", "health"])

            assert result.exit_code == 0
            response = json.loads(result.output)
            assert response["status"] == "healthy"
            assert response["backend"] == "memory"

    def test_list_command_empty(self):
        """Test the list command with empty results"""
        with patch("minipam.cli.APIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.list_cidrs.return_value = []
            mock_client_class.return_value = mock_client

            result = self.runner.invoke(cli, ["ctl", "cidr", "list"])

            assert result.exit_code == 0
            assert "No CIDR blocks found." in result.output

    def test_list_command_with_data(self):
        """Test the list command with data"""
        test_data = [
            {
                "cidr": "192.168.1.0/24",
                "name": "Test Network",
                "description": "Test description",
                "tags": {"env": "test"},
                "parent": None,
                "children": [],
                "created_at": "2025-07-06T04:52:51.141686",
            }
        ]

        with patch("minipam.cli.APIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.list_cidrs.return_value = test_data
            mock_client_class.return_value = mock_client

            result = self.runner.invoke(cli, ["ctl", "cidr", "list"])

            assert result.exit_code == 0
            assert "192.168.1.0/24" in result.output
            assert "Test Network" in result.output

    def test_get_command(self):
        """Test the get command"""
        test_data = {
            "cidr": "192.168.1.0/24",
            "name": "Test Network",
            "description": "Test description",
            "tags": {},
            "parent": None,
            "children": [],
            "created_at": "2025-07-06T04:52:51.141686",
        }

        with patch("minipam.cli.APIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.get_cidr.return_value = test_data
            mock_client_class.return_value = mock_client

            result = self.runner.invoke(cli, ["ctl", "cidr", "get", "192.168.1.0/24"])

            assert result.exit_code == 0
            assert "192.168.1.0/24" in result.output
            assert "Test Network" in result.output

    def test_create_command(self):
        """Test the create command"""
        test_data = {
            "cidr": "192.168.1.0/24",
            "name": "Test Network",
            "description": None,
            "tags": {},
            "parent": None,
            "children": [],
            "created_at": "2025-07-06T04:52:51.141686",
        }

        with patch("minipam.cli.APIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.create_cidr.return_value = test_data
            mock_client_class.return_value = mock_client

            result = self.runner.invoke(
                cli,
                ["ctl", "cidr", "create", "192.168.1.0/24", "--name", "Test Network"],
            )

            assert result.exit_code == 0
            assert "Created CIDR block successfully:" in result.output
            assert "192.168.1.0/24" in result.output

    def test_create_command_with_tags(self):
        """Test the create command with tags"""
        test_data = {
            "cidr": "192.168.1.0/24",
            "name": "Test Network",
            "description": None,
            "tags": {"env": "test", "owner": "admin"},
            "parent": None,
            "children": [],
            "created_at": "2025-07-06T04:52:51.141686",
        }

        with patch("minipam.cli.APIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.create_cidr.return_value = test_data
            mock_client_class.return_value = mock_client

            result = self.runner.invoke(
                cli,
                [
                    "ctl",
                    "cidr",
                    "create",
                    "192.168.1.0/24",
                    "--name",
                    "Test Network",
                    "--tag",
                    "env=test",
                    "--tag",
                    "owner=admin",
                ],
            )

            assert result.exit_code == 0
            assert "Created CIDR block successfully:" in result.output
            assert "env=test, owner=admin" in result.output

    def test_delete_command_force(self):
        """Test the delete command with force flag"""
        with patch("minipam.cli.APIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.delete_cidr.return_value = True
            mock_client_class.return_value = mock_client

            result = self.runner.invoke(
                cli, ["ctl", "cidr", "delete", "192.168.1.0/24", "--force"]
            )

            assert result.exit_code == 0
            assert "deleted successfully" in result.output

    def test_invalid_cidr_format(self):
        """Test create command with invalid CIDR format"""
        result = self.runner.invoke(cli, ["ctl", "cidr", "create", "invalid-cidr"])

        assert result.exit_code == 1  # Validation error exits with 1
        assert "Validation error:" in result.output

    def test_invalid_tag_format(self):
        """Test create command with invalid tag format"""
        result = self.runner.invoke(
            cli, ["ctl", "cidr", "create", "192.168.1.0/24", "--tag", "invalid-tag"]
        )

        assert result.exit_code == 1
        assert "Invalid tag format" in result.output

    def test_api_connection_error(self):
        """Test handling of API connection errors"""
        with patch("minipam.cli.APIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.health_check.side_effect = Exception("Connection failed")
            mock_client_class.return_value = mock_client

            result = self.runner.invoke(cli, ["ctl", "health"])

            assert result.exit_code == 1
            assert "Error:" in result.output
