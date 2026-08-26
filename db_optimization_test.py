#!/usr/bin/env python3
"""
DB Optimization Regression Test
Tests endpoints affected by DB query optimizations (projections + bulk_write reorder)
"""
import requests
import json

# Backend base URL from frontend/.env
BASE_URL = "https://column-ads-hub.preview.emergentagent.com/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Global storage
auth_token = None
test_banner_id = None


def print_step(step_num, description, passed, details=""):
    """Print test step result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\nStep {step_num}: {description}")
    print(f"  {status}")
    if details:
        print(f"  Details: {details}")


def step1_login():
    """Step 1: POST /api/auth/login with admin/admin123"""
    global auth_token
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            timeout=10
        )
        
        if response.status_code != 200:
            print_step(1, "Login with admin/admin123", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        if "token" not in data:
            print_step(1, "Login with admin/admin123", False, 
                      f"Missing token in response: {data}")
            return False
        
        auth_token = data["token"]
        print_step(1, "Login with admin/admin123", True, 
                  f"Token received: {auth_token[:30]}...")
        return True
    except Exception as e:
        print_step(1, "Login with admin/admin123", False, str(e))
        return False


def step2_get_all_banners():
    """Step 2: GET /api/banners?all=true with Bearer token"""
    if not auth_token:
        print_step(2, "GET /api/banners?all=true", False, "No auth token")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/banners?all=true",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_step(2, "GET /api/banners?all=true", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        banners = response.json()
        if not isinstance(banners, list):
            print_step(2, "GET /api/banners?all=true", False, 
                      f"Expected list, got {type(banners)}")
            return False
        
        print_step(2, "GET /api/banners?all=true", True, 
                  f"Returned {len(banners)} banners")
        return True
    except Exception as e:
        print_step(2, "GET /api/banners?all=true", False, str(e))
        return False


def step3_create_banner():
    """Step 3: POST /api/banners to create test banner"""
    global test_banner_id
    
    if not auth_token:
        print_step(3, "POST /api/banners (create)", False, "No auth token")
        return False
    
    try:
        banner_data = {
            "section": "grid",
            "image": "https://kara8.com/uploads/bonus_cards/test.jpg",
            "url": "https://example.com/test-target",
            "title": "DB Optimization Test Banner",
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
            print_step(3, "POST /api/banners (create)", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        if "id" not in data:
            print_step(3, "POST /api/banners (create)", False, 
                      f"Missing 'id' in response: {data}")
            return False
        
        test_banner_id = data["id"]
        print_step(3, "POST /api/banners (create)", True, 
                  f"Created banner with id: {test_banner_id}")
        return True
    except Exception as e:
        print_step(3, "POST /api/banners (create)", False, str(e))
        return False


def step4_reorder_banners():
    """Step 4: POST /api/banners/reorder and verify order persistence via bulk_write"""
    if not auth_token:
        print_step(4, "POST /api/banners/reorder + verify", False, "No auth token")
        return False
    
    try:
        # Get all current banners
        response = requests.get(
            f"{BASE_URL}/banners?all=true",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_step(4, "POST /api/banners/reorder + verify", False, 
                      f"Failed to get banners: {response.status_code}")
            return False
        
        banners = response.json()
        original_ids = [b["id"] for b in banners]
        
        # Reverse the order
        reversed_ids = list(reversed(original_ids))
        
        # Reorder using bulk_write
        response = requests.post(
            f"{BASE_URL}/banners/reorder",
            json={"ids": reversed_ids},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_step(4, "POST /api/banners/reorder + verify", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        # Verify order fields now reflect the new sequence
        response = requests.get(
            f"{BASE_URL}/banners?all=true",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        banners = response.json()
        
        # Check that order fields are 0..n matching the reversed id list
        for i, banner in enumerate(banners):
            expected_id = reversed_ids[i]
            expected_order = i
            
            if banner["id"] != expected_id:
                print_step(4, "POST /api/banners/reorder + verify", False, 
                          f"Banner at position {i}: expected id {expected_id}, got {banner['id']}")
                return False
            
            if banner["order"] != expected_order:
                print_step(4, "POST /api/banners/reorder + verify", False, 
                          f"Banner {banner['id']}: expected order {expected_order}, got {banner['order']}")
                return False
        
        # Restore original order
        requests.post(
            f"{BASE_URL}/banners/reorder",
            json={"ids": original_ids},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        print_step(4, "POST /api/banners/reorder + verify", True, 
                  f"Reordered {len(banners)} banners, order fields correctly persist (0..{len(banners)-1})")
        return True
    except Exception as e:
        print_step(4, "POST /api/banners/reorder + verify", False, str(e))
        return False


def step5_stats_overview():
    """Step 5: GET /api/stats/overview with projections optimization"""
    if not auth_token:
        print_step(5, "GET /api/stats/overview", False, "No auth token")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/stats/overview",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_step(5, "GET /api/stats/overview", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        
        # Verify all required fields present and numeric
        required_fields = ["totalViews", "totalClicks", "activeBanners", "ctr"]
        for field in required_fields:
            if field not in data:
                print_step(5, "GET /api/stats/overview", False, 
                          f"Missing required field: {field}")
                return False
            
            if not isinstance(data[field], (int, float)):
                print_step(5, "GET /api/stats/overview", False, 
                          f"Field {field} is not numeric: {type(data[field])}")
                return False
        
        print_step(5, "GET /api/stats/overview", True, 
                  f"totalViews={data['totalViews']}, totalClicks={data['totalClicks']}, activeBanners={data['activeBanners']}, ctr={data['ctr']}%")
        return True
    except Exception as e:
        print_step(5, "GET /api/stats/overview", False, str(e))
        return False


def step6_click_banner():
    """Step 6: POST /api/banners/{id}/click (public) and verify increment"""
    if not test_banner_id:
        print_step(6, "POST /api/banners/{id}/click", False, "No test banner id")
        return False
    
    try:
        # Get current clicks
        response = requests.get(f"{BASE_URL}/banners?all=true", timeout=10)
        banners = response.json()
        test_banner = next((b for b in banners if b["id"] == test_banner_id), None)
        
        if not test_banner:
            print_step(6, "POST /api/banners/{id}/click", False, 
                      "Test banner not found")
            return False
        
        initial_clicks = test_banner.get("clicks", 0)
        
        # Click the banner (public endpoint)
        response = requests.post(
            f"{BASE_URL}/banners/{test_banner_id}/click",
            timeout=10
        )
        
        if response.status_code != 200:
            print_step(6, "POST /api/banners/{id}/click", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        # Verify clicks incremented
        response = requests.get(f"{BASE_URL}/banners?all=true", timeout=10)
        banners = response.json()
        test_banner = next((b for b in banners if b["id"] == test_banner_id), None)
        new_clicks = test_banner.get("clicks", 0)
        
        if new_clicks != initial_clicks + 1:
            print_step(6, "POST /api/banners/{id}/click", False, 
                      f"Clicks not incremented: expected {initial_clicks + 1}, got {new_clicks}")
            return False
        
        print_step(6, "POST /api/banners/{id}/click", True, 
                  f"Clicks incremented from {initial_clicks} to {new_clicks}")
        return True
    except Exception as e:
        print_step(6, "POST /api/banners/{id}/click", False, str(e))
        return False


def step7_delete_banner():
    """Step 7: DELETE /api/banners/{id} cleanup"""
    if not auth_token:
        print_step(7, "DELETE /api/banners/{id}", False, "No auth token")
        return False
    
    if not test_banner_id:
        print_step(7, "DELETE /api/banners/{id}", False, "No test banner id")
        return False
    
    try:
        response = requests.delete(
            f"{BASE_URL}/banners/{test_banner_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            print_step(7, "DELETE /api/banners/{id}", False, 
                      f"Expected 200, got {response.status_code}: {response.text}")
            return False
        
        # Verify banner removed
        response = requests.get(f"{BASE_URL}/banners?all=true", timeout=10)
        banners = response.json()
        if any(b["id"] == test_banner_id for b in banners):
            print_step(7, "DELETE /api/banners/{id}", False, 
                      "Banner still exists after deletion")
            return False
        
        print_step(7, "DELETE /api/banners/{id}", True, 
                  f"Successfully deleted banner {test_banner_id}")
        return True
    except Exception as e:
        print_step(7, "DELETE /api/banners/{id}", False, str(e))
        return False


def step8_verify_auth_protection():
    """Step 8: Verify auth-protected endpoints return 401/403 without token"""
    try:
        endpoints = [
            ("GET", f"{BASE_URL}/auth/me"),
            ("POST", f"{BASE_URL}/banners"),
            ("PUT", f"{BASE_URL}/banners/test-id"),
            ("DELETE", f"{BASE_URL}/banners/test-id"),
            ("POST", f"{BASE_URL}/banners/reorder"),
            ("GET", f"{BASE_URL}/stats/overview"),
            ("GET", f"{BASE_URL}/stats/daily"),
            ("PUT", f"{BASE_URL}/settings"),
            ("POST", f"{BASE_URL}/upload"),
        ]
        
        failed = []
        for method, url in endpoints:
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json={}, timeout=10)
            elif method == "PUT":
                response = requests.put(url, json={}, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, timeout=10)
            
            if response.status_code not in [401, 403]:
                failed.append(f"{method} {url} returned {response.status_code} (expected 401/403)")
        
        if failed:
            print_step(8, "Verify auth protection", False, 
                      f"{len(failed)} endpoints not properly protected: {', '.join(failed)}")
            return False
        
        print_step(8, "Verify auth protection", True, 
                  f"All {len(endpoints)} protected endpoints correctly return 401/403 without token")
        return True
    except Exception as e:
        print_step(8, "Verify auth protection", False, str(e))
        return False


def run_optimization_tests():
    """Run all DB optimization regression tests"""
    print("=" * 80)
    print("DB OPTIMIZATION REGRESSION TEST")
    print("Testing endpoints affected by projections + bulk_write optimizations")
    print(f"Base URL: {BASE_URL}")
    print("=" * 80)
    
    results = []
    
    # Run all steps in sequence
    results.append(("Step 1: Login", step1_login()))
    results.append(("Step 2: GET all banners", step2_get_all_banners()))
    results.append(("Step 3: Create banner", step3_create_banner()))
    results.append(("Step 4: Reorder + verify", step4_reorder_banners()))
    results.append(("Step 5: Stats overview", step5_stats_overview()))
    results.append(("Step 6: Click banner", step6_click_banner()))
    results.append(("Step 7: Delete banner", step7_delete_banner()))
    results.append(("Step 8: Auth protection", step8_verify_auth_protection()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\nPassed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL DB OPTIMIZATION TESTS PASSED!")
        print("Confirmed: projections + bulk_write reorder working correctly")
    else:
        print("\n⚠️  SOME TESTS FAILED")
    
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    success = run_optimization_tests()
    exit(0 if success else 1)
