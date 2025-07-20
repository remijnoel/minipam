#!/usr/bin/env python3
"""
Test UI DOM rendering to debug tree children visibility.
"""

import time
import threading
import uvicorn
import httpx
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from minipam.main import create_minipam_app


def start_test_server():
    """Start test server."""
    app = create_minipam_app()
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="critical")


def create_test_data():
    """Create test data via API."""
    print("Creating test data...")
    time.sleep(2)  # Wait for server
    
    base_url = "http://127.0.0.1:8002"
    
    test_data = [
        {
            "cidr": "192.168.0.0/16",
            "name": "Home Network",
            "description": "Home network",
            "parent": None,
            "tags": ["home"]
        },
        {
            "cidr": "192.168.1.0/24",
            "name": "IoT Network",
            "description": "IoT devices",
            "parent": "192.168.0.0/16",
            "tags": ["home", "iot"]
        },
        {
            "cidr": "192.168.2.0/24",
            "name": "Guest Network",
            "description": "Guest devices",
            "parent": "192.168.0.0/16",
            "tags": ["home", "guest"]
        }
    ]
    
    try:
        with httpx.Client() as client:
            for data in test_data:
                response = client.post(f"{base_url}/api/v1/cidrs", json=data)
                print(f"Created {data['cidr']}: {response.status_code}")
    except Exception as e:
        print(f"Error creating test data: {e}")


def test_ui_dom():
    """Test UI DOM structure."""
    print("Testing UI DOM structure...")
    
    # Setup Chrome driver
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=options)
        
        # Navigate to UI
        driver.get("http://127.0.0.1:8002/ui/")
        
        # Wait for app to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.ID, "app")))
        
        # Give Vue time to render
        time.sleep(3)
        
        print("\n=== PAGE TITLE ===")
        print(driver.title)
        
        print("\n=== NAVIGATION ===")
        nav_elements = driver.find_elements(By.CLASS_NAME, "nav-tab")
        for nav in nav_elements:
            print(f"Nav tab: {nav.text} (active: {'active' in nav.get_attribute('class')})")
        
        print("\n=== TREE NODES ===")
        tree_nodes = driver.find_elements(By.CLASS_NAME, "tree-node")
        print(f"Found {len(tree_nodes)} tree nodes")
        
        for i, node in enumerate(tree_nodes):
            text = node.text
            print(f"Node {i}: {text}")
            
            # Check for toggle button
            try:
                toggle = node.find_element(By.CLASS_NAME, "tree-toggle")
                print(f"  Toggle: '{toggle.text}'")
            except:
                print("  No toggle found")
        
        print("\n=== TREE CHILDREN ===")
        tree_children = driver.find_elements(By.CLASS_NAME, "tree-children")
        print(f"Found {len(tree_children)} tree-children containers")
        
        for i, child_container in enumerate(tree_children):
            print(f"Children container {i}: visible={child_container.is_displayed()}")
            child_nodes = child_container.find_elements(By.CLASS_NAME, "tree-node")
            print(f"  Contains {len(child_nodes)} child nodes")
        
        print("\n=== DEBUG INFO ===")
        debug_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Debug Info')]")
        if debug_elements:
            debug_text = debug_elements[0].find_element(By.XPATH, "..").text
            print("Debug section found:")
            print(debug_text)
        else:
            print("No debug section found")
        
        print("\n=== PAGE SOURCE (Tree section) ===")
        page_source = driver.page_source
        if "tree-node" in page_source:
            start = page_source.find('<div class="tree"')
            end = page_source.find('</div>', start + 200)
            if start > -1 and end > -1:
                tree_html = page_source[start:end+6]
                print(tree_html[:500] + "..." if len(tree_html) > 500 else tree_html)
        
        print("\n=== CONSOLE LOGS ===")
        logs = driver.get_log('browser')
        for log in logs[-10:]:  # Last 10 logs
            print(f"{log['level']}: {log['message']}")
        
        # Try clicking on a toggle button
        print("\n=== TESTING TOGGLE ===")
        toggles = driver.find_elements(By.CLASS_NAME, "tree-toggle")
        if toggles:
            print(f"Clicking first toggle: '{toggles[0].text}'")
            toggles[0].click()
            time.sleep(1)
            
            # Check again
            tree_children_after = driver.find_elements(By.CLASS_NAME, "tree-children")
            print(f"After toggle: {len(tree_children_after)} tree-children containers")
            
            # Get logs after click
            new_logs = driver.get_log('browser')
            print("New console logs:")
            for log in new_logs[-5:]:
                print(f"{log['level']}: {log['message']}")
    
    except Exception as e:
        print(f"Error during DOM test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'driver' in locals():
            driver.quit()


def main():
    print("🧪 Testing UI DOM Structure")
    print("=" * 50)
    
    # Start server in background
    server_thread = threading.Thread(target=start_test_server, daemon=True)
    server_thread.start()
    
    # Create test data in background
    data_thread = threading.Thread(target=create_test_data, daemon=True)
    data_thread.start()
    
    # Wait a bit for setup
    time.sleep(4)
    
    # Test DOM
    test_ui_dom()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"Test failed: {e}")
        # If Chrome driver not available, show instructions
        if "chrome" in str(e).lower():
            print("\n📝 Chrome driver not available for automated testing.")
            print("To test manually:")
            print("1. Run: python debug_tree.py &")
            print("2. Open: http://localhost:8000/ui/")
            print("3. Navigate to CIDR tab")
            print("4. Check browser console for debug logs")
            print("5. Try clicking the ▶ toggle buttons")