#!/usr/bin/env python3
"""
Debug script to test UI with sample data.
"""

import asyncio
import httpx
import uvicorn
from threading import Thread
import time

def create_test_data():
    """Create test data via API calls."""
    print("Creating test data...")
    
    # Wait for server to start
    time.sleep(2)
    
    base_url = "http://localhost:8000/api/v1"
    
    # Create test CIDRs
    test_data = [
        {
            "cidr": "10.0.0.0/16",
            "name": "Corporate Network",
            "description": "Main corporate network",
            "parent": None,
            "tags": ["production"]
        },
        {
            "cidr": "10.0.1.0/24", 
            "name": "Development",
            "description": "Development subnet",
            "parent": "10.0.0.0/16",
            "tags": ["development"]
        },
        {
            "cidr": "10.0.2.0/24",
            "name": "Production",
            "description": "Production subnet", 
            "parent": "10.0.0.0/16",
            "tags": ["production"]
        },
        {
            "cidr": "10.0.1.128/25",
            "name": "Dev Team A",
            "description": "Team A development subnet",
            "parent": "10.0.1.0/24",
            "tags": ["development", "team-a"]
        }
    ]
    
    try:
        with httpx.Client() as client:
            for data in test_data:
                response = client.post(f"{base_url}/cidrs", json=data)
                if response.status_code == 201:
                    print(f"✓ Created CIDR: {data['cidr']}")
                else:
                    print(f"✗ Failed to create CIDR: {data['cidr']} - {response.status_code}")
            
            # Test tree endpoint
            response = client.get(f"{base_url}/cidrs/tree")
            if response.status_code == 200:
                tree = response.json()
                print(f"\n✓ Tree endpoint working. Root nodes: {len(tree)}")
                for node in tree:
                    print(f"  - {node['cidr']} ({len(node.get('children', []))} children)")
                    for child in node.get('children', []):
                        print(f"    - {child['cidr']} ({len(child.get('children', []))} children)")
                        for grandchild in child.get('children', []):
                            print(f"      - {grandchild['cidr']}")
            else:
                print(f"✗ Tree endpoint failed: {response.status_code}")
                
    except Exception as e:
        print(f"Error creating test data: {e}")

def start_server():
    """Start the server."""
    from minipam.main import create_minipam_app
    app = create_minipam_app()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    print("Starting MiniPAM debug server...")
    print("The UI will be available at: http://localhost:8000/ui/")
    print("Open browser console to see debug logs")
    
    # Start data creation in background
    data_thread = Thread(target=create_test_data, daemon=True)
    data_thread.start()
    
    # Start server (this will block)
    start_server()