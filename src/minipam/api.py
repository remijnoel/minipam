"""
FastAPI application and routes for MiniPAM.
"""

import logging
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .auth import AuthenticationError, get_current_user
from .config_loader import AppConfig
from .models import (
    CIDRBlock,
    CIDRBlockCreate,
    CIDRBlockListResponse,
    CIDRBlockUpdate,
    HealthResponse,
)
from .storage import StorageBackend
from .validation import CIDRValidationEngine

logger = logging.getLogger(__name__)


class DependencyContainer:
    """Container for application dependencies."""

    def __init__(
        self,
        config: AppConfig,
        storage: StorageBackend,
        validation_engine: CIDRValidationEngine,
    ):
        self.config = config
        self.storage = storage
        self.validation_engine = validation_engine


# Global dependency container
_deps: Optional[DependencyContainer] = None


def set_dependencies(deps: DependencyContainer) -> None:
    """Set the global dependency container."""
    global _deps
    _deps = deps


def reset_dependencies() -> None:
    """Reset the global dependency container - useful for testing."""
    global _deps
    _deps = None


def get_storage() -> StorageBackend:
    """Get the storage backend."""
    if _deps is None:
        raise RuntimeError("Dependencies not initialized")
    return _deps.storage


def get_validation_engine() -> CIDRValidationEngine:
    """Get the validation engine."""
    if _deps is None:
        raise RuntimeError("Dependencies not initialized")
    return _deps.validation_engine


def get_config() -> AppConfig:
    """Get the application configuration."""
    if _deps is None:
        raise RuntimeError("Dependencies not initialized")
    return _deps.config


