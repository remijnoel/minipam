"""
Debug utilities for MiniPAM

This module provides debugging tools and utilities to help with development
and troubleshooting of the MiniPAM application.
"""

import inspect
import json
import logging
import os
import sys
import time
import traceback
from typing import Any, Dict, Optional

from fastapi import Request, Response

# Configure debug mode based on environment variable
DEBUG_MODE = os.environ.get("MINIPAM_DEBUG", "0") == "1"

# Setup logger
logger = logging.getLogger("minipam.debug")
if DEBUG_MODE:
    logger.setLevel(logging.DEBUG)

    # Add console handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
else:
    logger.setLevel(logging.INFO)


def debug_context() -> Dict[str, Any]:
    """Get debug context information from the current call stack"""
    if not DEBUG_MODE:
        return {}

    # Get the caller's frame
    stack = inspect.stack()
    frame = stack[2] if len(stack) > 2 else stack[1]

    return {
        "file": os.path.basename(frame.filename),
        "line": frame.lineno,
        "function": frame.function,
        "code": frame.code_context[0].strip() if frame.code_context else None,
    }


def log_api_call(
    path: str,
    method: str,
    params: Optional[Dict[str, Any]] = None,
    response_code: Optional[int] = None,
    error: Optional[Exception] = None,
):
    """Log details about an API call"""
    if not DEBUG_MODE:
        return

    ctx = debug_context()
    message = f"{method} {path}"

    if params:
        try:
            params_str = json.dumps(params, default=str)
            message += f" - Params: {params_str}"
        except Exception:
            message += f" - Params: {params}"

    if response_code:
        message += f" - Status: {response_code}"

    if error:
        logger.error("API Error: %s", message, exc_info=error)
        logger.error("Traceback: %s", traceback.format_exc())
    else:
        logger.debug("API Call: %s", message)
        logger.debug("Context: %s", json.dumps(ctx, default=str))


def log_request_details(request, body: Optional[str] = None):
    """Log details about a FastAPI request"""
    if not DEBUG_MODE:
        return

    logger.debug("Request Headers: %s", dict(request.headers))
    logger.debug("Request Query Params: %s", dict(request.query_params))

    if body:
        try:
            body_json = json.loads(body)
            logger.debug("Request Body: %s", json.dumps(body_json, indent=2))
        except Exception:
            logger.debug("Request Body (raw): %s", body)


async def log_full_request(request: Request) -> None:
    """Log full request details including body - to be used in middleware"""
    if not DEBUG_MODE:
        return

    logger.debug("=== REQUEST: %s %s ===", request.method, request.url.path)
    if request.client:
        logger.debug("Client: %s:%s", request.client.host, request.client.port)
    else:
        logger.debug("Client: unknown")
    logger.debug("Headers: %s", dict(request.headers))

    # Log query parameters
    query_params = dict(request.query_params)
    if query_params:
        logger.debug("Query Parameters: %s", query_params)

    # Log request body
    body = await request.body()
    if body:
        try:
            body_text = body.decode("utf-8")
            try:
                # Try to parse as JSON for prettier output
                body_json = json.loads(body_text)
                logger.debug("Body (JSON): %s", json.dumps(body_json, indent=2))
            except json.JSONDecodeError:
                logger.debug("Body (raw): %s", body_text)
        except UnicodeDecodeError:
            logger.debug("Body: <binary data of length %d>", len(body))

    # Save body in request state for potential reuse
    request.state.body = body

    logger.debug("=== END REQUEST ===")


def log_response(response: Response, processing_time: Optional[float] = None) -> None:
    """Log response details"""
    if not DEBUG_MODE:
        return

    logger.debug("=== RESPONSE: Status %d ===", response.status_code)

    # Log headers
    logger.debug("Headers: %s", dict(response.headers))

    # Log body if it's a JSON response
    media_type = response.headers.get("content-type", "")
    if hasattr(response, "body") and "application/json" in media_type:
        try:
            # Access raw body content
            if hasattr(response, "body"):
                if isinstance(response.body, bytes):
                    body_text = response.body.decode("utf-8")
                    try:
                        body_json = json.loads(body_text)
                        logger.debug("Body (JSON): %s", json.dumps(body_json, indent=2))
                    except json.JSONDecodeError:
                        logger.debug("Body (raw): %s", body_text)
                else:
                    logger.debug("Body: <non-bytes data>")
        except (UnicodeDecodeError, AttributeError) as ex:
            logger.debug("Error reading response body: %s", str(ex))

    if processing_time is not None:
        logger.debug("Processing Time: %.6f seconds", processing_time)

    logger.debug("=== END RESPONSE ===")


async def request_response_logging_middleware(request: Request, call_next):
    """Middleware to log requests and responses with timing information"""

    # Log the request
    await log_full_request(request)

    # Process the request and time it
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log the response
        log_response(response, process_time)

        return response
    except Exception:
        process_time = time.time() - start_time
        logger.error("Request failed after %.6f seconds", process_time)
        logger.exception("Unhandled exception in request processing:")
        raise


