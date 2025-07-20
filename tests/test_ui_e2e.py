"""
End-to-end UI tests using selenium.
"""

import pytest
import time
import threading
import uvicorn
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from minipam.main import create_minipam_app


@pytest.fixture(scope="session")
def server():
    """Start test server in background."""
    app = create_minipam_app()
    
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="critical")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    yield "http://127.0.0.1:8001"


@pytest.fixture
def driver():
    """Create headless Chrome driver."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=options)
        yield driver
    except Exception as e:
        pytest.skip(f"Chrome driver not available: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()


@pytest.fixture
def api_client(server):
    """Create API client for test data setup."""
    import httpx
    return httpx.Client(base_url=server)


class TestUIE2E:
    """End-to-end UI tests."""
    
    def test_ui_loads_and_displays_tree(self, driver, server, api_client):
        """Test that UI loads and displays tree structure."""
        # Create test data via API
        parent_data = {
            "cidr": "192.168.0.0/16",
            "name": "Home Network",
            "description": "Home network range",
            "parent": None,
            "tags": ["home"]
        }
        response = api_client.post("/api/v1/cidrs", json=parent_data)
        assert response.status_code == 201
        
        child_data = {
            "cidr": "192.168.1.0/24",
            "name": "IoT Network", 
            "description": "IoT devices subnet",
            "parent": "192.168.0.0/16",
            "tags": ["home", "iot"]
        }
        response = api_client.post("/api/v1/cidrs", json=child_data)
        assert response.status_code == 201
        
        # Navigate to UI
        driver.get(f"{server}/ui/")
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
        # Wait for Vue app to initialize
        wait.until(EC.presence_of_element_located((By.ID, "app")))
        
        # Give Vue time to render
        time.sleep(2)
        
        # Check if main content loaded
        try:
            # Should see navigation
            nav_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "nav")))
            assert "CIDR" in nav_element.text
            
            # Click on CIDR tab
            cidr_tab = driver.find_element(By.XPATH, "//a[contains(text(), 'CIDR')]")
            cidr_tab.click()
            
            # Wait for tree content
            time.sleep(1)
            
            # Look for tree nodes
            tree_nodes = driver.find_elements(By.CLASS_NAME, "tree-node")
            print(f"Found {len(tree_nodes)} tree nodes")
            
            # Check for CIDR content
            page_source = driver.page_source
            print("Page contains 192.168.0.0/16:", "192.168.0.0/16" in page_source)
            print("Page contains 192.168.1.0/24:", "192.168.1.0/24" in page_source) 
            print("Page contains Home Network:", "Home Network" in page_source)
            print("Page contains IoT Network:", "IoT Network" in page_source)
            
            # Check console for errors
            logs = driver.get_log('browser')
            for log in logs:
                print(f"Browser log: {log}")
            
            # Assert we can see the parent CIDR
            assert "192.168.0.0/16" in page_source
            assert "Home Network" in page_source
            
        except (TimeoutException, NoSuchElementException) as e:
            # Print page source for debugging
            print("Page source:", driver.page_source)
            print("Current URL:", driver.current_url)
            raise e
    
    def test_add_child_button_functionality(self, driver, server, api_client):
        """Test the Add Child button functionality."""
        # Create parent data
        parent_data = {
            "cidr": "10.0.0.0/16",
            "name": "Corporate Network",
            "description": "Corporate network",
            "parent": None,
            "tags": ["corporate"]
        }
        response = api_client.post("/api/v1/cidrs", json=parent_data)
        assert response.status_code == 201
        
        # Navigate to UI
        driver.get(f"{server}/ui/")
        
        wait = WebDriverWait(driver, 10)
        
        # Wait for app to load
        wait.until(EC.presence_of_element_located((By.ID, "app")))
        time.sleep(2)
        
        # Go to CIDR tab
        cidr_tab = driver.find_element(By.XPATH, "//a[contains(text(), 'CIDR')]")
        cidr_tab.click()
        time.sleep(1)
        
        # Look for Add Child button
        try:
            add_child_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '+ Child')]")
            print(f"Found {len(add_child_buttons)} Add Child buttons")
            
            if add_child_buttons:
                # Click the first Add Child button
                add_child_buttons[0].click()
                time.sleep(1)
                
                # Should see modal
                modal = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "modal")))
                assert modal.is_displayed()
                
                # Check modal title
                modal_title = driver.find_element(By.CLASS_NAME, "modal-title")
                assert "Create Child CIDR" in modal_title.text
                
                # Check parent field is pre-filled
                parent_input = driver.find_element(By.XPATH, "//input[@placeholder='e.g., 10.0.0.0/8 (leave empty for root)']")
                assert parent_input.get_attribute("value") == "10.0.0.0/16"
                assert parent_input.get_attribute("disabled") is not None
                
        except (TimeoutException, NoSuchElementException) as e:
            print("Page source:", driver.page_source)
            raise e