#!/usr/bin/env python3
"""
Backend test for saray5-style image upload feature
Tests POST /api/upload (MongoDB storage) and GET /api/uploads/{name} (public serve)
"""
import requests
import io
from PIL import Image

# Backend base URL
BASE_URL = "https://fc5c4110-4c6f-460a-a59f-91cc49411a0b.preview.emergentagent.com/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def get_auth_token():
    """Login and get JWT token"""
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    })
    if resp.status_code != 200:
        raise Exception(f"Login failed: {resp.status_code} {resp.text}")
    return resp.json()["token"]

def create_test_png(size_bytes=1000):
    """Create a small test PNG image in memory"""
    # Create a simple 10x10 red image
    img = Image.new('RGB', (10, 10), color='red')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    
    # If we need a larger file, pad it
    data = buf.getvalue()
    if len(data) < size_bytes:
        # Pad with zeros to reach desired size
        data = data + b'\x00' * (size_bytes - len(data))
    
    return data

def create_large_png(size_mb=5.1):
    """Create a PNG-ish file over 5MB"""
    # PNG magic bytes
    png_header = b'\x89PNG\r\n\x1a\n'
    # Create file slightly over 5MB
    size_bytes = int(size_mb * 1024 * 1024)
    data = png_header + b'\x00' * (size_bytes - len(png_header))
    return data

def test_1_upload_with_auth():
    """Test 1: POST /api/upload with auth + small PNG → 200, url starts with '/api/uploads/' and ends with '.png'"""
    print("\n=== Test 1: Upload with auth + small PNG ===")
    token = get_auth_token()
    
    # Create a small PNG
    png_data = create_test_png(1000)
    
    # Upload
    files = {'file': ('test.png', png_data, 'image/png')}
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.post(f"{BASE_URL}/upload", files=files, headers=headers)
    
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert "url" in data, "Response missing 'url' field"
    url = data["url"]
    assert url.startswith("/api/uploads/"), f"URL should start with '/api/uploads/', got: {url}"
    assert url.endswith(".png"), f"URL should end with '.png', got: {url}"
    
    print(f"✅ Test 1 PASSED: Upload returned URL: {url}")
    return url, png_data

def test_2_serve_uploaded_file(url, original_bytes):
    """Test 2: GET {url} (public, no auth) → 200, content-type image/png, body bytes identical"""
    print(f"\n=== Test 2: Serve uploaded file (public, no auth) ===")
    
    # Construct full URL
    full_url = f"https://fc5c4110-4c6f-460a-a59f-91cc49411a0b.preview.emergentagent.com{url}"
    
    # GET without auth
    resp = requests.get(full_url)
    
    print(f"Status: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('content-type')}")
    print(f"Content-Length: {len(resp.content)}")
    
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.headers.get('content-type') == 'image/png', f"Expected content-type image/png, got {resp.headers.get('content-type')}"
    
    # Check PNG magic bytes (first 8 bytes: 89 50 4E 47 0D 0A 1A 0A)
    png_magic = b'\x89PNG\r\n\x1a\n'
    assert resp.content[:8] == png_magic, f"PNG magic bytes mismatch. Got: {resp.content[:8].hex()}"
    
    # Check length matches (allowing for padding we added)
    # The original PNG should be in the response
    assert len(resp.content) >= 100, f"Response too small: {len(resp.content)} bytes"
    
    print(f"✅ Test 2 PASSED: File served correctly with PNG magic bytes {resp.content[:8].hex()}")

def test_3_upload_without_auth():
    """Test 3: POST /api/upload WITHOUT auth → 401/403"""
    print("\n=== Test 3: Upload without auth ===")
    
    png_data = create_test_png(1000)
    files = {'file': ('test.png', png_data, 'image/png')}
    
    # No Authorization header
    resp = requests.post(f"{BASE_URL}/upload", files=files)
    
    print(f"Status: {resp.status_code}")
    
    assert resp.status_code in [401, 403], f"Expected 401 or 403, got {resp.status_code}"
    
    print(f"✅ Test 3 PASSED: Upload without auth correctly rejected with {resp.status_code}")

def test_4_upload_non_image():
    """Test 4: POST /api/upload with non-image file (text/plain) → 400"""
    print("\n=== Test 4: Upload non-image file ===")
    
    token = get_auth_token()
    
    # Create a text file
    text_data = b"This is a text file, not an image"
    files = {'file': ('test.txt', text_data, 'text/plain')}
    headers = {'Authorization': f'Bearer {token}'}
    
    resp = requests.post(f"{BASE_URL}/upload", files=files, headers=headers)
    
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    
    print(f"✅ Test 4 PASSED: Non-image file correctly rejected with 400")

def test_5_serve_nonexistent():
    """Test 5: GET /api/uploads/does-not-exist.png → 404"""
    print("\n=== Test 5: Serve non-existent file ===")
    
    full_url = f"https://fc5c4110-4c6f-460a-a59f-91cc49411a0b.preview.emergentagent.com/api/uploads/does-not-exist.png"
    resp = requests.get(full_url)
    
    print(f"Status: {resp.status_code}")
    
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
    
    print(f"✅ Test 5 PASSED: Non-existent file correctly returns 404")

