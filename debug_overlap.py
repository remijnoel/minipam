#!/usr/bin/env python3

"""Debug script to understand the overlap validation logic."""

from minipam.models import CIDRBlock
from minipam.validation import CIDRValidationEngine
from unittest.mock import Mock

def test_parent_child_overlap():
    """Test what happens when we have a valid parent-child relationship."""
    engine = CIDRValidationEngine()
    
    # Create a parent block
    parent_block = CIDRBlock(
        cidr="10.0.0.0/24", 
        name="Parent Network", 
        parent=None, 
        tags=[]
    )
    
    # Create a child block that should be valid
    child_block = CIDRBlock(
        cidr="10.0.0.0/25",  # Subnet of parent
        name="Child Network", 
        parent="10.0.0.0/24",  # Correctly declares parent
        tags=[]
    )
    
    # Mock storage
    mock_storage = Mock()
    mock_storage.get.side_effect = lambda cidr: (
        parent_block if cidr == "10.0.0.0/24" else None
    )
    mock_storage.list.return_value = [parent_block]
    
    print("Testing valid parent-child relationship:")
    print(f"Parent: {parent_block.cidr}")
    print(f"Child: {child_block.cidr} (declares parent: {child_block.parent})")
    
    result = engine.validate(child_block, mock_storage)
    print(f"Validation result: {result.is_valid}")
    if not result.is_valid:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
    print()

def test_invalid_overlap():
    """Test what happens when we have an invalid overlap (no parent declared)."""
    engine = CIDRValidationEngine()
    
    # Create an existing block
    existing_block = CIDRBlock(
        cidr="10.0.0.0/24", 
        name="Existing Network", 
        parent=None, 
        tags=[]
    )
    
    # Create a new block that overlaps but doesn't declare parent
    new_block = CIDRBlock(
        cidr="10.0.0.0/25",  # Subnet of existing
        name="New Network", 
        parent=None,  # WRONG: should declare existing as parent
        tags=[]
    )
    
    # Mock storage
    mock_storage = Mock()
    mock_storage.get.return_value = None  # No existing block with this exact CIDR
    mock_storage.list.return_value = [existing_block]
    
    print("Testing invalid overlap (no parent declared):")
    print(f"Existing: {existing_block.cidr}")
    print(f"New: {new_block.cidr} (declares parent: {new_block.parent})")
    
    result = engine.validate(new_block, mock_storage)
    print(f"Validation result: {result.is_valid}")
    if not result.is_valid:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
    print()

def test_reverse_case():
    """Test when we try to add a parent that contains an existing child."""
    engine = CIDRValidationEngine()
    
    # Create an existing child block
    existing_child = CIDRBlock(
        cidr="10.0.0.0/25", 
        name="Existing Child", 
        parent=None,  # Initially no parent
        tags=[]
    )
    
    # Create a new parent block that would contain the existing child
    new_parent = CIDRBlock(
        cidr="10.0.0.0/24",  # Contains existing child
        name="New Parent", 
        parent=None,
        tags=[]
    )
    
    # Mock storage
    mock_storage = Mock()
    mock_storage.get.return_value = None  # No existing block with this exact CIDR
    mock_storage.list.return_value = [existing_child]
    
    print("Testing reverse case (adding parent that contains existing child):")
    print(f"Existing child: {existing_child.cidr} (parent: {existing_child.parent})")
    print(f"New parent: {new_parent.cidr}")
    
    result = engine.validate(new_parent, mock_storage)
    print(f"Validation result: {result.is_valid}")
    if not result.is_valid:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
    print()

if __name__ == "__main__":
    test_parent_child_overlap()
    test_invalid_overlap()
    test_reverse_case()