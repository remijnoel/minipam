#!/usr/bin/env python3
"""Create sample CIDR data for development."""
import os
import sys
from pathlib import Path

# Add src directory to path for development use
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from minipam.models import CIDRBlock
from minipam.storage import FileStorage

def create_sample_data():
    """Create sample CIDR blocks."""
    # Use environment variable or default to ./data
    data_path = os.environ.get("MINIPAM_STORAGE_PATH", "./data")
    storage = FileStorage(data_path)
    
    # Sample hierarchical CIDR blocks
    blocks = [
        CIDRBlock(
            cidr="10.0.0.0/8",
            name="Private Network",
            description="RFC 1918 private address space",
            tags=["private", "rfc1918"]
        ),
        CIDRBlock(
            cidr="10.0.0.0/16",
            name="Corporate Network",
            description="Main corporate network",
            parent="10.0.0.0/8",
            tags=["vlan:100", "location:HQ", "corporate"]
        ),
        CIDRBlock(
            cidr="10.0.128.0/17",
            name="DMZ Network",
            description="Demilitarized zone",
            parent="10.0.0.0/16",
            tags=["vlan:200", "location:HQ", "dmz"]
        ),
        CIDRBlock(
            cidr="10.0.128.0/23",
            name="Web Servers",
            description="Production web servers",
            parent="10.0.128.0/17",
            tags=["vlan:201", "device:lb-01", "customer:web-team", "location:HQ-Floor2"]
        ),
        CIDRBlock(
            cidr="10.0.130.0/23",
            name="API Servers",
            description="Backend API servers",
            parent="10.0.128.0/17",
            tags=["vlan:202", "device:lb-02", "customer:api-team", "location:HQ-Floor2"]
        ),
        CIDRBlock(
            cidr="10.1.0.0/16",
            name="Development Network",
            description="Development and testing",
            parent="10.0.0.0/8",
            tags=["vlan:300", "vrf:dev", "location:HQ", "environment:dev"]
        ),
        CIDRBlock(
            cidr="192.168.0.0/16",
            name="Office Network",
            description="Office workstations and printers",
            tags=["vlan:400", "vrf:office", "location:HQ", "office"]
        ),
        CIDRBlock(
            cidr="192.168.1.0/24",
            name="IT Department",
            description="IT department workstations",
            parent="192.168.0.0/16",
            tags=["vlan:401", "device:sw-it-01", "customer:it-dept", "location:HQ-Floor1"]
        ),
        CIDRBlock(
            cidr="172.16.0.0/12",
            name="Branch Networks",
            description="Remote branch office networks",
            tags=["private", "branch"]
        ),
        CIDRBlock(
            cidr="172.16.0.0/16",
            name="Branch NYC",
            description="New York branch office",
            parent="172.16.0.0/12",
            tags=["vlan:500", "location:NYC", "branch"]
        )
    ]
    
    # Store blocks
    for block in blocks:
        try:
            storage.put(block)
            print(f"Created: {block.cidr} - {block.name}")
        except Exception as e:
            print(f"Error creating {block.cidr}: {e}")

if __name__ == "__main__":
    create_sample_data()