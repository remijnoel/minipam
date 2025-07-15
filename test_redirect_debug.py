#!/usr/bin/env python3
"""
Test script to debug OIDC redirect loop issue

This script simulates the browser OIDC authentication flow to identify
where redirect loops are occurring.
"""

import requests
import json
from urllib.parse import urlparse, parse_qs
import time


class OIDCFlowDebugger:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        # Set a browser-like user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.redirect_history = []
        
    def log_step(self, step, url, status_code, headers=None, content_preview=None):
        """Log each step of the authentication flow"""
        print(f"\n{'='*50}")
        print(f"STEP {len(self.redirect_history) + 1}: {step}")
        print(f"URL: {url}")
        print(f"Status: {status_code}")
        
        if headers:
            print("Important Headers:")
            for header in ['Location', 'Set-Cookie', 'Content-Type']:
                if header in headers:
                    print(f"  {header}: {headers[header]}")
        
        if content_preview:
            print(f"Content Preview: {content_preview[:200]}...")
            
        # Track redirects
        if 300 <= status_code < 400 and headers and 'Location' in headers:
            location = headers['Location']
            self.redirect_history.append({
                'from': url,
                'to': location,
                'status': status_code
            })
            print(f"REDIRECT TO: {location}")
            
        print(f"{'='*50}")
    
    def test_auth_config(self):
        """Test the authentication configuration endpoint"""
        print("Testing auth configuration endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/auth/config")
            self.log_step(
                "Auth Config Check", 
                f"{self.base_url}/auth/config",
                response.status_code,
                dict(response.headers),
                response.text
            )
            
            if response.status_code == 200:
                config = response.json()
                print(f"Auth Config: {json.dumps(config, indent=2)}")
                return config
            else:
                print(f"ERROR: Auth config failed with {response.status_code}")
                return None
                
        except Exception as e:
            print(f"ERROR in auth config: {e}")
            return None
    
    def test_auth_health(self):
        """Test the authentication health endpoint"""
        print("Testing auth health endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/auth/health")
            self.log_step(
                "Auth Health Check", 
                f"{self.base_url}/auth/health",
                response.status_code,
                dict(response.headers),
                response.text
            )
            
            if response.status_code == 200:
                health = response.json()
                print(f"Auth Health: {json.dumps(health, indent=2)}")
                return health
            else:
                print(f"ERROR: Auth health failed with {response.status_code}")
                return None
                
        except Exception as e:
            print(f"ERROR in auth health: {e}")
            return None
    
    def test_root_access(self):
        """Test accessing the root URL (/) to see if auth middleware redirects"""
        print("Testing root URL access...")
        
        try:
            # Don't follow redirects automatically so we can track them
            response = self.session.get(f"{self.base_url}/", allow_redirects=False)
            self.log_step(
                "Root URL Access", 
                f"{self.base_url}/",
                response.status_code,
                dict(response.headers),
                response.text
            )
            
            return response
            
        except Exception as e:
            print(f"ERROR in root access: {e}")
            return None
    
    def test_ui_access(self):
        """Test accessing the UI URL (/ui) to see if auth middleware redirects"""
        print("Testing UI URL access...")
        
        try:
            response = self.session.get(f"{self.base_url}/ui", allow_redirects=False)
            self.log_step(
                "UI URL Access", 
                f"{self.base_url}/ui",
                response.status_code,
                dict(response.headers),
                response.text
            )
            
            return response
            
        except Exception as e:
            print(f"ERROR in UI access: {e}")
            return None
    
    def test_oidc_login_flow(self, max_redirects=10):
        """Test the full OIDC login flow and track redirects"""
        print("Testing OIDC login flow...")
        
        current_url = f"{self.base_url}/auth/login/oidc"
        redirect_count = 0
        
        while redirect_count < max_redirects:
            try:
                print(f"\nFollowing redirect #{redirect_count + 1} to: {current_url}")
                
                response = self.session.get(current_url, allow_redirects=False)
                self.log_step(
                    f"OIDC Flow Step {redirect_count + 1}",
                    current_url,
                    response.status_code,
                    dict(response.headers),
                    response.text
                )
                
                # Check if we have a redirect
                if 300 <= response.status_code < 400 and 'Location' in response.headers:
                    redirect_count += 1
                    next_url = response.headers['Location']
                    
                    # Check if this is a redirect loop (going back to same URL)
                    if next_url == current_url:
                        print(f"REDIRECT LOOP DETECTED! URL redirecting to itself: {current_url}")
                        break
                    
                    # Check if we've seen this URL before
                    for i, redirect in enumerate(self.redirect_history):
                        if redirect['to'] == next_url:
                            print(f"REDIRECT LOOP DETECTED! Already visited {next_url} at step {i}")
                            break
                    
                    current_url = next_url
                    
                    # Add a small delay to avoid overwhelming the server
                    time.sleep(0.1)
                else:
                    print(f"Flow ended with status {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"ERROR in OIDC flow at redirect {redirect_count}: {e}")
                break
        
        if redirect_count >= max_redirects:
            print(f"STOPPED: Reached maximum redirects ({max_redirects})")
        
        return redirect_count
    
    def analyze_middleware_behavior(self):
        """Test specific paths to understand auth middleware behavior"""
        print("Analyzing auth middleware behavior...")
        
        test_paths = [
            "/",
            "/ui",
            "/ui/",
            "/api/cidrs",
            "/auth/config",
            "/auth/health", 
            "/auth/login/oidc",
            "/auth/callback/oidc",
            "/health"
        ]
        
        for path in test_paths:
            try:
                url = f"{self.base_url}{path}"
                response = self.session.get(url, allow_redirects=False)
                
                print(f"\nPATH: {path}")
                print(f"  Status: {response.status_code}")
                if 'Location' in response.headers:
                    print(f"  Redirects to: {response.headers['Location']}")
                else:
                    print(f"  No redirect")
                    
            except Exception as e:
                print(f"  ERROR: {e}")
    
    def run_full_debug(self):
        """Run the complete debugging flow"""
        print("="*80)
        print("OIDC REDIRECT LOOP DEBUGGING")
        print("="*80)
        
        # Step 1: Check auth configuration
        auth_config = self.test_auth_config()
        if not auth_config:
            print("CRITICAL: Cannot get auth config - stopping")
            return
        
        # Step 2: Check auth health
        auth_health = self.test_auth_health()
        if not auth_health:
            print("CRITICAL: Cannot get auth health - stopping")
            return
        
        # Step 3: Test middleware behavior on different paths
        self.analyze_middleware_behavior()
        
        # Step 4: Test root and UI access
        self.test_root_access()
        self.test_ui_access()
        
        # Step 5: Test OIDC flow
        redirect_count = self.test_oidc_login_flow()
        
        # Summary
        print("\n" + "="*80)
        print("DEBUGGING SUMMARY")
        print("="*80)
        print(f"Total redirects detected: {len(self.redirect_history)}")
        print(f"OIDC flow redirects: {redirect_count}")
        
        if self.redirect_history:
            print("\nRedirect Chain:")
            for i, redirect in enumerate(self.redirect_history):
                print(f"  {i+1}. {redirect['from']} -> {redirect['to']} (Status: {redirect['status']})")
        
        if redirect_count >= 5:
            print("\nLIKELY REDIRECT LOOP DETECTED!")
        else:
            print("\nRedirect behavior appears normal.")


if __name__ == "__main__":
    debugger = OIDCFlowDebugger()
    debugger.run_full_debug()