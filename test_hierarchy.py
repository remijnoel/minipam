#!/usr/bin/env python3
"""Test script for hierarchical CIDR display."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from minipam.models import CIDRBlock
from minipam.storage import FileStorage


def test_hierarchy():
    """Test the hierarchical CIDR display functionality."""
    print("Testing hierarchical CIDR display...")
    
    # Create test storage
    storage = FileStorage("/tmp/minipam_test")
    
    # Create test CIDR blocks with hierarchy
    blocks = [
        CIDRBlock(
            cidr="10.0.0.0/16",
            name="Main Network",
            description="Primary corporate network",
            tags=["vlan:100", "location:DC1"]
        ),
        CIDRBlock(
            cidr="10.0.128.0/17",
            name="DMZ zone",
            description="Demilitarized zone",
            parent="10.0.0.0/16",
            tags=["vlan:200", "location:DC1"]
        ),
        CIDRBlock(
            cidr="10.0.128.0/23",
            name="DMZ production",
            description="Production DMZ servers",
            parent="10.0.128.0/17",
            tags=["vlan:201", "device:fw01", "customer:production"]
        ),
        CIDRBlock(
            cidr="10.0.130.0/23",
            name="DMZ testing",
            description="Testing DMZ servers",
            parent="10.0.128.0/17",
            tags=["vlan:202", "device:fw01", "customer:testing"]
        ),
        CIDRBlock(
            cidr="172.16.0.0/16",
            name="Internal network",
            description="Internal corporate network",
            tags=["vlan:300", "location:Office"]
        ),
    ]
    
    # Store blocks
    for block in blocks:
        storage.put(block)
    
    # Test tree building
    all_blocks = storage.list()
    
    def build_tree_recursive(parent_cidr=None):
        """Build hierarchical tree from flat list of blocks."""
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
                    "children": build_tree_recursive(block.cidr)
                }
                children.append(node)
        return children
    
    tree = build_tree_recursive()
    
    def print_tree(nodes, depth=0):
        """Print tree structure for visualization."""
        for node in nodes:
            indent = "  " * depth
            toggle = "▼" if node["children"] else " "
            
            # Extract tag values
            tags_dict = {}
            for tag in node["tags"]:
                if ":" in tag:
                    key, value = tag.split(":", 1)
                    tags_dict[key] = value
            
            vlan = tags_dict.get("vlan", "Default")
            location = tags_dict.get("location", "-")
            device = tags_dict.get("device", "-")
            customer = tags_dict.get("customer", "-")
            
            print(f"{indent}{toggle} {node['cidr']:<18} {node['name']:<20} {vlan:<8} {location:<8} {device:<8} {customer}")
            
            if node["children"]:
                print_tree(node["children"], depth + 1)
    
    print("\nHierarchical CIDR Tree:")
    print("   Subnet             Name                 VLAN     Location Device   Customer")
    print("   " + "─" * 80)
    print_tree(tree)
    
    print(f"\nTest completed successfully!")
    print(f"Total blocks: {len(all_blocks)}")
    print(f"Root nodes: {len(tree)}")
    

if __name__ == "__main__":
    test_hierarchy()