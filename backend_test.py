#!/usr/bin/env python3
"""
Backend API test for logoSize setting feature
Tests GET/PUT /api/settings with logoSize field
"""
import requests
import json

BASE_URL = "http://localhost:8001/api"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

def get_auth_token():
    """Login and get JWT token"""
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": ADMIN_USER,
        "password": ADMIN_PASS
    })
    if resp.status_code != 200:
        raise Exception(f"Login failed: {resp.status_code} {resp.text}")
    return resp.json()["token"]

def test_1_get_settings_includes_logosize():
    """Test 1: GET /api/settings (public) includes logoSize field, numeric, currently 64"""
    print("\n=== TEST 1: GET /api/settings includes logoSize ===")
    resp = requests.get(f"{BASE_URL}/settings")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    
    assert "logoSize" in data, "logoSize field missing from response"
    assert isinstance(data["logoSize"], int), f"logoSize should be int, got {type(data['logoSize'])}"
    print(f"✅ logoSize field present: {data['logoSize']} (type: {type(data['logoSize']).__name__})")
    
    # Note: The review request says "currently 64" but we'll report actual value
    if data["logoSize"] == 64:
        print(f"✅ logoSize is 64 as expected")
    else:
        print(f"⚠️  logoSize is {data['logoSize']} (expected 64 per review request)")
    
    return data

