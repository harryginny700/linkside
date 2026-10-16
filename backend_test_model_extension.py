#!/usr/bin/env python3
"""
Backend API test suite for MODEL EXTENSION verification
Tests NEW fields added to Banner and Settings models for customizable design feature
"""
import requests
import json
import io
from PIL import Image

# Backend base URL - direct testing on localhost:8001
BASE_URL = "http://localhost:8001/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Global storage
auth_token = None
test_banner_with_new_fields_id = None
test_banner_minimal_id = None

# Test counters
passed_tests = 0
failed_tests = 0


def print_test(name, passed, details=""):
    """Print test result with formatting"""
    global passed_tests, failed_tests
    if passed:
        passed_tests += 1
    else:
        failed_tests += 1
    
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if details:
        print(f"    Details: {details}")
    if not passed:
        print()


def test_auth_login():
    """Test POST /api/auth/login - get token for subsequent tests"""
    global auth_token
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("AUTH: Login admin/admin123", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        if "token" not in data:
            print_test("AUTH: Login admin/admin123", False, 
                      f"Missing token in response: {data}")
            return False
        
        auth_token = data["token"]
        print_test("AUTH: Login admin/admin123", True, 
                  f"Token: {auth_token[:30]}...")
        return True
    except Exception as e:
        print_test("AUTH: Login admin/admin123", False, str(e))
        return False


def test_auth_me():
    """Test GET /api/auth/me with Bearer token"""
    if not auth_token:
        print_test("AUTH: GET /api/auth/me with Bearer", False, "No auth token")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("AUTH: GET /api/auth/me with Bearer", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        if data.get("username") != ADMIN_USERNAME:
            print_test("AUTH: GET /api/auth/me with Bearer", False, 
                      f"Username mismatch: expected {ADMIN_USERNAME}, got {data.get('username')}")
            return False
        
        print_test("AUTH: GET /api/auth/me with Bearer", True, f"Username: {data['username']}")
        return True
    except Exception as e:
        print_test("AUTH: GET /api/auth/me with Bearer", False, str(e))
        return False


def test_auth_wrong_password():
    """Test POST /api/auth/login with wrong password"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": ADMIN_USERNAME, "password": "wrongpassword"},
            timeout=10
        )
        
        if response.status_code != 401:
            print_test("AUTH: Wrong password → 401", False, 
                      f"Expected 401, got {response.status_code}")
            return False
        
        print_test("AUTH: Wrong password → 401", True, "Correctly rejected")
        return True
    except Exception as e:
        print_test("AUTH: Wrong password → 401", False, str(e))
        return False


def test_banner_create_with_new_fields():
    """Test POST /api/banners with ALL NEW FIELDS (badge, headline, description, ctaText, accent)"""
    global test_banner_with_new_fields_id
    
    if not auth_token:
        print_test("BANNER: POST with NEW fields", False, "No auth token")
        return False
    
    try:
        # Create banner with ALL new fields as specified in review request
        banner_data = {
            "section": "grid",
            "image": "",
            "url": "https://example.com",
            "title": "Test Kart",
            "badge": "ZİRVE",
            "headline": "3000₺ NAKİT DENEME BONUSU",
            "description": "SINIRSIZ ANLIK ÇEKİM İMKANI",
            "ctaText": "TIKLA KAYIT OL",
            "accent": "#22c55e",
            "active": True
        }
        
        response = requests.post(
            f"{BASE_URL}/banners",
            json=banner_data,
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("BANNER: POST with NEW fields", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        
        # Verify ID exists
        if "id" not in data:
            print_test("BANNER: POST with NEW fields", False, 
                      f"Missing 'id' in response: {data}")
            return False
        
        test_banner_with_new_fields_id = data["id"]
        
        # CRITICAL: Verify ALL new fields echo back with EXACT values
        new_fields = ["badge", "headline", "description", "ctaText", "accent"]
        for field in new_fields:
            if field not in data:
                print_test("BANNER: POST with NEW fields", False, 
                          f"NEW field '{field}' missing in response")
                return False
            if data[field] != banner_data[field]:
                print_test("BANNER: POST with NEW fields", False, 
                          f"NEW field '{field}' mismatch: expected '{banner_data[field]}', got '{data[field]}'")
                return False
        
        print_test("BANNER: POST with NEW fields", True, 
                  f"Created banner {test_banner_with_new_fields_id} with badge='{data['badge']}', headline='{data['headline'][:30]}...', description='{data['description'][:30]}...', ctaText='{data['ctaText']}', accent='{data['accent']}'")
        return True
    except Exception as e:
        print_test("BANNER: POST with NEW fields", False, str(e))
        return False


def test_banner_get_includes_new_fields():
    """Test GET /api/banners returns banner with NEW fields present"""
    if not test_banner_with_new_fields_id:
        print_test("BANNER: GET includes NEW fields", False, "No test banner id")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/banners", timeout=10)
        
        if response.status_code != 200:
            print_test("BANNER: GET includes NEW fields", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        banners = response.json()
        
        # Find our test banner
        test_banner = None
        for b in banners:
            if b.get("id") == test_banner_with_new_fields_id:
                test_banner = b
                break
        
        if not test_banner:
            print_test("BANNER: GET includes NEW fields", False, 
                      f"Test banner {test_banner_with_new_fields_id} not found in GET response")
            return False
        
        # Verify NEW fields are present
        expected_values = {
            "badge": "ZİRVE",
            "headline": "3000₺ NAKİT DENEME BONUSU",
            "description": "SINIRSIZ ANLIK ÇEKİM İMKANI",
            "ctaText": "TIKLA KAYIT OL",
            "accent": "#22c55e"
        }
        
        for field, expected_value in expected_values.items():
            if field not in test_banner:
                print_test("BANNER: GET includes NEW fields", False, 
                          f"NEW field '{field}' missing in GET response")
                return False
            if test_banner[field] != expected_value:
                print_test("BANNER: GET includes NEW fields", False, 
                          f"NEW field '{field}' mismatch: expected '{expected_value}', got '{test_banner[field]}'")
                return False
        
        print_test("BANNER: GET includes NEW fields", True, 
                  f"All NEW fields present and correct in GET response")
        return True
    except Exception as e:
        print_test("BANNER: GET includes NEW fields", False, str(e))
        return False


def test_banner_update_new_field():
    """Test PUT /api/banners/{id} updating headline field"""
    if not auth_token or not test_banner_with_new_fields_id:
        print_test("BANNER: PUT update headline", False, "Missing auth token or banner id")
        return False
    
    try:
        update_data = {
            "headline": "5000₺ TEST"
        }
        
        response = requests.put(
            f"{BASE_URL}/banners/{test_banner_with_new_fields_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("BANNER: PUT update headline", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        
        if data.get("headline") != "5000₺ TEST":
            print_test("BANNER: PUT update headline", False, 
                      f"Headline not updated: expected '5000₺ TEST', got '{data.get('headline')}'")
            return False
        
        # Verify persistence by fetching again
        response2 = requests.get(f"{BASE_URL}/banners", timeout=10)
        banners = response2.json()
        test_banner = next((b for b in banners if b.get("id") == test_banner_with_new_fields_id), None)
        
        if not test_banner or test_banner.get("headline") != "5000₺ TEST":
            print_test("BANNER: PUT update headline", False, 
                      "Headline update not persisted")
            return False
        
        print_test("BANNER: PUT update headline", True, 
                  f"Headline updated to '5000₺ TEST' and persisted")
        return True
    except Exception as e:
        print_test("BANNER: PUT update headline", False, str(e))
        return False


def test_banner_create_without_auth():
    """Test POST /api/banners without auth → 401/403"""
    try:
        banner_data = {
            "section": "grid",
            "url": "https://example.com",
            "title": "Unauthorized Test"
        }
        
        response = requests.post(
            f"{BASE_URL}/banners",
            json=banner_data,
            timeout=10
        )
        
        if response.status_code not in [401, 403]:
            print_test("BANNER: POST without auth → 401/403", False, 
                      f"Expected 401/403, got {response.status_code}")
            return False
        
        print_test("BANNER: POST without auth → 401/403", True, 
                  f"Correctly rejected with {response.status_code}")
        return True
    except Exception as e:
        print_test("BANNER: POST without auth → 401/403", False, str(e))
        return False


def test_banner_click():
    """Test POST /api/banners/{id}/click"""
    if not test_banner_with_new_fields_id:
        print_test("BANNER: POST click", False, "No test banner id")
        return False
    
    try:
        response = requests.post(
            f"{BASE_URL}/banners/{test_banner_with_new_fields_id}/click",
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("BANNER: POST click", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        print_test("BANNER: POST click", True, "Click recorded")
        return True
    except Exception as e:
        print_test("BANNER: POST click", False, str(e))
        return False


def test_banner_backward_compatibility():
    """Test BACKWARD COMPATIBILITY: POST banner with MINIMAL body (no new fields)"""
    global test_banner_minimal_id
    
    if not auth_token:
        print_test("BANNER: Backward compatibility (minimal body)", False, "No auth token")
        return False
    
    try:
        # Minimal body: only section, url, title (no new fields)
        minimal_data = {
            "section": "grid",
            "url": "https://example.com/minimal",
            "title": "Minimal Test Banner"
        }
        
        response = requests.post(
            f"{BASE_URL}/banners",
            json=minimal_data,
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("BANNER: Backward compatibility (minimal body)", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        
        if "id" not in data:
            print_test("BANNER: Backward compatibility (minimal body)", False, 
                      f"Missing 'id' in response")
            return False
        
        test_banner_minimal_id = data["id"]
        
        # Verify NEW fields are present with DEFAULT values (empty strings)
        new_fields = ["badge", "headline", "description", "ctaText", "accent"]
        for field in new_fields:
            if field not in data:
                print_test("BANNER: Backward compatibility (minimal body)", False, 
                          f"NEW field '{field}' missing in response (should default to '')")
                return False
            if data[field] != "":
                print_test("BANNER: Backward compatibility (minimal body)", False, 
                          f"NEW field '{field}' should default to '', got '{data[field]}'")
                return False
        
        print_test("BANNER: Backward compatibility (minimal body)", True, 
                  f"Created banner {test_banner_minimal_id} with all NEW fields defaulted to ''")
        return True
    except Exception as e:
        print_test("BANNER: Backward compatibility (minimal body)", False, str(e))
        return False


def test_banner_reorder():
    """Test POST /api/banners/reorder"""
    if not auth_token:
        print_test("BANNER: POST reorder", False, "No auth token")
        return False
    
    try:
        # Get current banners
        response = requests.get(f"{BASE_URL}/banners?all=true", timeout=10)
        if response.status_code != 200:
            print_test("BANNER: POST reorder", False, "Failed to get banners for reorder test")
            return False
        
        banners = response.json()
        if len(banners) < 2:
            print_test("BANNER: POST reorder", False, "Need at least 2 banners to test reorder")
            return False
        
        # Get banner IDs and reverse them
        banner_ids = [b["id"] for b in banners]
        reversed_ids = list(reversed(banner_ids))
        
        # Reorder
        response = requests.post(
            f"{BASE_URL}/banners/reorder",
            json={"ids": reversed_ids},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("BANNER: POST reorder", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        # Verify order persisted
        response2 = requests.get(f"{BASE_URL}/banners?all=true", timeout=10)
        reordered_banners = response2.json()
        reordered_ids = [b["id"] for b in reordered_banners]
        
        if reordered_ids != reversed_ids:
            print_test("BANNER: POST reorder", False, 
                      f"Order not persisted correctly. Expected {reversed_ids}, got {reordered_ids}")
            return False
        
        print_test("BANNER: POST reorder", True, 
                  f"Reordered {len(banner_ids)} banners and verified persistence")
        return True
    except Exception as e:
        print_test("BANNER: POST reorder", False, str(e))
        return False


def test_settings_get_all_fields():
    """Test GET /api/settings returns ALL fields including NEW ones"""
    try:
        response = requests.get(f"{BASE_URL}/settings", timeout=10)
        
        if response.status_code != 200:
            print_test("SETTINGS: GET all fields", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        
        # Verify ALL fields including NEW ones
        required_fields = [
            "siteTitle",
            "brandName",           # NEW
            "headerTitle",         # NEW
            "headerSubtitle",      # NEW
            "statusLabel",         # NEW
            "tickerItems",         # NEW (array)
            "footerText",          # NEW
            "footerDomains",       # NEW
            "gridColumns",
            "ageGateEnabled",
            "totalViews"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            print_test("SETTINGS: GET all fields", False, 
                      f"Missing fields: {missing_fields}")
            return False
        
        # Verify brandName is "EMRE18" as per review request
        if data.get("brandName") != "EMRE18":
            print_test("SETTINGS: GET all fields", False, 
                      f"brandName should be 'EMRE18', got '{data.get('brandName')}'")
            return False
        
        # Verify statusLabel is "GÜNCEL" as per review request
        if data.get("statusLabel") != "GÜNCEL":
            print_test("SETTINGS: GET all fields", False, 
                      f"statusLabel should be 'GÜNCEL', got '{data.get('statusLabel')}'")
            return False
        
        # Verify tickerItems is an array with 3 items
        if not isinstance(data.get("tickerItems"), list):
            print_test("SETTINGS: GET all fields", False, 
                      f"tickerItems should be array, got {type(data.get('tickerItems'))}")
            return False
        
        if len(data.get("tickerItems")) != 3:
            print_test("SETTINGS: GET all fields", False, 
                      f"tickerItems should have 3 items, got {len(data.get('tickerItems'))}")
            return False
        
        # Verify each tickerItem has text and color
        for i, item in enumerate(data.get("tickerItems")):
            if "text" not in item or "color" not in item:
                print_test("SETTINGS: GET all fields", False, 
                          f"tickerItems[{i}] missing text or color: {item}")
                return False
        
        # Verify footerDomains is "emre18.com" as per review request
        if data.get("footerDomains") != "emre18.com":
            print_test("SETTINGS: GET all fields", False, 
                      f"footerDomains should be 'emre18.com', got '{data.get('footerDomains')}'")
            return False
        
        # Verify gridColumns is 3 as per review request
        if data.get("gridColumns") != 3:
            print_test("SETTINGS: GET all fields", False, 
                      f"gridColumns should be 3, got {data.get('gridColumns')}")
            return False
        
        print_test("SETTINGS: GET all fields", True, 
                  f"All fields present: brandName='{data['brandName']}', statusLabel='{data['statusLabel']}', tickerItems={len(data['tickerItems'])} items, footerDomains='{data['footerDomains']}', gridColumns={data['gridColumns']}")
        return True
    except Exception as e:
        print_test("SETTINGS: GET all fields", False, str(e))
        return False


def test_settings_update_ticker_items():
    """Test PUT /api/settings updating tickerItems"""
    if not auth_token:
        print_test("SETTINGS: PUT update tickerItems", False, "No auth token")
        return False
    
    try:
        # Update tickerItems to a NEW array
        update_data = {
            "tickerItems": [
                {"text": "TEST DUYURU", "color": "#ff0000"}
            ],
            "gridColumns": 3  # Keep gridColumns at 3
        }
        
        response = requests.put(
            f"{BASE_URL}/settings",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("SETTINGS: PUT update tickerItems", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        
        # Verify tickerItems updated
        if not isinstance(data.get("tickerItems"), list):
            print_test("SETTINGS: PUT update tickerItems", False, 
                      f"tickerItems should be array, got {type(data.get('tickerItems'))}")
            return False
        
        if len(data.get("tickerItems")) != 1:
            print_test("SETTINGS: PUT update tickerItems", False, 
                      f"tickerItems should have 1 item, got {len(data.get('tickerItems'))}")
            return False
        
        if data["tickerItems"][0].get("text") != "TEST DUYURU":
            print_test("SETTINGS: PUT update tickerItems", False, 
                      f"tickerItems[0].text should be 'TEST DUYURU', got '{data['tickerItems'][0].get('text')}'")
            return False
        
        if data["tickerItems"][0].get("color") != "#ff0000":
            print_test("SETTINGS: PUT update tickerItems", False, 
                      f"tickerItems[0].color should be '#ff0000', got '{data['tickerItems'][0].get('color')}'")
            return False
        
        # Verify persistence
        response2 = requests.get(f"{BASE_URL}/settings", timeout=10)
        data2 = response2.json()
        
        if len(data2.get("tickerItems")) != 1 or data2["tickerItems"][0].get("text") != "TEST DUYURU":
            print_test("SETTINGS: PUT update tickerItems", False, 
                      "tickerItems update not persisted")
            return False
        
        print_test("SETTINGS: PUT update tickerItems", True, 
                  f"Updated tickerItems to 1 item and verified persistence")
        return True
    except Exception as e:
        print_test("SETTINGS: PUT update tickerItems", False, str(e))
        return False


def test_settings_restore_ticker_items():
    """Test PUT /api/settings restoring tickerItems to original 3 items"""
    if not auth_token:
        print_test("SETTINGS: PUT restore tickerItems", False, "No auth token")
        return False
    
    try:
        # Restore tickerItems to original 3 items
        restore_data = {
            "tickerItems": [
                {"text": "YENİ ÜYELERE %200 HOŞ GELDİN BONUSU", "color": "#22d3ee"},
                {"text": "ANINDA PARA ÇEKİM GARANTİSİ", "color": "#f5b81c"},
                {"text": "GÜNCEL GİRİŞ ADRESLERİ 7/24 GÜNCELLENİR", "color": "#3b82f6"}
            ]
        }
        
        response = requests.put(
            f"{BASE_URL}/settings",
            json=restore_data,
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("SETTINGS: PUT restore tickerItems", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        
        if len(data.get("tickerItems")) != 3:
            print_test("SETTINGS: PUT restore tickerItems", False, 
                      f"tickerItems should have 3 items, got {len(data.get('tickerItems'))}")
            return False
        
        # Verify persistence
        response2 = requests.get(f"{BASE_URL}/settings", timeout=10)
        data2 = response2.json()
        
        if len(data2.get("tickerItems")) != 3:
            print_test("SETTINGS: PUT restore tickerItems", False, 
                      "tickerItems restore not persisted")
            return False
        
        print_test("SETTINGS: PUT restore tickerItems", True, 
                  f"Restored tickerItems to 3 items and verified persistence")
        return True
    except Exception as e:
        print_test("SETTINGS: PUT restore tickerItems", False, str(e))
        return False


def test_settings_update_without_auth():
    """Test PUT /api/settings without auth → 401/403"""
    try:
        update_data = {
            "gridColumns": 4
        }
        
        response = requests.put(
            f"{BASE_URL}/settings",
            json=update_data,
            timeout=10
        )
        
        if response.status_code not in [401, 403]:
            print_test("SETTINGS: PUT without auth → 401/403", False, 
                      f"Expected 401/403, got {response.status_code}")
            return False
        
        print_test("SETTINGS: PUT without auth → 401/403", True, 
                  f"Correctly rejected with {response.status_code}")
        return True
    except Exception as e:
        print_test("SETTINGS: PUT without auth → 401/403", False, str(e))
        return False


def test_view_increment():
    """Test POST /api/view"""
    try:
        response = requests.post(f"{BASE_URL}/view", timeout=10)
        
        if response.status_code != 200:
            print_test("VIEWS: POST /api/view", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        print_test("VIEWS: POST /api/view", True, "View recorded")
        return True
    except Exception as e:
        print_test("VIEWS: POST /api/view", False, str(e))
        return False


def test_stats_overview():
    """Test GET /api/stats/overview with auth"""
    if not auth_token:
        print_test("STATS: GET /api/stats/overview", False, "No auth token")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/stats/overview",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("STATS: GET /api/stats/overview", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        
        # Verify numeric fields
        required_fields = ["totalViews", "totalClicks", "activeBanners", "ctr"]
        for field in required_fields:
            if field not in data:
                print_test("STATS: GET /api/stats/overview", False, 
                          f"Missing field: {field}")
                return False
            if not isinstance(data[field], (int, float)):
                print_test("STATS: GET /api/stats/overview", False, 
                          f"Field {field} should be numeric, got {type(data[field])}")
                return False
        
        print_test("STATS: GET /api/stats/overview", True, 
                  f"totalViews={data['totalViews']}, totalClicks={data['totalClicks']}, activeBanners={data['activeBanners']}, ctr={data['ctr']}%")
        return True
    except Exception as e:
        print_test("STATS: GET /api/stats/overview", False, str(e))
        return False


def test_stats_daily():
    """Test GET /api/stats/daily with auth"""
    if not auth_token:
        print_test("STATS: GET /api/stats/daily", False, "No auth token")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/stats/daily",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("STATS: GET /api/stats/daily", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        
        if not isinstance(data, list):
            print_test("STATS: GET /api/stats/daily", False, 
                      f"Expected array, got {type(data)}")
            return False
        
        if len(data) != 14:
            print_test("STATS: GET /api/stats/daily", False, 
                      f"Expected 14 items, got {len(data)}")
            return False
        
        # Verify each item has date, views, clicks
        for i, item in enumerate(data):
            if "date" not in item or "views" not in item or "clicks" not in item:
                print_test("STATS: GET /api/stats/daily", False, 
                          f"Item {i} missing required fields: {item}")
                return False
        
        print_test("STATS: GET /api/stats/daily", True, 
                  f"Returned 14 daily stat items")
        return True
    except Exception as e:
        print_test("STATS: GET /api/stats/daily", False, str(e))
        return False


def test_upload_with_auth():
    """Test POST /api/upload with auth"""
    if not auth_token:
        print_test("UPLOAD: POST with auth", False, "No auth token")
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
            print_test("UPLOAD: POST with auth", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        
        if "url" not in data:
            print_test("UPLOAD: POST with auth", False, 
                      f"Missing 'url' in response: {data}")
            return False
        
        if not data["url"].startswith("data:image"):
            print_test("UPLOAD: POST with auth", False, 
                      f"URL should be base64 data URL, got: {data['url'][:50]}")
            return False
        
        print_test("UPLOAD: POST with auth", True, 
                  f"Returned base64 data URL ({len(data['url'])} chars)")
        return True
    except Exception as e:
        print_test("UPLOAD: POST with auth", False, str(e))
        return False


def test_cleanup_test_banners():
    """Cleanup: Delete test banners"""
    if not auth_token:
        print_test("CLEANUP: Delete test banners", False, "No auth token")
        return False
    
    try:
        deleted_count = 0
        
        # Delete banner with new fields
        if test_banner_with_new_fields_id:
            response = requests.delete(
                f"{BASE_URL}/banners/{test_banner_with_new_fields_id}",
                headers={"Authorization": f"Bearer {auth_token}"},
                timeout=10
            )
            if response.status_code == 200:
                deleted_count += 1
        
        # Delete minimal banner
        if test_banner_minimal_id:
            response = requests.delete(
                f"{BASE_URL}/banners/{test_banner_minimal_id}",
                headers={"Authorization": f"Bearer {auth_token}"},
                timeout=10
            )
            if response.status_code == 200:
                deleted_count += 1
        
        print_test("CLEANUP: Delete test banners", True, 
                  f"Deleted {deleted_count} test banners")
        return True
    except Exception as e:
        print_test("CLEANUP: Delete test banners", False, str(e))
        return False


def run_all_tests():
    """Run all model extension tests"""
    print("=" * 80)
    print("BACKEND MODEL EXTENSION TEST SUITE")
    print("Testing NEW fields: Banner (badge, headline, description, ctaText, accent)")
    print("                    Settings (brandName, headerTitle, headerSubtitle, statusLabel,")
    print("                              tickerItems, footerText, footerDomains)")
    print(f"Base URL: {BASE_URL}")
    print("=" * 80)
    print()
    
    # 1. AUTH
    print("--- 1. AUTH ---")
    test_auth_login()
    test_auth_me()
    test_auth_wrong_password()
    print()
    
    # 2. BANNER CRUD WITH NEW FIELDS
    print("--- 2. BANNER CRUD WITH NEW FIELDS ---")
    test_banner_create_with_new_fields()
    test_banner_get_includes_new_fields()
    test_banner_update_new_field()
    test_banner_create_without_auth()
    test_banner_click()
    print()
    
    # 3. BACKWARD COMPATIBILITY
    print("--- 3. BACKWARD COMPATIBILITY ---")
    test_banner_backward_compatibility()
    print()
    
    # 4. REORDER
    print("--- 4. REORDER ---")
    test_banner_reorder()
    print()
    
    # 5. SETTINGS
    print("--- 5. SETTINGS ---")
    test_settings_get_all_fields()
    test_settings_update_ticker_items()
    test_settings_restore_ticker_items()
    test_settings_update_without_auth()
    print()
    
    # 6. VIEWS & STATS
    print("--- 6. VIEWS & STATS ---")
    test_view_increment()
    test_stats_overview()
    test_stats_daily()
    print()
    
    # 7. UPLOAD
    print("--- 7. UPLOAD ---")
    test_upload_with_auth()
    print()
    
    # CLEANUP
    print("--- CLEANUP ---")
    test_cleanup_test_banners()
    print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    total = passed_tests + failed_tests
    print(f"Passed: {passed_tests}/{total}")
    print(f"Failed: {failed_tests}/{total}")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed_tests} TEST(S) FAILED")
    
    print("=" * 80)
    
    return failed_tests == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
