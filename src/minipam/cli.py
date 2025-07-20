"""
Command-line interface for MiniPAM.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import click

from .config_loader import get_config, load_config
from .main import create_minipam_app
from .storage import create_storage_backend
from .validation import CIDRValidationEngine

logger = logging.getLogger(__name__)


@click.group()
@click.option(
    "--config", "-c", type=click.Path(exists=True), help="Configuration file path"
)
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.pass_context
def cli(ctx, config: Optional[str], debug: bool):
    """MiniPAM - Minimalistic IP Address Management."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["debug"] = debug

    # Set up logging
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level)


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
@click.pass_context
def serve(ctx, host: str, port: int, reload: bool):
    """Start the MiniPAM server."""
    config_path = ctx.obj.get("config_path")

    # Load configuration
    if config_path:
        config = load_config(config_path)
    else:
        config = get_config()

    # Override with CLI options
    if host != "127.0.0.1":
        config.server.host = host
    if port != 8000:
        config.server.port = port
    if ctx.obj.get("debug"):
        config.server.debug = True

    # Create app
    app = create_minipam_app()

    # Start server
    import uvicorn

    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
        reload=reload or config.server.debug,
        log_level="debug" if config.server.debug else "info",
    )


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize MiniPAM configuration."""
    config_path = ctx.obj.get("config_path", "config.yaml")

    if Path(config_path).exists():
        click.echo(f"Configuration file {config_path} already exists")
        return

    # Create default configuration
    default_config = """
server:
  host: "127.0.0.1"
  port: 8000
  debug: false

storage:
  type: "file"
  path: "./data"

auth:
  backend: "none"

ui:
  enabled: true
  path: "/ui"
"""

    with open(config_path, "w") as f:
        f.write(default_config.strip())

    click.echo(f"Created configuration file: {config_path}")


@cli.command()
@click.pass_context
def config_show(ctx):
    """Show current configuration."""
    config_path = ctx.obj.get("config_path")

    if config_path:
        config = load_config(config_path)
    else:
        config = get_config()

    click.echo("Current configuration:")
    click.echo(f"  Server: {config.server.host}:{config.server.port}")
    click.echo(f"  Debug: {config.server.debug}")
    click.echo(f"  Storage: {config.storage.type}")
    if config.storage.path:
        click.echo(f"  Storage path: {config.storage.path}")
    click.echo(f"  Auth: {config.auth.backend}")
    click.echo(f"  UI enabled: {config.ui.enabled}")


@cli.command()
@click.argument("cidr")
@click.argument("name")
@click.option("--description", help="CIDR description")
@click.option("--parent", help="Parent CIDR")
@click.option("--tags", help="Comma-separated tags")
@click.pass_context
def add(
    ctx,
    cidr: str,
    name: str,
    description: Optional[str],
    parent: Optional[str],
    tags: Optional[str],
):
    """Add a new CIDR block."""
    config_path = ctx.obj.get("config_path")

    async def _add():
        # Load configuration and create storage
        if config_path:
            config = load_config(config_path)
        else:
            config = get_config()

        storage = create_storage_backend(config.storage.type, path=config.storage.path)

        validation_engine = CIDRValidationEngine()

        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []

        # Create CIDR block data
        from .models import CIDRBlock, CIDRBlockCreate

        cidr_data = CIDRBlockCreate(
            cidr=cidr, name=name, description=description, parent=parent, tags=tag_list
        )

        # Validate
        temp_block = CIDRBlock(
            cidr=cidr_data.cidr,
            name=cidr_data.name,
            description=cidr_data.description,
            parent=cidr_data.parent,
            tags=cidr_data.tags,
        )

        result = await validation_engine.validate_create(temp_block, storage)
        if not result.is_valid:
            click.echo("Validation failed:")
            for error in result.errors:
                click.echo(f"  {error}")
            return

        # Create the block
        block = CIDRBlock(**cidr_data.model_dump())
        storage.put(block)
        click.echo(f"Created CIDR block: {block.cidr} ({block.name})")

    asyncio.run(_add())


@cli.command()
@click.option("--tags", help="Filter by comma-separated tags")
@click.pass_context
def list(ctx, tags: Optional[str]):
    """List CIDR blocks."""
    config_path = ctx.obj.get("config_path")

    async def _list():
        # Load configuration and create storage
        if config_path:
            config = load_config(config_path)
        else:
            config = get_config()

        storage = create_storage_backend(config.storage.type, path=config.storage.path)

        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else None

        # Get blocks
        blocks = await storage.list(tags=tag_list)

        if not blocks:
            click.echo("No CIDR blocks found")
            return

        # Display blocks
        from tabulate import tabulate

        headers = ["CIDR", "Name", "Parent", "Tags", "Created"]
        rows = []

        for block in blocks:
            rows.append(
                [
                    block.cidr,
                    block.name,
                    block.parent or "-",
                    ", ".join(block.tags) if block.tags else "-",
                    block.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )

        click.echo(tabulate(rows, headers=headers, tablefmt="grid"))

    asyncio.run(_list())


def main():
    """Entry point for console scripts."""
    cli()


if __name__ == "__main__":
    cli()
