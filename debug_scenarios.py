#!/usr/bin/env python3

"""Debug all overlap scenarios to understand the validation logic issues."""

from minipam.models import CIDRBlock
from minipam.validation import CIDRValidationEngine
from unittest.mock import Mock

def create_mock_storage(blocks):
    """Create a mock storage with the given blocks."""
    mock_storage = Mock()
    mock_storage.get.side_effect = lambda cidr: next(
        (block for block in blocks if block.cidr == cidr), None
    )
    mock_storage.list.return_value = blocks
    return mock_storage

def test_scenario(title, new_block, existing_blocks):
    """Test a validation scenario."""
    engine = CIDRValidationEngine()
    storage = create_mock_storage(existing_blocks)
    
    print(f"=== {title} ===")
    print(f"New block: {new_block.cidr} (parent: {new_block.parent})")
    print("Existing blocks:")
    for block in existing_blocks:
        print(f"  - {block.cidr} (parent: {block.parent})")
    
    result = engine.validate(new_block, storage)
    print(f"Validation result: {result.is_valid}")
    if not result.is_valid:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
    print()

def main():
    # Scenario 1: Valid parent-child (child declares parent correctly)
    test_scenario(
        "Scenario 1: Valid parent-child relationship",
        CIDRBlock(cidr="10.0.0.0/25", name="Child", parent="10.0.0.0/24", tags=[]),
        [CIDRBlock(cidr="10.0.0.0/24", name="Parent", parent=None, tags=[])]
    )
    
    # Scenario 2: Invalid overlap (child doesn't declare parent)
    test_scenario(
        "Scenario 2: Invalid overlap - child doesn't declare parent",
        CIDRBlock(cidr="10.0.0.0/25", name="Child", parent=None, tags=[]),
        [CIDRBlock(cidr="10.0.0.0/24", name="Parent", parent=None, tags=[])]
    )
    
    # Scenario 3: Adding parent for existing orphaned child
    test_scenario(
        "Scenario 3: Adding parent for existing orphaned child (PROBLEMATIC)",
        CIDRBlock(cidr="10.0.0.0/24", name="New Parent", parent=None, tags=[]),
        [CIDRBlock(cidr="10.0.0.0/25", name="Existing Child", parent=None, tags=[])]
    )
    
    # Scenario 4: Adding parent for existing child that declares different parent
    test_scenario(
        "Scenario 4: Adding parent but child has different parent",
        CIDRBlock(cidr="10.0.0.0/24", name="New Parent", parent=None, tags=[]),
        [CIDRBlock(cidr="10.0.0.0/25", name="Existing Child", parent="192.168.1.0/24", tags=[])]
    )
    
    # Scenario 5: Overlapping siblings
    test_scenario(
        "Scenario 5: Overlapping siblings (should fail)",
        CIDRBlock(cidr="10.0.1.0/25", name="New Sibling", parent="10.0.0.0/16", tags=[]),
        [
            CIDRBlock(cidr="10.0.0.0/16", name="Parent", parent=None, tags=[]),
            CIDRBlock(cidr="10.0.1.0/24", name="Existing Sibling", parent="10.0.0.0/16", tags=[])
        ]
    )
    
    # Scenario 6: Valid siblings (non-overlapping)
    test_scenario(
        "Scenario 6: Valid siblings (non-overlapping)",
        CIDRBlock(cidr="10.0.2.0/24", name="New Sibling", parent="10.0.0.0/16", tags=[]),
        [
            CIDRBlock(cidr="10.0.0.0/16", name="Parent", parent=None, tags=[]),
            CIDRBlock(cidr="10.0.1.0/24", name="Existing Sibling", parent="10.0.0.0/16", tags=[])
        ]
    )

if __name__ == "__main__":
    main()