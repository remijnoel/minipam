#!/usr/bin/env python3
"""
Debug script to test tree structure with real data.
"""

from fastapi.testclient import TestClient
from minipam.main import create_minipam_app
import json

def main():
    print("🔍 Debugging CIDR Tree Structure")
    print("=" * 50)
    
    # Create app and client
    app = create_minipam_app()
    client = TestClient(app)
    
    # Create test data
    print("\n📝 Creating test data...")
    
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
    
    for data in test_data:
        response = client.post("/api/v1/cidrs", json=data)
        status = "✅" if response.status_code == 201 else "❌"
        print(f"{status} {data['cidr']} -> {response.status_code}")
        if response.status_code != 201:
            print(f"   Error: {response.text}")
    
    print("\n🌳 Testing tree structure...")
    
    # Test tree endpoint
    response = client.get("/api/v1/cidrs/tree")
    print(f"Tree endpoint status: {response.status_code}")
    
    if response.status_code == 200:
        tree = response.json()
        print(f"\n📊 Tree structure ({len(tree)} root nodes):")
        print("=" * 40)
        
        def print_tree(nodes, indent=""):
            for i, node in enumerate(nodes):
                children_count = len(node.get('children', []))
                print(f"{indent}📁 {node['cidr']} - {node['name']} ({children_count} children)")
                
                if node.get('children'):
                    print_tree(node['children'], indent + "  ")
                    
        print_tree(tree)
        
        print(f"\n📋 Raw JSON structure:")
        print(json.dumps(tree, indent=2))
        
        # Test what Vue.js should receive
        print(f"\n🎭 Vue.js perspective:")
        for i, node in enumerate(tree):
            print(f"Root node {i}: {node['cidr']}")
            print(f"  - Has children: {bool(node.get('children'))}")
            print(f"  - Children count: {len(node.get('children', []))}")
            print(f"  - Children array: {[c['cidr'] for c in node.get('children', [])]}")
            
            for j, child in enumerate(node.get('children', [])):
                print(f"  Child {j}: {child['cidr']}")
                print(f"    - Has children: {bool(child.get('children'))}")
                print(f"    - Children count: {len(child.get('children', []))}")
                print(f"    - Children array: {[c['cidr'] for c in child.get('children', [])]}")
    
    else:
        print(f"❌ Tree endpoint failed: {response.status_code}")
        print(response.text)
    
    print(f"\n🌐 UI should be accessible at: http://localhost:8000/ui/")
    print("📝 Check browser console for debug logs")

if __name__ == "__main__":
    main()