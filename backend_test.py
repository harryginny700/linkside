#!/usr/bin/env python3
"""
Comprehensive backend API test suite for reklam sitesi (ad banner directory)
Tests all endpoints: Auth, Banners, Settings, Views & Stats, Upload
"""
import requests
import json
import io
from PIL import Image

# Backend base URL from frontend/.env
BASE_URL = "https://column-ads-hub.preview.emergentagent.com/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Global token storage
auth_token = None
test_banner_id = None


def print_test(name, passed, details=""):
    """Print test result with formatting"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if details:
        print(f"    Details: {details}")
    if not passed:
        print()


def test_auth_login_success():
    """Test POST /api/auth/login with correct credentials"""
    global auth_token
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Auth: Login with correct credentials", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        if "token" not in data or "username" not in data:
            print_test("Auth: Login with correct credentials", False, 
                      f"Missing token or username in response: {data}")
            return False
        
        if data["username"] != ADMIN_USERNAME:
            print_test("Auth: Login with correct credentials", False, 
                      f"Username mismatch: expected {ADMIN_USERNAME}, got {data['username']}")
            return False
        
        auth_token = data["token"]
        print_test("Auth: Login with correct credentials", True, 
                  f"Token received: {auth_token[:20]}...")
        return True
    except Exception as e:
        print_test("Auth: Login with correct credentials", False, str(e))
        return False


def test_auth_login_wrong_password():
    """Test POST /api/auth/login with wrong password"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": ADMIN_USERNAME, "password": "wrongpassword"},
            timeout=10
        )
        
        if response.status_code != 401:
            print_test("Auth: Login with wrong password", False, 
                      f"Expected 401, got {response.status_code}")
            return False
        
        print_test("Auth: Login with wrong password", True, "Correctly rejected with 401")
        return True
    except Exception as e:
        print_test("Auth: Login with wrong password", False, str(e))
        return False


def test_auth_me_with_token():
    """Test GET /api/auth/me with valid Bearer token"""
    if not auth_token:
        print_test("Auth: GET /me with valid token", False, "No auth token available")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Auth: GET /me with valid token", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        if data.get("username") != ADMIN_USERNAME:
            print_test("Auth: GET /me with valid token", False, 
                      f"Username mismatch: expected {ADMIN_USERNAME}, got {data.get('username')}")
            return False
        
        print_test("Auth: GET /me with valid token", True, f"Username: {data['username']}")
        return True
    except Exception as e:
        print_test("Auth: GET /me with valid token", False, str(e))
        return False


def test_auth_me_without_token():
    """Test GET /api/auth/me without token"""
    try:
        response = requests.get(f"{BASE_URL}/auth/me", timeout=10)
        
        if response.status_code not in [401, 403]:
            print_test("Auth: GET /me without token", False, 
                      f"Expected 401/403, got {response.status_code}")
            return False
        
        print_test("Auth: GET /me without token", True, 
                  f"Correctly rejected with {response.status_code}")
        return True
    except Exception as e:
        print_test("Auth: GET /me without token", False, str(e))
        return False