def test_2_put_partial_logosize_preserves_fields(token):
    """Test 2: PUT /api/settings with auth and partial body {"logoSize": 100} preserves all other fields"""
    print("\n=== TEST 2: PUT partial logoSize=100, verify all fields intact ===")
    
    # Get current settings first
    resp = requests.get(f"{BASE_URL}/settings")
    before = resp.json()
    print(f"Before PUT: brandName={before.get('brandName')}, gridColumns={before.get('gridColumns')}, tickerItems count={len(before.get('tickerItems', []))}")
    
    # Partial PUT with only logoSize
    resp = requests.put(
        f"{BASE_URL}/settings",
        json={"logoSize": 100},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    
    # Verify logoSize updated
    assert data.get("logoSize") == 100, f"logoSize should be 100, got {data.get('logoSize')}"
    print(f"✅ logoSize updated to 100")
    
    # Verify other fields preserved
    assert data.get("brandName") == before.get("brandName"), f"brandName changed! Was {before.get('brandName')}, now {data.get('brandName')}"
    assert data.get("gridColumns") == before.get("gridColumns"), f"gridColumns changed! Was {before.get('gridColumns')}, now {data.get('gridColumns')}"
    assert len(data.get("tickerItems", [])) == len(before.get("tickerItems", [])), f"tickerItems count changed!"
    
    print(f"✅ All other fields preserved: brandName={data.get('brandName')}, gridColumns={data.get('gridColumns')}, tickerItems count={len(data.get('tickerItems', []))}")
    
    # Verify specific values mentioned in review request
    if data.get("brandName") == "EMRE18":
        print(f"✅ brandName='EMRE18' confirmed")
    else:
        print(f"⚠️  brandName is '{data.get('brandName')}' (review request expected 'EMRE18')")
    
    if data.get("gridColumns") == 3:
        print(f"✅ gridColumns=3 confirmed")
    else:
        print(f"⚠️  gridColumns is {data.get('gridColumns')} (review request expected 3)")
    
    if len(data.get("tickerItems", [])) == 3:
        print(f"✅ tickerItems has 3 items confirmed")
    else:
        print(f"⚠️  tickerItems has {len(data.get('tickerItems', []))} items (review request expected 3)")
    
    return data

def test_3_get_settings_persisted():
    """Test 3: GET /api/settings again, verify logoSize=100 persisted"""
    print("\n=== TEST 3: GET /api/settings again, verify persistence ===")
    resp = requests.get(f"{BASE_URL}/settings")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    
    assert data.get("logoSize") == 100, f"logoSize should be 100, got {data.get('logoSize')}"
    print(f"✅ logoSize=100 persisted correctly")
    return data

def test_4_put_without_auth():
    """Test 4: PUT /api/settings without auth with {"logoSize": 50} should return 401/403"""
    print("\n=== TEST 4: PUT without auth should reject ===")
    resp = requests.put(
        f"{BASE_URL}/settings",
        json={"logoSize": 50}
    )
    assert resp.status_code in [401, 403], f"Expected 401 or 403, got {resp.status_code}"
    print(f"✅ PUT without auth correctly rejected with {resp.status_code}")

def test_5_edge_large_value(token):
    """Test 5: PUT {"logoSize": 99999}, verify stored, then restore to 64"""
    print("\n=== TEST 5: Edge case - large value 99999 ===")
    
    # PUT large value
    resp = requests.put(
        f"{BASE_URL}/settings",
        json={"logoSize": 99999},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    
    assert data.get("logoSize") == 99999, f"logoSize should be 99999, got {data.get('logoSize')}"
    print(f"✅ logoSize=99999 stored as-is (no validation)")
    
    # Verify persistence
    resp = requests.get(f"{BASE_URL}/settings")
    data = resp.json()
    assert data.get("logoSize") == 99999, f"logoSize should persist as 99999, got {data.get('logoSize')}"
    print(f"✅ logoSize=99999 persisted")
    
    # Restore to 64
    resp = requests.put(
        f"{BASE_URL}/settings",
        json={"logoSize": 64},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert data.get("logoSize") == 64, f"logoSize should be 64, got {data.get('logoSize')}"
    print(f"✅ logoSize restored to 64")

def test_6_wrong_type(token):
    """Test 6: PUT {"logoSize": "abc"} (wrong type), report behavior, restore to 64"""
    print("\n=== TEST 6: Wrong type - string 'abc' ===")
    
    # PUT wrong type
    resp = requests.put(
        f"{BASE_URL}/settings",
        json={"logoSize": "abc"},
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"PUT response status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        logo_size_value = data.get("logoSize")
        logo_size_type = type(logo_size_value).__name__
        print(f"⚠️  FINDING: Backend accepted string 'abc' and stored it. Response logoSize={repr(logo_size_value)} (type: {logo_size_type})")
        
        # Verify what GET returns
        resp_get = requests.get(f"{BASE_URL}/settings")
        data_get = resp_get.json()
        logo_size_get = data_get.get("logoSize")
        logo_size_get_type = type(logo_size_get).__name__
        print(f"⚠️  FINDING: GET /api/settings returns logoSize={repr(logo_size_get)} (type: {logo_size_get_type})")
        
        if isinstance(logo_size_get, str):
            print(f"❌ CRITICAL FINDING: logoSize is stored and returned as string '{logo_size_get}' instead of int")
        
    elif resp.status_code == 422:
        print(f"✅ Backend correctly rejected wrong type with 422 (Pydantic validation)")
        print(f"Response: {resp.text}")
    else:
        print(f"⚠️  Unexpected status code: {resp.status_code}")
        print(f"Response: {resp.text}")
    
    # Restore to 64
    resp = requests.put(
        f"{BASE_URL}/settings",
        json={"logoSize": 64},
        headers={"Authorization": f"Bearer {token}"}
    )
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ logoSize restored to 64 (type: {type(data.get('logoSize')).__name__})")
    else:
        print(f"⚠️  Failed to restore logoSize to 64: {resp.status_code}")

def test_7_regression(token):
    """Test 7: Regression - auth login, banners, view tracking"""
    print("\n=== TEST 7: Regression tests ===")
    
    # Auth login
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": ADMIN_USER,
        "password": ADMIN_PASS
    })
    assert resp.status_code == 200, f"Login failed: {resp.status_code}"
    assert "token" in resp.json(), "Token missing from login response"
    print(f"✅ POST /api/auth/login works")
    
    # Get banners
    resp = requests.get(f"{BASE_URL}/banners")
    assert resp.status_code == 200, f"GET /api/banners failed: {resp.status_code}"
    banners = resp.json()
    assert isinstance(banners, list), "Banners should be a list"
    active_count = len([b for b in banners if b.get("active")])
    print(f"✅ GET /api/banners returns {len(banners)} banners ({active_count} active)")
    
    if active_count == 5:
        print(f"✅ 5 active banners confirmed (as per review request)")
    else:
        print(f"⚠️  Found {active_count} active banners (review request expected 5)")
    
    # View tracking
    resp = requests.post(f"{BASE_URL}/view")
    assert resp.status_code == 200, f"POST /api/view failed: {resp.status_code}"
    assert resp.json().get("ok") == True, "View tracking should return ok:true"
    print(f"✅ POST /api/view works")

def main():
    print("=" * 60)
    print("BACKEND LOGOSIZE SETTING VERIFICATION")
    print("=" * 60)
    
    try:
        # Get auth token
        print("\n🔐 Getting auth token...")
        token = get_auth_token()
        print(f"✅ Auth token obtained")
        
        # Run all tests
        test_1_get_settings_includes_logosize()
        test_2_put_partial_logosize_preserves_fields(token)
        test_3_get_settings_persisted()
        test_4_put_without_auth()
        test_5_edge_large_value(token)
        test_6_wrong_type(token)
        test_7_regression(token)
        
        # Final state verification
        print("\n" + "=" * 60)
        print("FINAL STATE VERIFICATION")
        print("=" * 60)
        resp = requests.get(f"{BASE_URL}/settings")
        data = resp.json()
        final_logo_size = data.get("logoSize")
        print(f"Final logoSize: {final_logo_size} (type: {type(final_logo_size).__name__})")
        
        if final_logo_size == 64 and isinstance(final_logo_size, int):
            print(f"✅ Final state correct: logoSize=64 (int)")
        else:
            print(f"⚠️  Final state: logoSize={repr(final_logo_size)} (expected 64 as int)")
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
