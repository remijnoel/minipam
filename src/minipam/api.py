"""
FastAPI routes for CIDR Management Service
"""

import logging
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from .debug import DEBUG_MODE, log_api_call, log_request_details
from .models import CIDRBlock
from .rules import ValidationError, validate_cidr
from .storage import CIDRStorage, get_cidr_storage

# Setup logger for this module
logger = logging.getLogger("minipam.api")

# Create router
router = APIRouter()

# Global storage instance (singleton pattern for simplicity)
_storage_instance = None


def get_storage() -> CIDRStorage:
    """Dependency injection for storage backend"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = get_cidr_storage()
    return _storage_instance


def _sanitize_block(block: CIDRBlock) -> CIDRBlock:
    """
    Sanitize input data from UI:
    - Convert empty strings to None
    - Remove empty/null values
    """
    # Clean up empty strings in optional fields
    if hasattr(block, "parent") and block.parent == "":
        block.parent = None

    if hasattr(block, "name") and block.name == "":
        block.name = None

    if hasattr(block, "description") and block.description == "":
        block.description = None

    return block


@router.get("/cidrs/", response_model=List[CIDRBlock])
async def list_cidrs(storage: CIDRStorage = Depends(get_storage)):
    """List all CIDR blocks"""
    return await storage.list()


@router.get("/cidrs", response_model=List[CIDRBlock])
async def list_cidrs_no_slash(storage: CIDRStorage = Depends(get_storage)):
    """List all CIDR blocks (no trailing slash)"""
    return await storage.list()


@router.post("/cidrs/", response_model=CIDRBlock, status_code=status.HTTP_201_CREATED)
async def create_cidr(block: CIDRBlock, storage: CIDRStorage = Depends(get_storage)):
    """Create a new CIDR block"""
    from .debug import log_cidr_relationship

    block = _sanitize_block(block)

    try:
        # Validate the CIDR block against all rules
        await validate_cidr(block, storage)

        # Log parent-child relationship if parent is specified
        if block.parent:
            parent_block = await storage.get(block.parent)
            if parent_block:
                log_cidr_relationship(block.parent, block.cidr, "create", success=True)
            else:
                log_cidr_relationship(block.parent, block.cidr, "create", success=False)
                logger.warning(
                    "Parent CIDR %s specified for %s doesn't exist",
                    block.parent,
                    block.cidr,
                )

        await storage.put(block)
        return block

    except ValidationError as e:
        # Return a clear error message for the UI/CLI
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.post("/cidrs", response_model=CIDRBlock, status_code=status.HTTP_201_CREATED)
async def create_cidr_no_slash(
    block: CIDRBlock, storage: CIDRStorage = Depends(get_storage)
):
    """Create a new CIDR block (no trailing slash)"""
    from .debug import log_cidr_relationship

    block = _sanitize_block(block)

    try:
        # Validate the CIDR block against all rules
        await validate_cidr(block, storage)

        # Log parent-child relationship if parent is specified
        if block.parent:
            parent_block = await storage.get(block.parent)
            if parent_block:
                log_cidr_relationship(block.parent, block.cidr, "create", success=True)
            else:
                log_cidr_relationship(block.parent, block.cidr, "create", success=False)
                logger.warning(
                    "Parent CIDR %s specified for %s doesn't exist",
                    block.parent,
                    block.cidr,
                )

        await storage.put(block)
        return block

    except ValidationError as e:
        # Return a clear error message for the UI/CLI
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.put("/cidrs", status_code=status.HTTP_400_BAD_REQUEST)
async def update_cidr_missing_path_no_slash(request: Request):
    """Handle PUT requests to /cidrs without a CIDR path parameter"""
    if DEBUG_MODE:
        logger.warning("PUT request to /cidrs without CIDR path parameter")
        body = await request.body()
        log_request_details(request, body=body.decode("utf-8", errors="replace"))
        log_api_call("/cidrs", "PUT", response_code=400)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="PUT requests require a CIDR path parameter, e.g. PUT /cidrs/192.168.1.0/24",
    )


@router.put("/cidrs/", status_code=status.HTTP_400_BAD_REQUEST)
async def update_cidr_missing_path(request: Request):
    """Handle PUT requests to /cidrs/ without a CIDR path parameter"""
    if DEBUG_MODE:
        logger.warning("PUT request to /cidrs/ without CIDR path parameter")
        body = await request.body()
        log_request_details(request, body=body.decode("utf-8", errors="replace"))
        log_api_call("/cidrs/", "PUT", response_code=400)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="PUT requests require a CIDR path parameter, e.g. PUT /cidrs/192.168.1.0/24",
    )


@router.put("/cidrs/{cidr:path}", response_model=CIDRBlock)
async def update_cidr(
    request: Request,
    cidr: str,
    block: CIDRBlock,
    storage: CIDRStorage = Depends(get_storage),
):
    """Update an existing CIDR block"""
    block = _sanitize_block(block)
    # Enhanced debugging for PUT requests
    if DEBUG_MODE:
        logger.debug("PUT request received for CIDR: %s", cidr)
        log_api_call(f"/cidrs/{cidr}", "PUT", params=block.dict())
        body = await request.body()
        log_request_details(request, body=body.decode("utf-8", errors="replace"))

    # If cidr is empty, return a more helpful error
    if not cidr:
        logger.warning("Empty CIDR path parameter in PUT request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PUT requests require a CIDR path parameter, e.g. PUT /cidrs/192.168.1.0/24",
        )

    # Check if it exists
    existing = await storage.get(cidr)
    if existing is None:
        logger.warning("CIDR not found in PUT request: %s", cidr)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CIDR block '{cidr}' not found",
        )

    # Update the block (CIDR should match the path parameter)
    block.cidr = cidr

    # For updates, we need to temporarily remove the existing entry
    # so the duplicate check doesn't trigger on the item being updated
    # First, keep a copy of the existing entry
    old_block = existing

    try:
        # We need to delete the existing entry before validation to avoid
        # the duplicate check failing on the same CIDR
        await storage.delete(cidr)

        # Validate the CIDR block against all rules
        await validate_cidr(block, storage)

        # If validation passes, put the updated block
        await storage.put(block)
        if DEBUG_MODE:
            logger.debug("CIDR updated successfully: %s", cidr)
        return block

    except ValidationError as e:
        # If validation fails, restore the old block
        await storage.put(old_block)
        # Return a clear error message for the UI/CLI
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception:
        # Ensure the old block is restored on any other error
        await storage.put(old_block)
        raise


@router.get("/cidrs/{cidr:path}", response_model=CIDRBlock)
async def get_cidr(cidr: str, storage: CIDRStorage = Depends(get_storage)):
    """Retrieve a CIDR block by CIDR string"""
    block = await storage.get(cidr)
    if block is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CIDR block '{cidr}' not found",
        )
    return block


@router.delete("/cidrs/{cidr:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cidr(cidr: str, storage: CIDRStorage = Depends(get_storage)):
    """Delete a CIDR block by CIDR string"""
    block = await storage.get(cidr)
    if block is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CIDR block '{cidr}' not found",
        )
    await storage.delete(cidr)


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    from .config import USE_FILE_BACKEND

    return {"status": "healthy", "backend": "file" if USE_FILE_BACKEND else "memory"}