def test_banners_get_public():
    """Test GET /api/banners (public) - should return only active banners"""
    try:
        response = requests.get(f"{BASE_URL}/banners", timeout=10)
        
        if response.status_code != 200:
            print_test("Banners: GET public (active only)", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        banners = response.json()
        if not isinstance(banners, list):
            print_test("Banners: GET public (active only)", False, 
                      f"Expected list, got {type(banners)}")
            return False
        
        # Check all returned banners are active
        inactive_count = sum(1 for b in banners if not b.get("active", True))
        if inactive_count > 0:
            print_test("Banners: GET public (active only)", False, 
                      f"Found {inactive_count} inactive banners in public response")
            return False
        
        # Check ordering (should be sorted by 'order' ascending)
        orders = [b.get("order", 0) for b in banners]
        if orders != sorted(orders):
            print_test("Banners: GET public (active only)", False, 
                      f"Banners not sorted by order: {orders}")
            return False
        
        print_test("Banners: GET public (active only)", True, 
                  f"Returned {len(banners)} active banners, correctly ordered")
        return True
    except Exception as e:
        print_test("Banners: GET public (active only)", False, str(e))
        return False


def test_banners_get_all():
    """Test GET /api/banners?all=true - should return all banners"""
    try:
        response = requests.get(f"{BASE_URL}/banners?all=true", timeout=10)
        
        if response.status_code != 200:
            print_test("Banners: GET all banners", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        banners = response.json()
        if not isinstance(banners, list):
            print_test("Banners: GET all banners", False, 
                      f"Expected list, got {type(banners)}")
            return False
        
        # Should have 5 seeded banners
        if len(banners) < 5:
            print_test("Banners: GET all banners", False, 
                      f"Expected at least 5 seeded banners, got {len(banners)}")
            return False
        
        print_test("Banners: GET all banners", True, 
                  f"Returned {len(banners)} banners (including inactive)")
        return True
    except Exception as e:
        print_test("Banners: GET all banners", False, str(e))
        return False


def test_banners_create_with_auth():
    """Test POST /api/banners with Bearer token"""
    global test_banner_id
    
    if not auth_token:
        print_test("Banners: POST create with auth", False, "No auth token available")
        return False
    
    try:
        banner_data = {
            "section": "grid",
            "image": "https://example.com/test.png",
            "url": "https://example.com/target",
            "title": "Test Banner for API Testing",
            "orient": "square",
            "span": 1,
            "active": True
        }
        
        response = requests.post(
            f"{BASE_URL}/banners",
            json=banner_data,
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Banners: POST create with auth", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        if "id" not in data:
            print_test("Banners: POST create with auth", False, 
                      f"Missing 'id' in response: {data}")
            return False
        
        test_banner_id = data["id"]
        
        # Verify all fields
        for key, value in banner_data.items():
            if data.get(key) != value:
                print_test("Banners: POST create with auth", False, 
                          f"Field mismatch: {key} expected {value}, got {data.get(key)}")
                return False
        
        print_test("Banners: POST create with auth", True, 
                  f"Created banner with id: {test_banner_id}")
        return True
    except Exception as e:
        print_test("Banners: POST create with auth", False, str(e))
        return False


def test_banners_create_without_auth():
    """Test POST /api/banners without token - should fail"""
    try:
        banner_data = {
            "section": "grid",
            "image": "https://example.com/test.png",
            "url": "https://example.com/target",
            "title": "Unauthorized Test",
            "orient": "square",
            "span": 1,
            "active": True
        }
        
        response = requests.post(
            f"{BASE_URL}/banners",
            json=banner_data,
            timeout=10
        )
        
        if response.status_code not in [401, 403]:
            print_test("Banners: POST create without auth", False, 
                      f"Expected 401/403, got {response.status_code}")
            return False
        
        print_test("Banners: POST create without auth", True, 
                  f"Correctly rejected with {response.status_code}")
        return True
    except Exception as e:
        print_test("Banners: POST create without auth", False, str(e))
        return False


def test_banners_update_with_auth():
    """Test PUT /api/banners/{id} with Bearer token"""
    if not auth_token:
        print_test("Banners: PUT update with auth", False, "No auth token available")
        return False
    
    if not test_banner_id:
        print_test("Banners: PUT update with auth", False, "No test banner id available")
        return False
    
    try:
        update_data = {"title": "Updated Test Banner Title"}
        
        response = requests.put(
            f"{BASE_URL}/banners/{test_banner_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Banners: PUT update with auth", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        if data.get("title") != update_data["title"]:
            print_test("Banners: PUT update with auth", False, 
                      f"Title not updated: expected '{update_data['title']}', got '{data.get('title')}'")
            return False
        
        print_test("Banners: PUT update with auth", True, 
                  f"Updated banner title to: {data['title']}")
        return True
    except Exception as e:
        print_test("Banners: PUT update with auth", False, str(e))
        return False


def test_banners_click():
    """Test POST /api/banners/{id}/click (public) - should increment clicks"""
    if not test_banner_id:
        print_test("Banners: POST click (public)", False, "No test banner id available")
        return False
    
    try:
        # Get current clicks count
        response = requests.get(f"{BASE_URL}/banners?all=true", timeout=10)
        if response.status_code != 200:
            print_test("Banners: POST click (public)", False, 
                      f"Failed to get banners: {response.status_code}")
            return False
        
        banners = response.json()
        test_banner = next((b for b in banners if b["id"] == test_banner_id), None)
        if not test_banner:
            print_test("Banners: POST click (public)", False, 
                      "Test banner not found in banners list")
            return False
        
        initial_clicks = test_banner.get("clicks", 0)
        
        # Click the banner
        response = requests.post(f"{BASE_URL}/banners/{test_banner_id}/click", timeout=10)
        if response.status_code != 200:
            print_test("Banners: POST click (public)", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        # Verify clicks incremented
        response = requests.get(f"{BASE_URL}/banners?all=true", timeout=10)
        banners = response.json()
        test_banner = next((b for b in banners if b["id"] == test_banner_id), None)
        new_clicks = test_banner.get("clicks", 0)
        
        if new_clicks != initial_clicks + 1:
            print_test("Banners: POST click (public)", False, 
                      f"Clicks not incremented: expected {initial_clicks + 1}, got {new_clicks}")
            return False
        
        print_test("Banners: POST click (public)", True, 
                  f"Clicks incremented from {initial_clicks} to {new_clicks}")
        return True
    except Exception as e:
        print_test("Banners: POST click (public)", False, str(e))
        return False


def test_banners_reorder():
    """Test POST /api/banners/reorder with Bearer token"""
    if not auth_token:
        print_test("Banners: POST reorder with auth", False, "No auth token available")
        return False
    
    try:
        # Get current banners
        response = requests.get(f"{BASE_URL}/banners?all=true", timeout=10)
        if response.status_code != 200:
            print_test("Banners: POST reorder with auth", False, 
                      f"Failed to get banners: {response.status_code}")
            return False
        
        banners = response.json()
        if len(banners) < 2:
            print_test("Banners: POST reorder with auth", False, 
                      "Need at least 2 banners to test reorder")
            return False
        
        # Reverse the order
        original_ids = [b["id"] for b in banners]
        reversed_ids = list(reversed(original_ids))
        
        # Reorder
        response = requests.post(
            f"{BASE_URL}/banners/reorder",
            json={"ids": reversed_ids},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Banners: POST reorder with auth", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        # Verify order changed
        response = requests.get(f"{BASE_URL}/banners?all=true", timeout=10)
        banners = response.json()
        new_ids = [b["id"] for b in banners]
        
        if new_ids != reversed_ids:
            print_test("Banners: POST reorder with auth", False, 
                      f"Order not changed correctly. Expected {reversed_ids}, got {new_ids}")
            return False
        
        # Restore original order
        requests.post(
            f"{BASE_URL}/banners/reorder",
            json={"ids": original_ids},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        print_test("Banners: POST reorder with auth", True, 
                  f"Successfully reordered {len(banners)} banners")
        return True
    except Exception as e:
        print_test("Banners: POST reorder with auth", False, str(e))
        return False


def test_settings_get_public():
    """Test GET /api/settings (public)"""
    try:
        response = requests.get(f"{BASE_URL}/settings", timeout=10)
        
        if response.status_code != 200:
            print_test("Settings: GET public", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        required_fields = ["siteTitle", "gridColumns", "ageGateEnabled"]
        for field in required_fields:
            if field not in data:
                print_test("Settings: GET public", False, 
                          f"Missing required field: {field}")
                return False
        
        print_test("Settings: GET public", True, 
                  f"siteTitle: {data['siteTitle']}, gridColumns: {data['gridColumns']}, ageGateEnabled: {data['ageGateEnabled']}")
        return True
    except Exception as e:
        print_test("Settings: GET public", False, str(e))
        return False


def test_settings_update_with_auth():
    """Test PUT /api/settings with Bearer token"""
    if not auth_token:
        print_test("Settings: PUT update with auth", False, "No auth token available")
        return False
    
    try:
        # Get current settings
        response = requests.get(f"{BASE_URL}/settings", timeout=10)
        original_settings = response.json()
        original_columns = original_settings.get("gridColumns", 2)
        
        # Update gridColumns
        new_columns = 3 if original_columns != 3 else 4
        response = requests.put(
            f"{BASE_URL}/settings",
            json={"gridColumns": new_columns},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Settings: PUT update with auth", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        # Verify persisted
        response = requests.get(f"{BASE_URL}/settings", timeout=10)
        data = response.json()
        
        if data.get("gridColumns") != new_columns:
            print_test("Settings: PUT update with auth", False, 
                      f"gridColumns not updated: expected {new_columns}, got {data.get('gridColumns')}")
            return False
        
        # Restore original
        requests.put(
            f"{BASE_URL}/settings",
            json={"gridColumns": original_columns},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        print_test("Settings: PUT update with auth", True, 
                  f"Updated gridColumns from {original_columns} to {new_columns}")
        return True
    except Exception as e:
        print_test("Settings: PUT update with auth", False, str(e))
        return False


def test_settings_update_without_auth():
    """Test PUT /api/settings without token - should fail"""
    try:
        response = requests.put(
            f"{BASE_URL}/settings",
            json={"gridColumns": 5},
            timeout=10
        )
        
        if response.status_code not in [401, 403]:
            print_test("Settings: PUT update without auth", False, 
                      f"Expected 401/403, got {response.status_code}")
            return False
        
        print_test("Settings: PUT update without auth", True, 
                  f"Correctly rejected with {response.status_code}")
        return True
    except Exception as e:
        print_test("Settings: PUT update without auth", False, str(e))
        return False


def test_view_increment():
    """Test POST /api/view (public) - should increment daily views"""
    try:
        # Get current stats
        if not auth_token:
            print_test("Views: POST view increment", False, "No auth token for stats check")
            return False
        
        response = requests.get(
            f"{BASE_URL}/stats/overview",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        initial_views = response.json().get("totalViews", 0)
        
        # Record a view
        response = requests.post(f"{BASE_URL}/view", timeout=10)
        if response.status_code != 200:
            print_test("Views: POST view increment", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        # Verify views incremented
        response = requests.get(
            f"{BASE_URL}/stats/overview",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        new_views = response.json().get("totalViews", 0)
        
        if new_views != initial_views + 1:
            print_test("Views: POST view increment", False, 
                      f"Views not incremented: expected {initial_views + 1}, got {new_views}")
            return False
        
        print_test("Views: POST view increment", True, 
                  f"Views incremented from {initial_views} to {new_views}")
        return True
    except Exception as e:
        print_test("Views: POST view increment", False, str(e))
        return False


def test_stats_overview_with_auth():
    """Test GET /api/stats/overview with Bearer token"""
    if not auth_token:
        print_test("Stats: GET overview with auth", False, "No auth token available")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/stats/overview",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Stats: GET overview with auth", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        required_fields = ["totalViews", "totalClicks", "activeBanners", "ctr"]
        for field in required_fields:
            if field not in data:
                print_test("Stats: GET overview with auth", False, 
                          f"Missing required field: {field}")
                return False
        
        print_test("Stats: GET overview with auth", True, 
                  f"totalViews: {data['totalViews']}, totalClicks: {data['totalClicks']}, activeBanners: {data['activeBanners']}, ctr: {data['ctr']}%")
        return True
    except Exception as e:
        print_test("Stats: GET overview with auth", False, str(e))
        return False


def test_stats_overview_without_auth():
    """Test GET /api/stats/overview without token - should fail"""
    try:
        response = requests.get(f"{BASE_URL}/stats/overview", timeout=10)
        
        if response.status_code not in [401, 403]:
            print_test("Stats: GET overview without auth", False, 
                      f"Expected 401/403, got {response.status_code}")
            return False
        
        print_test("Stats: GET overview without auth", True, 
                  f"Correctly rejected with {response.status_code}")
        return True
    except Exception as e:
        print_test("Stats: GET overview without auth", False, str(e))
        return False


def test_stats_daily_with_auth():
    """Test GET /api/stats/daily with Bearer token"""
    if not auth_token:
        print_test("Stats: GET daily with auth", False, "No auth token available")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/stats/daily",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Stats: GET daily with auth", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        if not isinstance(data, list):
            print_test("Stats: GET daily with auth", False, 
                      f"Expected list, got {type(data)}")
            return False
        
        if len(data) != 14:
            print_test("Stats: GET daily with auth", False, 
                      f"Expected 14 items, got {len(data)}")
            return False
        
        # Check each item has required fields
        for item in data:
            if not all(k in item for k in ["date", "views", "clicks"]):
                print_test("Stats: GET daily with auth", False, 
                          f"Missing required fields in daily stat: {item}")
                return False
        
        print_test("Stats: GET daily with auth", True, 
                  f"Returned 14 daily stats items")
        return True
    except Exception as e:
        print_test("Stats: GET daily with auth", False, str(e))
        return False


def test_stats_daily_without_auth():
    """Test GET /api/stats/daily without token - should fail"""
    try:
        response = requests.get(f"{BASE_URL}/stats/daily", timeout=10)
        
        if response.status_code not in [401, 403]:
            print_test("Stats: GET daily without auth", False, 
                      f"Expected 401/403, got {response.status_code}")
            return False
        
        print_test("Stats: GET daily without auth", True, 
                  f"Correctly rejected with {response.status_code}")
        return True
    except Exception as e:
        print_test("Stats: GET daily without auth", False, str(e))
        return False


def test_upload_with_auth():
    """Test POST /api/upload with Bearer token and multipart file"""
    if not auth_token:
        print_test("Upload: POST with auth", False, "No auth token available")
        return False
    
    try:
        # Create a small test PNG image
        img = Image.new('RGB', (10, 10), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        files = {'file': ('test.png', img_bytes, 'image/png')}
        
        response = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Upload: POST with auth", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        if "url" not in data:
            print_test("Upload: POST with auth", False, 
                      f"Missing 'url' in response: {data}")
            return False
        
        url = data["url"]
        if not url.startswith("data:image"):
            print_test("Upload: POST with auth", False, 
                      f"URL should be base64 data URL starting with 'data:image', got: {url[:50]}")
            return False
        
        print_test("Upload: POST with auth", True, 
                  f"Uploaded image, received base64 data URL ({len(url)} chars)")
        return True
    except Exception as e:
        print_test("Upload: POST with auth", False, str(e))
        return False


def test_upload_without_auth():
    """Test POST /api/upload without token - should fail"""
    try:
        # Create a small test PNG image
        img = Image.new('RGB', (10, 10), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        files = {'file': ('test.png', img_bytes, 'image/png')}
        
        response = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            timeout=10
        )
        
        if response.status_code not in [401, 403]:
            print_test("Upload: POST without auth", False, 
                      f"Expected 401/403, got {response.status_code}")
            return False
        
        print_test("Upload: POST without auth", True, 
                  f"Correctly rejected with {response.status_code}")
        return True
    except Exception as e:
        print_test("Upload: POST without auth", False, str(e))
        return False


def test_banners_delete_with_auth():
    """Test DELETE /api/banners/{id} with Bearer token - cleanup test banner"""
    if not auth_token:
        print_test("Banners: DELETE with auth", False, "No auth token available")
        return False
    
    if not test_banner_id:
        print_test("Banners: DELETE with auth", False, "No test banner id available")
        return False
    
    try:
        response = requests.delete(
            f"{BASE_URL}/banners/{test_banner_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Banners: DELETE with auth", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        # Verify banner removed
        response = requests.get(f"{BASE_URL}/banners?all=true", timeout=10)
        banners = response.json()
        if any(b["id"] == test_banner_id for b in banners):
            print_test("Banners: DELETE with auth", False, 
                      "Banner still exists after deletion")
            return False
        
        print_test("Banners: DELETE with auth", True, 
                  f"Successfully deleted banner {test_banner_id}")
        return True
    except Exception as e:
        print_test("Banners: DELETE with auth", False, str(e))
        return False


def run_all_tests():
    """Run all backend API tests"""
    print("=" * 80)
    print("BACKEND API TEST SUITE - Reklam Sitesi")
    print(f"Base URL: {BASE_URL}")
    print("=" * 80)
    print()
    
    results = {}
    
    # Auth tests
    print("--- AUTH TESTS ---")
    results["auth_login_success"] = test_auth_login_success()
    results["auth_login_wrong_password"] = test_auth_login_wrong_password()
    results["auth_me_with_token"] = test_auth_me_with_token()
    results["auth_me_without_token"] = test_auth_me_without_token()
    print()
    
    # Banner tests
    print("--- BANNER TESTS ---")
    results["banners_get_public"] = test_banners_get_public()
    results["banners_get_all"] = test_banners_get_all()
    results["banners_create_with_auth"] = test_banners_create_with_auth()
    results["banners_create_without_auth"] = test_banners_create_without_auth()
    results["banners_update_with_auth"] = test_banners_update_with_auth()
    results["banners_click"] = test_banners_click()
    results["banners_reorder"] = test_banners_reorder()
    print()
    
    # Settings tests
    print("--- SETTINGS TESTS ---")
    results["settings_get_public"] = test_settings_get_public()
    results["settings_update_with_auth"] = test_settings_update_with_auth()
    results["settings_update_without_auth"] = test_settings_update_without_auth()
    print()
    
    # Views & Stats tests
    print("--- VIEWS & STATS TESTS ---")
    results["view_increment"] = test_view_increment()
    results["stats_overview_with_auth"] = test_stats_overview_with_auth()
    results["stats_overview_without_auth"] = test_stats_overview_without_auth()
    results["stats_daily_with_auth"] = test_stats_daily_with_auth()
    results["stats_daily_without_auth"] = test_stats_daily_without_auth()
    print()
    
    # Upload tests
    print("--- UPLOAD TESTS ---")
    results["upload_with_auth"] = test_upload_with_auth()
    results["upload_without_auth"] = test_upload_without_auth()
    print()
    
    # Cleanup - delete test banner
    print("--- CLEANUP ---")
    results["banners_delete_with_auth"] = test_banners_delete_with_auth()
    print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nFailed tests:")
        for test_name, result in results.items():
            if not result:
                print(f"  - {test_name}")
    
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
