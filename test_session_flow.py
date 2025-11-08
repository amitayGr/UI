"""
test_session_flow.py
-------------------
Diagnostic script to test API session management and cookie handling.
Run this to see exactly what's happening with cookies.
"""

import requests
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:17654/api"

print("=" * 70)
print("API SESSION FLOW DIAGNOSTIC TEST")
print("=" * 70)

# Create a session (like api_client does)
session = requests.Session()

print("\n1. Testing /api/session/start")
print("-" * 70)

# Start session
try:
    print(f"   Making POST request to {BASE_URL}/session/start")
    print(f"   Cookies before request: {dict(session.cookies)}")
    
    response = session.post(f"{BASE_URL}/session/start", timeout=5)
    
    print(f"   Response status: {response.status_code}")
    print(f"   Response headers:")
    for header, value in response.headers.items():
        print(f"      {header}: {value}")
    
    print(f"   Response JSON: {response.json()}")
    print(f"   Cookies after request: {dict(session.cookies)}")
    
    # Check for session cookie specifically
    if 'session' in session.cookies:
        print(f"   ✅ Session cookie found: {session.cookies['session'][:50]}...")
    else:
        print(f"   ❌ No 'session' cookie found!")
        print(f"   Available cookies: {list(session.cookies.keys())}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print("\n2. Testing /api/questions/first (should use session cookie)")
print("-" * 70)

# Get first question
try:
    print(f"   Making GET request to {BASE_URL}/questions/first")
    print(f"   Cookies being sent: {dict(session.cookies)}")
    
    response = session.get(f"{BASE_URL}/questions/first", timeout=5)
    
    print(f"   Response status: {response.status_code}")
    print(f"   Response JSON: {response.json()}")
    
    if response.status_code == 200:
        print(f"   ✅ SUCCESS! Session cookie is working!")
    else:
        print(f"   ❌ FAILED! Got status {response.status_code}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    print(f"   This means the session cookie is NOT being recognized by the API")

print("\n3. Testing /api/session/status")
print("-" * 70)

# Check session status
try:
    print(f"   Making GET request to {BASE_URL}/session/status")
    print(f"   Cookies being sent: {dict(session.cookies)}")
    
    response = session.get(f"{BASE_URL}/session/status", timeout=5)
    
    print(f"   Response status: {response.status_code}")
    print(f"   Response JSON: {response.json()}")
    
    status_data = response.json()
    if status_data.get('active'):
        print(f"   ✅ Session is active!")
        print(f"   Session ID: {status_data.get('session_id')}")
    else:
        print(f"   ❌ Session is NOT active!")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n4. Testing with a NEW session object (should fail)")
print("-" * 70)

# Create a new session without cookies
new_session = requests.Session()

try:
    print(f"   Making GET request to {BASE_URL}/questions/first with NEW session")
    print(f"   Cookies being sent: {dict(new_session.cookies)}")
    
    response = new_session.get(f"{BASE_URL}/questions/first", timeout=5)
    
    print(f"   Response status: {response.status_code}")
    print(f"   Response JSON: {response.json()}")
    
    if response.status_code != 200:
        print(f"   ✅ EXPECTED! New session without cookies should fail")
    else:
        print(f"   ❌ UNEXPECTED! Should have required session cookie")
    
except Exception as e:
    print(f"   ✅ EXPECTED! Error: {e}")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)

print("\n📋 ANALYSIS:")
print("-" * 70)

if 'session' in session.cookies:
    print("✅ Session cookie is being set by the API")
    print("✅ requests.Session() is storing the cookie")
    print("\n🔍 If you're still getting 'please start a new session first', check:")
    print("   1. Are you using the SAME api_client instance?")
    print("   2. Is thread-local storage working correctly?")
    print("   3. Is the session being cleared somewhere?")
else:
    print("❌ Session cookie is NOT being set by the API")
    print("\n🔍 Possible issues:")
    print("   1. API server is not running on localhost:17654")
    print("   2. API is not setting the session cookie correctly")
    print("   3. Cookie is being blocked (check SameSite/Secure settings)")

print("\n💡 Next steps:")
print("   - Check the logs above for cookie details")
print("   - Compare with your Flask app's api_client logs")
print("   - Verify both are using the same requests.Session() instance")
