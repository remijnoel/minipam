"""
CIDR Block Management Service - Main Application

A FastAPI-based service for managing CIDR blocks with pluggable storage backends.
Supports in-memory and file-based storage with concurrent access protection.
Configuration can be loaded from YAML/JSON files or environment variables.
"""

import argparse
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import router
from .config import (
    get_config,
    get_cors_config,
    get_server_config,
    get_ui_config,
    load_configuration,
)
from .debug import DEBUG_MODE, log_app_startup, request_response_logging_middleware

# Configure logging based on environment
if DEBUG_MODE:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("minipam")
    logger.setLevel(logging.DEBUG)
    logger.debug("🐞 Debug mode enabled - verbose logging active")


def create_app(config_path: Optional[str] = None) -> FastAPI:
    """Create and configure the FastAPI application"""
    # Load configuration
    if config_path:
        load_configuration(config_path)

    config = get_config()
    server_config = get_server_config()
    cors_config = get_cors_config()
    ui_config = get_ui_config()

    fastapi_app = FastAPI(
        title="CIDR Block Management Service",
        description="A service for managing CIDR blocks with pluggable storage backends",
        version="1.0.0",
        debug=config.get("debug", False),
    )

    # Log application startup information in debug mode
    if config.get("debug", False):
        # Collect configuration for logging
        log_config = {
            "HOST": server_config.get("host"),
            "PORT": server_config.get("port"),
            "LOG_LEVEL": server_config.get("log_level"),
            "DEBUG_MODE": config.get("debug"),
            "STORAGE_TYPE": config.get("storage", {}).get("type"),
            "STORAGE_FILE_PATH": config.get("storage", {}).get("file", {}).get("path"),
            "WEBUI_PATH": str(
                Path(__file__).parent.parent.parent
                / ui_config.get("path", "webui/dist")
            ),
            "PYTHON_VERSION": sys.version,
        }
        log_app_startup(log_config)

    # Add debug mode logging middleware
    if config.get("debug", False):
        app_logger = logging.getLogger("minipam")

        @fastapi_app.middleware("http")
        async def log_requests(request: Request, call_next):
            """Log all requests in debug mode"""
            path = request.url.path
            method = request.method
            app_logger.debug("→ %s %s", method, path)
            response = await call_next(request)
            app_logger.debug("← %s %s - Status %s", method, path, response.status_code)
            return response

        @fastapi_app.exception_handler(RequestValidationError)
        async def validation_exception_handler(
            request: Request, exc: RequestValidationError
        ):
            """Better error details for validation errors in debug mode"""
            app_logger.error(
                "Validation error on %s: %s", request.url.path, exc.errors()
            )
            body = await request.body()
            app_logger.error("Request body: %s", body.decode("utf-8", errors="replace"))

            # Create a safe representation of the error details
            error_details = []
            for error in exc.errors():
                # Create a copy without the ctx which might contain
                # non-serializable objects
                safe_error = {k: v for k, v in error.items() if k != "ctx"}
                # Add a string representation of the context error if it exists
                if "ctx" in error and "error" in error["ctx"]:
                    ctx_error = error["ctx"]["error"]
                    safe_error["error_msg"] = str(ctx_error)
                error_details.append(safe_error)

            return JSONResponse(
                status_code=422,
                content={
                    "detail": error_details,
                    "body": body.decode("utf-8", errors="replace"),
                },
            )

        @fastapi_app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            """Detailed error response for all exceptions in debug mode"""
            logger.error(f"Error processing {request.url.path}: {exc}")
            logger.error(traceback.format_exc())
            return JSONResponse(
                status_code=500,
                content={
                    "detail": str(exc),
                    "traceback": traceback.format_exc().split("\n"),
                    "request_path": str(request.url.path),
                    "request_method": str(request.method),
                },
            )

    # Add CORS middleware
    if cors_config.get("enabled", True):
        fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_config.get("origins", ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Add request/response logging middleware for debugging
    if config.get("debug", False):
        fastapi_app.middleware("http")(request_response_logging_middleware)

    # Add API routes
    fastapi_app.include_router(router, prefix="/api")

    # Serve static files for the UI if enabled
    if ui_config.get("enabled", True):
        ui_path = Path(__file__).parent.parent.parent / ui_config.get(
            "path", "webui/dist"
        )

        if ui_path.exists() and ui_path.is_dir():
            # Mount static files under /ui
            fastapi_app.mount(
                "/ui", StaticFiles(directory=str(ui_path), html=True), name="ui"
            )

            @fastapi_app.get("/")
            async def serve_root():
                """Serve the API info and redirect to UI"""
                return {
                    "message": "MiniPAM CIDR Management API",
                    "docs": "/docs",
                    "webui": "/ui",
                    "api": "/api",
                    "health": "/health",
                }

        else:

            @fastapi_app.get("/")
            async def no_webui():
                """Fallback when web UI is not available"""
                return {
                    "message": "MiniPAM CIDR Management API",
                    "docs": "/docs",
                    "webui": "Web UI not available. Build it with: cd webui && npm install && npm run build",
                }

    return fastapi_app


# Create the app instance
app = create_app()


def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="MiniPAM CIDR Management Service")
    parser.add_argument(
        "--config", "-c", type=str, help="Path to configuration file (YAML or JSON)"
    )
    parser.add_argument(
        "--generate-config",
        type=str,
        help="Generate an example configuration file at the specified path",
    )
    parser.add_argument(
        "--host", type=str, help="Host to bind to (overrides config file)"
    )
    parser.add_argument(
        "--port", type=int, help="Port to bind to (overrides config file)"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode (overrides config file)"
    )

    args = parser.parse_args()

    # Generate example config if requested
    if args.generate_config:
        try:
            from .config_loader import config_loader

            config_loader.save_example_config(args.generate_config)
            print(f"Example configuration saved to {args.generate_config}")
            return 0
        except (ImportError, OSError, ValueError) as e:
            print(f"Error generating config: {e}")
            return 1

    # Load configuration
    try:
        if args.config:
            load_configuration(args.config)
        else:
            # Load default configuration
            load_configuration()

        # Validate configuration
        from .config_loader import validate_config

        validate_config()

    except (ImportError, OSError, ValueError) as e:
        print(f"Configuration error: {e}")
        return 1

    # Get configuration values
    config = get_config()
    server_config = get_server_config()

    # Apply command line overrides
    host = args.host if args.host else server_config.get("host", "0.0.0.0")
    port = args.port if args.port else server_config.get("port", 8000)
    log_level = server_config.get("log_level", "info")
    debug = args.debug or config.get("debug", False)

    # Update configuration with overrides
    if args.host or args.port or args.debug:
        from .config import _config

        if _config is None:
            config_dict = config
        else:
            config_dict = _config
        if args.host:
            config_dict.setdefault("server", {})["host"] = host
        if args.port:
            config_dict.setdefault("server", {})["port"] = port
        if args.debug:
            config_dict["debug"] = debug

    # Create the app with the loaded configuration
    fastapi_app = create_app()

    # Run the server
    try:
        print(f"Starting MiniPAM server on {host}:{port}")
        if debug:
            print("Debug mode enabled")
        uvicorn.run(
            fastapi_app,
            host=host,
            port=port,
            log_level=log_level,
            reload=debug,
            access_log=debug,
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")
        return 0
    except (OSError, ValueError) as e:
        print(f"Server error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