def log_storage_operation(
    operation: str, cidr_id: str, data: Optional[Any] = None, success: bool = True
) -> None:
    """
    Log details about storage operations (create, read, update, delete)

    Args:
        operation: The operation being performed (get, put, delete, list)
        cidr_id: The CIDR block identifier being operated on
        data: Optional data being stored/retrieved (can be dict, list, etc.)
        success: Whether the operation was successful
    """
    if not DEBUG_MODE:
        return

    ctx = debug_context()

    log_message = f"Storage {operation}: {cidr_id}"
    if not success:
        log_message += " (FAILED)"

    if operation == "put":
        logger.debug("%s - Context: %s", log_message, json.dumps(ctx, default=str))
        if data:
            try:
                logger.debug(
                    "Storage data: %s", json.dumps(data, default=str, indent=2)
                )
            except Exception:
                logger.debug("Storage data: %s", data)
    elif operation == "get":
        logger.debug("%s - Context: %s", log_message, json.dumps(ctx, default=str))
        if success and data:
            logger.debug("Retrieved data: %s", json.dumps(data, default=str, indent=2))
    elif operation == "delete":
        logger.debug("%s - Context: %s", log_message, json.dumps(ctx, default=str))
    elif operation == "list":
        logger.debug("%s - Context: %s", log_message, json.dumps(ctx, default=str))
        if success and data:
            logger.debug("Listed %d items", len(data))
            if DEBUG_MODE and len(data) > 0:
                logger.debug(
                    "First item sample: %s",
                    json.dumps(
                        data[0] if isinstance(data, list) else next(iter(data)),
                        default=str,
                        indent=2,
                    ),
                )


def log_app_startup(config: Dict[str, Any]) -> None:
    """
    Log application startup information and configuration

    Args:
        config: Configuration dictionary with app settings
    """
    if not DEBUG_MODE:
        logger.info("MiniPAM starting up (standard logging mode)")
        return

    logger.debug("=" * 80)
    logger.debug("🚀 MiniPAM Application Starting (DEBUG MODE)")
    logger.debug("=" * 80)
    logger.debug("Configuration:")
    for key, value in config.items():
        logger.debug("  %s: %s", key, value)

    logger.debug("Python version: %s", sys.version)
    logger.debug("Current directory: %s", os.getcwd())
    logger.debug("Environment variables:")

    # Log relevant environment variables (omitting secrets)
    env_vars = {
        key: value
        for key, value in os.environ.items()
        if key.startswith(("MINIPAM_", "PYTHONPATH", "HOST", "PORT", "LOG", "DEBUG"))
        and "PASSWORD" not in key
        and "SECRET" not in key
        and "TOKEN" not in key
    }

    for key, value in env_vars.items():
        logger.debug("  %s: %s", key, value)

    logger.debug("=" * 80)


def enable_cli_debug_mode() -> None:
    """
    Enable debug mode for CLI operations

    This function configures logging for CLI commands when in debug mode.
    It should be called at the beginning of CLI command execution.
    """
    if DEBUG_MODE:
        # Configure root logger for CLI debugging
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # Create a formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)

        # Add handlers if they don't exist
        if not root_logger.handlers:
            root_logger.addHandler(console_handler)

        logger.debug("🔍 CLI Debug Mode Activated")

        # Log the command being executed
        if len(sys.argv) > 1:
            command = " ".join(sys.argv)
            logger.debug("Executing CLI command: %s", command)


def log_cidr_relationship(
    parent_cidr: str, child_cidr: str, operation: str, success: bool = True
) -> None:
    """
    Log CIDR parent-child relationship operations

    Args:
        parent_cidr: The parent CIDR block
        child_cidr: The child CIDR block
        operation: The operation being performed (create, update, delete)
        success: Whether the operation was successful
    """
    if not DEBUG_MODE:
        return

    ctx = debug_context()

    log_message = f"CIDR Relationship {operation}: {child_cidr} → {parent_cidr}"
    if not success:
        log_message += " (FAILED)"

    logger.debug(log_message)

    # Check if child is a subnet of parent
    try:
        import ipaddress

        parent_net = ipaddress.ip_network(parent_cidr, strict=False)
        child_net = ipaddress.ip_network(child_cidr, strict=False)

        # Check if they're the same IP version
        if parent_net.version == child_net.version:
            # Use subnet_of for checking
            is_subnet = False

            # For IPv4
            if parent_net.version == 4:
                parent_ipv4 = ipaddress.IPv4Network(parent_cidr, strict=False)
                child_ipv4 = ipaddress.IPv4Network(child_cidr, strict=False)
                is_subnet = child_ipv4.subnet_of(parent_ipv4)
            # For IPv6
            else:
                parent_ipv6 = ipaddress.IPv6Network(parent_cidr, strict=False)
                child_ipv6 = ipaddress.IPv6Network(child_cidr, strict=False)
                is_subnet = child_ipv6.subnet_of(parent_ipv6)

            if not is_subnet:
                logger.warning(
                    "⚠️ Child CIDR %s is not a subnet of parent %s",
                    child_cidr,
                    parent_cidr,
                )
            else:
                logger.debug(
                    "✓ Child CIDR %s is a valid subnet of parent %s",
                    child_cidr,
                    parent_cidr,
                )
        else:
            logger.warning(
                "⚠️ CIDR version mismatch: Parent %s (IPv%s) vs Child %s (IPv%s)",
                parent_cidr,
                parent_net.version,
                child_cidr,
                child_net.version,
            )
    except (ValueError, TypeError) as e:
        logger.warning("Error validating CIDR relationship: %s", str(e))

    logger.debug("Context: %s", json.dumps(ctx, default=str))
