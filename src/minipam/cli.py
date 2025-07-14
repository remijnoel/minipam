"""
CLI interface for MiniPAM CIDR Management Service

Provides command-line interface to interact with the MiniPAM API.
"""

import json
import logging
import sys

import click
import httpx
from pydantic import ValidationError

from .debug import DEBUG_MODE, enable_cli_debug_mode
from .models import CIDRBlock

# Setup logger
logger = logging.getLogger("minipam.cli")

# Enable debug mode if environment variable is set
if DEBUG_MODE:
    enable_cli_debug_mode()


class APIClient:
    """Client for interacting with the MiniPAM API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        client_kwargs = {"base_url": self.base_url, "follow_redirects": True}

        # Add extra debugging options in debug mode
        if DEBUG_MODE:
            client_kwargs.update(
                {
                    "event_hooks": {
                        "request": [self._log_request],
                        "response": [self._log_response],
                    },
                    "timeout": 30.0,  # Longer timeout in debug mode
                }
            )

        self.client = httpx.Client(**client_kwargs)

        if DEBUG_MODE:
            logger.debug(f"Initialized API client with base URL: {self.base_url}")

    def _log_request(self, request):
        """Log HTTP request details in debug mode"""
        if not DEBUG_MODE:
            return

        logger.debug(f"API Request: {request.method} {request.url}")
        if hasattr(request, "content") and request.content:
            try:
                body = request.content.decode("utf-8")
                if body:
                    try:
                        json_body = json.loads(body)
                        logger.debug(
                            f"Request body (JSON): {json.dumps(json_body, indent=2)}"
                        )
                    except json.JSONDecodeError:
                        logger.debug(f"Request body: {body}")
            except UnicodeDecodeError:
                logger.debug(
                    f"Request body: <binary data of length {len(request.content)}>"
                )

    def _log_response(self, response):
        """Log HTTP response details in debug mode"""
        if not DEBUG_MODE:
            return

        logger.debug(
            f"API Response: {response.status_code} from {response.request.method} {response.url}"
        )
        logger.debug(f"Response headers: {dict(response.headers)}")

        try:
            body = response.text
            if body:
                try:
                    json_body = json.loads(body)
                    logger.debug(
                        f"Response body (JSON): {json.dumps(json_body, indent=2)}"
                    )
                except json.JSONDecodeError:
                    if len(body) > 500:
                        logger.debug(f"Response body (truncated): {body[:500]}...")
                    else:
                        logger.debug(f"Response body: {body}")
        except Exception as e:
            logger.debug(f"Error parsing response body: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        if DEBUG_MODE and exc_val:
            logger.exception("API client error:", exc_info=(exc_type, exc_val, exc_tb))

    def health_check(self) -> dict:
        """Check API health"""
        if DEBUG_MODE:
            logger.debug("Performing API health check")

        response = self.client.get("/health")
        response.raise_for_status()
        return response.json()

    def list_cidrs(self) -> list:
        """List all CIDR blocks"""
        if DEBUG_MODE:
            logger.debug("Listing all CIDR blocks")

        response = self.client.get("/cidrs")
        response.raise_for_status()
        return response.json()

    def get_cidr(self, cidr_id: str) -> dict:
        """Get a specific CIDR block"""
        if DEBUG_MODE:
            logger.debug(f"Getting CIDR block: {cidr_id}")

        response = self.client.get(f"/cidrs/{cidr_id}")
        response.raise_for_status()
        return response.json()

    def create_cidr(self, cidr_data: dict) -> dict:
        """Create a new CIDR block"""
        if DEBUG_MODE:
            logger.debug(f"Creating CIDR block: {json.dumps(cidr_data, indent=2)}")

        response = self.client.post("/cidrs", json=cidr_data)
        response.raise_for_status()
        return response.json()

    def update_cidr(self, cidr_id: str, cidr_data: dict) -> dict:
        """Update an existing CIDR block"""
        # First get the existing CIDR block
        existing = self.get_cidr(cidr_id)

        # Merge with update data
        updated_data = {**existing, **cidr_data}

        # Use POST endpoint for update (same as create)
        response = self.client.post("/cidrs", json=updated_data)
        response.raise_for_status()
        return response.json()

    def delete_cidr(self, cidr_id: str) -> bool:
        """Delete a CIDR block"""
        response = self.client.delete(f"/cidrs/{cidr_id}")
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True


def format_cidr_output(cidr_data, format_type: str = "table") -> str:
    """Format CIDR data for output"""
    if format_type == "json":
        return json.dumps(cidr_data, indent=2)

    # Table format
    if isinstance(cidr_data, list):
        if not cidr_data:
            return "No CIDR blocks found."

        output = []
        output.append("CIDR Blocks:")
        output.append("-" * 80)
        for cidr_block in cidr_data:
            output.append(f"CIDR: {cidr_block['cidr']}")
            if cidr_block.get("name"):
                output.append(f"  Name: {cidr_block['name']}")
            if cidr_block.get("description"):
                output.append(f"  Description: {cidr_block['description']}")
            if cidr_block.get("tags"):
                output.append(
                    f"  Tags: {', '.join(f'{k}={v}' for k, v in cidr_block['tags'].items())}"
                )
            if cidr_block.get("parent"):
                output.append(f"  Parent: {cidr_block['parent']}")
            if cidr_block.get("children"):
                output.append(f"  Children: {', '.join(cidr_block['children'])}")
            output.append(f"  Created: {cidr_block['created_at']}")
            output.append("")
        return "\n".join(output)

    # Single CIDR block (dict)
    output = []
    output.append(f"CIDR: {cidr_data['cidr']}")
    if cidr_data.get("name"):
        output.append(f"Name: {cidr_data['name']}")
    if cidr_data.get("description"):
        output.append(f"Description: {cidr_data['description']}")
    if cidr_data.get("tags"):
        output.append(
            f"Tags: {', '.join(f'{k}={v}' for k, v in cidr_data['tags'].items())}"
        )
    if cidr_data.get("parent"):
        output.append(f"Parent: {cidr_data['parent']}")
    if cidr_data.get("children"):
        output.append(f"Children: {', '.join(cidr_data['children'])}")
    output.append(f"Created: {cidr_data['created_at']}")

    return "\n".join(output)


@click.group()
@click.pass_context
def cli(ctx):
    """MiniPAM CLI - CIDR Block Management Tool"""
    ctx.ensure_object(dict)


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind the server to")
@click.option("--port", default=8000, type=int, help="Port to bind the server to")
@click.option("--config", "-c", help="Path to configuration file (YAML or JSON)")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["debug", "info", "warning", "error", "critical"]),
    help="Logging level",
)
def run(host, port, config, reload, log_level):
    """Start the MiniPAM API server"""
    try:
        import uvicorn

        from .main import app

        click.echo(f"Starting MiniPAM server on {host}:{port}")
        if config:
            click.echo(f"Using configuration file: {config}")
        click.echo(f"API documentation available at http://{host}:{port}/docs")

        # Set environment variables for the app configuration
        import os

        os.environ["HOST"] = host
        os.environ["PORT"] = str(port)
        os.environ["LOG_LEVEL"] = log_level
        
        # Set config file if provided
        if config:
            os.environ["MINIPAM_CONFIG_FILE"] = config

        uvicorn.run(app, host=host, port=port, reload=reload, log_level=log_level)
    except KeyboardInterrupt:
        click.echo("\nShutting down server...")
    except Exception as e:
        click.echo(f"Error starting server: {e}", err=True)
        sys.exit(1)


@cli.group()
@click.option(
    "--api-url", default="http://localhost:8000", help="Base URL of the MiniPAM API"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def ctl(ctx, api_url, output_format):
    """Control and manage MiniPAM resources"""
    ctx.obj["api_url"] = api_url
    ctx.obj["format"] = output_format


@ctl.command()
@click.pass_context
def health(ctx):
    """Check API health status"""
    try:
        with APIClient(ctx.obj["api_url"]) as client:
            health_data = client.health_check()
            if ctx.obj["format"] == "json":
                click.echo(json.dumps(health_data, indent=2))
            else:
                click.echo(f"API Status: {health_data['status']}")
                if "backend" in health_data:
                    click.echo(f"Backend: {health_data['backend']}")
                if "version" in health_data:
                    click.echo(f"Version: {health_data['version']}")
    except httpx.RequestError as e:
        click.echo(f"Error connecting to API: {e}", err=True)
        sys.exit(1)
    except (KeyError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@ctl.group()
@click.pass_context
def cidr(ctx):
    """Manage CIDR blocks"""
    pass


@cidr.command(name="list")
@click.pass_context
def list_cidrs(ctx):
    """List all CIDR blocks"""
    try:
        with APIClient(ctx.parent.obj["api_url"]) as client:
            cidrs = client.list_cidrs()
            output = format_cidr_output(cidrs, ctx.parent.obj["format"])
            click.echo(output)
    except httpx.RequestError as e:
        click.echo(f"Error connecting to API: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cidr.command()
@click.argument("cidr_id")
@click.pass_context
def get(ctx, cidr_id):
    """Get details of a specific CIDR block"""
    try:
        with APIClient(ctx.parent.obj["api_url"]) as client:
            cidr_data = client.get_cidr(cidr_id)
            output = format_cidr_output(cidr_data, ctx.parent.obj["format"])
            click.echo(output)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            click.echo(f"CIDR block '{cidr_id}' not found", err=True)
        else:
            click.echo(f"API error: {e}", err=True)
        sys.exit(1)
    except httpx.RequestError as e:
        click.echo(f"Error connecting to API: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cidr.command()
@click.argument("cidr_id")
@click.option("--name", help="Name for the CIDR block")
@click.option("--description", help="Description for the CIDR block")
@click.option(
    "--tag", multiple=True, help="Tags in key=value format (can be used multiple times)"
)
@click.option("--parent", help="Parent CIDR block")
@click.option(
    "--child",
    "children",
    multiple=True,
    help="Child CIDR blocks (can be used multiple times)",
)
@click.pass_context
def create(ctx, cidr_id, name, description, tag, parent, children):
    """Create a new CIDR block"""
    try:
        # Parse tags
        tags = {}
        for tag_str in tag:
            if "=" not in tag_str:
                click.echo(
                    f"Invalid tag format: {tag_str}. Use key=value format.", err=True
                )
                sys.exit(1)
            key, value = tag_str.split("=", 1)
            tags[key] = value

        # Build CIDR data
        cidr_data = {
            "cidr": cidr_id,
            "name": name,
            "description": description,
            "tags": tags,
            "parent": parent,
            "children": list(children) if children else [],
        }

        # Remove None values
        cidr_data = {k: v for k, v in cidr_data.items() if v is not None}

        # Validate using Pydantic model
        try:
            CIDRBlock(**cidr_data)
        except ValidationError as e:
            click.echo(f"Validation error: {e}", err=True)
            sys.exit(1)

        with APIClient(ctx.parent.obj["api_url"]) as client:
            result = client.create_cidr(cidr_data)
            output = format_cidr_output(result, ctx.parent.obj["format"])
            click.echo("Created CIDR block successfully:")
            click.echo(output)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            click.echo(f"Validation error: {e.response.json()}", err=True)
        else:
            click.echo(f"API error: {e}", err=True)
        sys.exit(1)
    except httpx.RequestError as e:
        click.echo(f"Error connecting to API: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cidr.command()
@click.argument("cidr_id")
@click.option("--name", help="Name for the CIDR block")
@click.option("--description", help="Description for the CIDR block")
@click.option(
    "--tag", multiple=True, help="Tags in key=value format (can be used multiple times)"
)
@click.option("--parent", help="Parent CIDR block")
@click.option(
    "--child",
    "children",
    multiple=True,
    help="Child CIDR blocks (can be used multiple times)",
)
@click.pass_context
def update(ctx, cidr_id, name, description, tag, parent, children):
    """Update an existing CIDR block"""
    try:
        # Parse tags
        tags = {}
        for tag_str in tag:
            if "=" not in tag_str:
                click.echo(
                    f"Invalid tag format: {tag_str}. Use key=value format.", err=True
                )
                sys.exit(1)
            key, value = tag_str.split("=", 1)
            tags[key] = value

        # Build update data (only include specified fields)
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if tag:
            update_data["tags"] = tags
        if parent is not None:
            update_data["parent"] = parent
        if children:
            update_data["children"] = list(children)

        if not update_data:
            click.echo(
                "No fields specified for update. Use --help for options.", err=True
            )
            sys.exit(1)

        with APIClient(ctx.parent.obj["api_url"]) as client:
            result = client.update_cidr(cidr_id, update_data)
            output = format_cidr_output(result, ctx.parent.obj["format"])
            click.echo("Updated CIDR block successfully:")
            click.echo(output)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            click.echo(f"CIDR block '{cidr_id}' not found", err=True)
        elif e.response.status_code == 422:
            click.echo(f"Validation error: {e.response.json()}", err=True)
        else:
            click.echo(f"API error: {e}", err=True)
        sys.exit(1)
    except httpx.RequestError as e:
        click.echo(f"Error connecting to API: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cidr.command()
@click.argument("cidr_id")
@click.option("--force", is_flag=True, help="Force deletion without confirmation")
@click.pass_context
def delete(ctx, cidr_id, force):
    """Delete a CIDR block"""
    try:
        if not force:
            if not click.confirm(
                f"Are you sure you want to delete CIDR block '{cidr_id}'?"
            ):
                click.echo("Deletion cancelled.")
                return

        with APIClient(ctx.parent.obj["api_url"]) as client:
            success = client.delete_cidr(cidr_id)
            if success:
                click.echo(f"CIDR block '{cidr_id}' deleted successfully.")
            else:
                click.echo(f"CIDR block '{cidr_id}' not found.", err=True)
                sys.exit(1)

    except httpx.RequestError as e:
        click.echo(f"Error connecting to API: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