def create_app(
    config: AppConfig = None,
    storage: StorageBackend = None,
    validation_engine: CIDRValidationEngine = None,
) -> FastAPI:
    """Create and configure the FastAPI application."""

    # Create defaults if not provided (for testing)
    if config is None:
        from .config_loader import get_config as standalone_get_config

        config = standalone_get_config()
    if storage is None:
        from .storage import create_storage_backend

        storage = create_storage_backend(
            config.storage.type, 
            path=config.storage.path
        )
    if validation_engine is None:
        validation_engine = CIDRValidationEngine()

    # Set up dependencies
    deps = DependencyContainer(config, storage, validation_engine)
    set_dependencies(deps)

    # Create FastAPI app
    app = FastAPI(
        title="MiniPAM",
        description="Minimalistic IP Address Management",
        version="1.0.0",
        debug=config.server.debug,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Root redirect
    @app.get("/", include_in_schema=False)
    async def root():
        """Redirect root to UI or API docs."""
        if config.ui.enabled:
            return RedirectResponse(url=config.ui.path)
        return RedirectResponse(url="/docs")

    # Health endpoints
    @app.get("/api/v1/health/live", response_model=HealthResponse)
    async def health_live():
        """Liveness probe endpoint."""
        return HealthResponse(status="ok", storage={}, auth={})

    @app.get("/api/v1/health/ready", response_model=HealthResponse)
    async def health_ready(storage: StorageBackend = Depends(get_storage)):
        """Readiness probe endpoint."""
        try:
            storage_health = storage.health_check()

            return HealthResponse(
                status="ready", storage=storage_health, auth={"status": "ready"}
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=503, detail="Service unavailable")

    # CIDR endpoints
    @app.get("/api/v1/cidrs", response_model=CIDRBlockListResponse)
    async def list_cidrs(
        offset: int = Query(0, ge=0, description="Pagination offset"),
        limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
        tags: Optional[str] = Query(
            None, description="Comma-separated tags to filter by"
        ),
        storage: StorageBackend = Depends(get_storage),
        current_user: Any = Depends(get_current_user),
    ):
        """List CIDR blocks with optional filtering."""
        try:
            tag_list = [tag.strip() for tag in tags.split(",")] if tags else None
            blocks = storage.list(offset=offset, limit=limit, tags=tag_list)
            total = len(storage.list(tags=tag_list))

            return CIDRBlockListResponse(
                blocks=blocks, total=total, offset=offset, limit=limit
            )
        except Exception as e:
            logger.error(f"Error listing CIDRs: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.get("/api/v1/cidrs/tree")
    async def get_cidr_tree(
        storage: StorageBackend = Depends(get_storage),
        current_user: Any = Depends(get_current_user),
    ):
        """Get hierarchical tree view of CIDR blocks."""
        try:
            # Get all blocks
            all_blocks = storage.list()
            
            # Build tree structure
            def build_tree(parent_cidr=None):
                children = []
                for block in all_blocks:
                    if block.parent == parent_cidr:
                        node = {
                            "cidr": block.cidr,
                            "name": block.name,
                            "description": block.description,
                            "parent": block.parent,
                            "tags": block.tags,
                            "created_at": block.created_at,
                            "updated_at": block.updated_at,
                            "children": build_tree(block.cidr)
                        }
                        children.append(node)
                return children
            
            tree = build_tree()
            return tree
            
        except Exception as e:
            logger.error(f"Error getting CIDR tree: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.get("/api/v1/cidrs/{cidr_path:path}", response_model=CIDRBlock)
    async def get_cidr(
        cidr_path: str,
        storage: StorageBackend = Depends(get_storage),
        current_user: Any = Depends(get_current_user),
    ):
        """Get a specific CIDR block."""
        try:
            # URL decode the CIDR path
            import urllib.parse

            cidr = urllib.parse.unquote(cidr_path)

            block = storage.get(cidr)
            if not block:
                raise HTTPException(
                    status_code=404, detail=f"CIDR block {cidr} not found"
                )

            return block
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting CIDR {cidr_path}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.post("/api/v1/cidrs", response_model=CIDRBlock, status_code=201)
    async def create_cidr(
        cidr_data: CIDRBlockCreate,
        storage: StorageBackend = Depends(get_storage),
        validation_engine: CIDRValidationEngine = Depends(get_validation_engine),
        current_user: Any = Depends(get_current_user),
    ):
        """Create a new CIDR block."""
        try:
            # Create temporary block for validation
            temp_block = CIDRBlock(
                cidr=cidr_data.cidr,
                name=cidr_data.name,
                description=cidr_data.description,
                parent=cidr_data.parent,
                tags=cidr_data.tags,
            )

            # Validate the block
            validation_result = validation_engine.validate_create(
                temp_block, storage
            )
            if not validation_result.is_valid:
                error_messages = validation_result.errors
                # Use 409 Conflict for overlap errors, 400 for other validation errors
                status_code = 409 if any("overlap" in msg.lower() for msg in error_messages) else 400
                raise HTTPException(
                    status_code=status_code,
                    detail=f"Validation failed: {'; '.join(error_messages)}",
                )

            # Create the block
            block = CIDRBlock(**cidr_data.model_dump())
            storage.put(block)
            logger.info(f"Created CIDR block: {block.cidr}")
            return block

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating CIDR: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.put("/api/v1/cidrs/{cidr_path:path}", response_model=CIDRBlock)
    async def update_cidr(
        cidr_path: str,
        updates: CIDRBlockUpdate,
        storage: StorageBackend = Depends(get_storage),
        validation_engine: CIDRValidationEngine = Depends(get_validation_engine),
        current_user: Any = Depends(get_current_user),
    ):
        """Update a CIDR block."""
        try:
            # URL decode the CIDR path
            import urllib.parse

            cidr = urllib.parse.unquote(cidr_path)

            # Get existing block
            existing_block = storage.get(cidr)
            if not existing_block:
                raise HTTPException(
                    status_code=404, detail=f"CIDR block {cidr} not found"
                )

            # Create updated block for validation
            update_data = updates.model_dump(exclude_unset=True)
            updated_block = existing_block.model_copy(update=update_data)

            # Validate the update
            validation_result = validation_engine.validate_update(
                cidr, updated_block, storage
            )
            if not validation_result.is_valid:
                error_messages = validation_result.errors
                # Use 409 Conflict for overlap errors, 400 for other validation errors
                status_code = 409 if any("overlap" in msg.lower() for msg in error_messages) else 400
                raise HTTPException(
                    status_code=status_code,
                    detail=f"Validation failed: {'; '.join(error_messages)}",
                )

            # Update the block
            block = storage.update(cidr, updates)
            if not block:
                raise HTTPException(
                    status_code=404, detail=f"CIDR block {cidr} not found"
                )

            logger.info(f"Updated CIDR block: {block.cidr}")
            return block

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating CIDR {cidr_path}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.delete("/api/v1/cidrs/{cidr_path:path}", status_code=204)
    async def delete_cidr(
        cidr_path: str,
        storage: StorageBackend = Depends(get_storage),
        current_user: Any = Depends(get_current_user),
    ):
        """Delete a CIDR block."""
        try:
            # URL decode the CIDR path
            import urllib.parse

            cidr = urllib.parse.unquote(cidr_path)

            # Check if block exists first
            block = storage.get(cidr)
            if not block:
                raise HTTPException(
                    status_code=404, detail=f"CIDR block {cidr} not found"
                )
            
            # Check if block has children (should not delete parents with children)
            all_blocks = storage.list()
            children = [b for b in all_blocks if b.parent == cidr]
            if children:
                raise HTTPException(
                    status_code=409, 
                    detail=f"Cannot delete CIDR {cidr} because it has {len(children)} child(ren)"
                )
            
            storage.delete(cidr)

            logger.info(f"Deleted CIDR block: {cidr}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting CIDR {cidr_path}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


    # Error handlers
    @app.exception_handler(AuthenticationError)
    async def auth_exception_handler(request, exc: AuthenticationError):
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication failed", "message": str(exc)},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
            },
        )

    # UI Routes
    if config.ui.enabled:
        import os
        from pathlib import Path
        
        # Find the webui dist directory
        webui_dist = None
        current_dir = Path(__file__).parent
        
        # Look for webui/dist relative to the source directory
        for parent in [current_dir, current_dir.parent, current_dir.parent.parent]:
            potential_webui = parent / "webui" / "dist"
            if potential_webui.exists():
                webui_dist = potential_webui
                break
        
        if webui_dist and webui_dist.exists():
            # Mount static files
            app.mount("/ui", StaticFiles(directory=str(webui_dist), html=True), name="ui")
        else:
            # Fallback: basic HTML page
            @app.get("/ui/", response_class=HTMLResponse)
            async def ui_index():
                """Serve the UI index page."""
                return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>MiniPAM</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                </head>
                <body>
                    <h1>MiniPAM</h1>
                    <p>Web UI files not found. Please build the UI first.</p>
                    <p>API documentation is available at <a href="/docs">/docs</a></p>
                </body>
                </html>
                """)
            
            @app.get("/ui")
            async def ui_redirect():
                """Redirect /ui to /ui/"""
                return RedirectResponse(url="/ui/", status_code=302)

    return app