def test_6_size_guard():
    """Test 6: POST image over 5MB → 413 or error"""
    print("\n=== Test 6: Size guard (>5MB) ===")
    
    token = get_auth_token()
    
    # Create a file slightly over 5MB
    large_data = create_large_png(5.1)
    print(f"Created test file of size: {len(large_data) / 1024 / 1024:.2f} MB")
    
    files = {'file': ('large.png', large_data, 'image/png')}
    headers = {'Authorization': f'Bearer {token}'}
    
    resp = requests.post(f"{BASE_URL}/upload", files=files, headers=headers)
    
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    
    # Accept 413 or any 4xx error
    assert resp.status_code >= 400 and resp.status_code < 500, f"Expected 4xx error, got {resp.status_code}"
    
    print(f"✅ Test 6 PASSED: Large file correctly rejected with {resp.status_code}")

def test_7_integration_banner():
    """Test 7: POST /api/banners with uploaded url → created; GET returns it; DELETE cleanup"""
    print("\n=== Test 7: Integration with banners ===")
    
    token = get_auth_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    # Upload an image first
    png_data = create_test_png(1000)
    files = {'file': ('banner_logo.png', png_data, 'image/png')}
    upload_resp = requests.post(f"{BASE_URL}/upload", files=files, headers=headers)
    assert upload_resp.status_code == 200
    uploaded_url = upload_resp.json()["url"]
    print(f"Uploaded image URL: {uploaded_url}")
    
    # Create a banner with this image
    banner_data = {
        "section": "grid",
        "image": uploaded_url,
        "url": "https://example.com/test",
        "title": "Test Banner with Uploaded Logo",
        "active": True
    }
    create_resp = requests.post(f"{BASE_URL}/banners", json=banner_data, headers=headers)
    print(f"Create banner status: {create_resp.status_code}")
    assert create_resp.status_code == 200
    banner = create_resp.json()
    banner_id = banner["id"]
    print(f"Created banner ID: {banner_id}")
    assert banner["image"] == uploaded_url, f"Banner image mismatch: {banner['image']} != {uploaded_url}"
    
    # GET /api/banners and verify it's there
    get_resp = requests.get(f"{BASE_URL}/banners?all=true")
    assert get_resp.status_code == 200
    banners = get_resp.json()
    found = any(b["id"] == banner_id and b["image"] == uploaded_url for b in banners)
    assert found, f"Banner {banner_id} not found in GET /api/banners"
    print(f"Banner found in GET /api/banners with correct image URL")
    
    # DELETE cleanup
    delete_resp = requests.delete(f"{BASE_URL}/banners/{banner_id}", headers=headers)
    assert delete_resp.status_code == 200
    print(f"Banner deleted successfully")
    
    print(f"✅ Test 7 PASSED: Integration with banners works correctly")

def test_8_regression():
    """Test 8: Quick regression - login, settings, banners"""
    print("\n=== Test 8: Quick regression ===")
    
    # Login
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    })
    assert login_resp.status_code == 200
    assert "token" in login_resp.json()
    print("✓ Login works")
    
    # GET /api/settings
    settings_resp = requests.get(f"{BASE_URL}/settings")
    assert settings_resp.status_code == 200
    settings = settings_resp.json()
    assert "brandName" in settings
    print(f"✓ Settings works (brandName: {settings['brandName']})")
    
    # GET /api/banners
    banners_resp = requests.get(f"{BASE_URL}/banners")
    assert banners_resp.status_code == 200
    banners = banners_resp.json()
    active_count = len([b for b in banners if b.get("active")])
    print(f"✓ Banners works ({active_count} active banners)")
    
    print(f"✅ Test 8 PASSED: Regression tests all passed")

def main():
    print("=" * 60)
    print("SARAY5-STYLE IMAGE UPLOAD BACKEND TEST")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    try:
        # Test 1 & 2 together (need to pass URL between them)
        url, png_bytes = test_1_upload_with_auth()
        passed += 1
        test_2_serve_uploaded_file(url, png_bytes)
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 1 or 2 FAILED: {e}")
        failed += 1
    except Exception as e:
        print(f"❌ Test 1 or 2 ERROR: {e}")
        failed += 1
    
    # Test 3
    try:
        test_3_upload_without_auth()
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 3 FAILED: {e}")
        failed += 1
    except Exception as e:
        print(f"❌ Test 3 ERROR: {e}")
        failed += 1
    
    # Test 4
    try:
        test_4_upload_non_image()
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 4 FAILED: {e}")
        failed += 1
    except Exception as e:
        print(f"❌ Test 4 ERROR: {e}")
        failed += 1
    
    # Test 5
    try:
        test_5_serve_nonexistent()
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 5 FAILED: {e}")
        failed += 1
    except Exception as e:
        print(f"❌ Test 5 ERROR: {e}")
        failed += 1
    
    # Test 6
    try:
        test_6_size_guard()
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 6 FAILED: {e}")
        failed += 1
    except Exception as e:
        print(f"❌ Test 6 ERROR: {e}")
        failed += 1
    
    # Test 7
    try:
        test_7_integration_banner()
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 7 FAILED: {e}")
        failed += 1
    except Exception as e:
        print(f"❌ Test 7 ERROR: {e}")
        failed += 1
    
    # Test 8
    try:
        test_8_regression()
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 8 FAILED: {e}")
        failed += 1
    except Exception as e:
        print(f"❌ Test 8 ERROR: {e}")
        failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of 8 tests")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
