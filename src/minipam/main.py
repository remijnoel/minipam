"""
Main entry point for MiniPAM application.
"""

import logging

from fastapi import FastAPI

from .api import create_app
from .config_loader import get_config
from .storage import create_storage_backend
from .validation import CIDRValidationEngine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_minipam_app() -> FastAPI:
    """Create and configure the MiniPAM FastAPI application."""
    # Load configuration
    config = get_config()

    # Create storage backend
    storage = create_storage_backend(config.storage.type, path=config.storage.path)

    # Create validation engine
    validation_engine = CIDRValidationEngine()

    # Create FastAPI app
    app = create_app(config, storage, validation_engine)

    return app


if __name__ == "__main__":
    import uvicorn

    config = get_config()

    uvicorn.run(
        "src.minipam.main:create_minipam_app",
        factory=True,
        host=config.server.host,
        port=config.server.port,
        reload=config.server.debug,
        log_level="debug" if config.server.debug else "info",
    )
