#!/usr/bin/env python3
"""
health_check.py
---------------
Quick health check script for the Geometry Learning System.
Tests API connectivity, database connections, and critical endpoints.

Usage:
    python health_check.py
"""

from api_client import api_client, check_api_health

print("🏥 System Health Check")
print("=" * 60)

# Check API
print("\n1. Checking API Server Health...")
print("-" * 60)
try:
    if check_api_health():
        print("   ✅ API is healthy and responding")
        try:
            status = api_client.get_session_status()
            print(f"   ℹ️  Active session: {status.get('active', 'N/A')}")
            if status.get('active'):
                session_id = status.get('session_id', 'N/A')
                print(f"   ℹ️  Session ID: {session_id}")
        except Exception as e:
            print(f"   ⚠️  Could not get session status: {str(e)}")
    else:
        print("   ❌ API is not healthy")
except Exception as e:
    print(f"   ❌ API Health Check Failed: {str(e)}")
    print(f"   ℹ️  Make sure the API server is running on http://localhost:17654")

# Check Database
print("\n2. Checking User Database Connection...")
print("-" * 60)
try:
    from db_utils import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Users")
    user_count = cursor.fetchone()[0]
    print(f"   ✅ Database connection successful")
    print(f"   ℹ️  Total users in database: {user_count}")
    conn.close()
except Exception as e:
    print(f"   ❌ Database Connection Failed: {str(e)}")
    print(f"   ℹ️  Check db_config.py settings")

# Check Critical Endpoints
print("\n3. Testing Critical API Endpoints...")
print("-" * 60)

endpoints = [
    ("Health Check", "/health", "GET", None),
    ("Session Start", "/session/start", "POST", {}),
    ("Answer Options", "/answers/options", "GET", None),
    ("Triangle Types", "/db/triangles", "GET", None),
]

test_session_started = False

for name, endpoint, method, payload in endpoints:
    try:
        url = f"{api_client.base_url}{endpoint}"
        
        if method == "GET":
            response = api_client.session.get(url, timeout=5)
        else:
            response = api_client.session.post(url, json=payload if payload else {}, timeout=5)
        
        if response.status_code == 200:
            print(f"   ✅ {name}: HTTP {response.status_code}")
            
            # Track if we started a session for cleanup
            if name == "Session Start":
                test_session_started = True
                
        elif response.status_code == 400:
            print(f"   ⚠️  {name}: HTTP {response.status_code} (Bad Request - may need active session)")
        else:
            print(f"   ⚠️  {name}: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ {name}: {str(e)}")

# Clean up test session
if test_session_started:
    try:
        api_client.end_session(save_to_db=False)
        print(f"   ℹ️  Test session cleaned up")
    except:
        pass

# Check Flask Session Directory
print("\n4. Checking Flask Session Storage...")
print("-" * 60)
try:
    import os
    session_dir = os.path.join(os.path.dirname(__file__), 'flask_session')
    if os.path.exists(session_dir):
        session_files = [f for f in os.listdir(session_dir) if not f.startswith('.')]
        print(f"   ✅ Flask session directory exists")
        print(f"   ℹ️  Active session files: {len(session_files)}")
    else:
        print(f"   ⚠️  Flask session directory not found (will be created on first use)")
except Exception as e:
    print(f"   ⚠️  Could not check session directory: {str(e)}")

# Summary
print("\n" + "=" * 60)
print("📊 Health Check Summary")
print("=" * 60)
print("\n✅ = Working correctly")
print("⚠️  = Warning or minor issue")
print("❌ = Critical issue")
print("\nℹ️  For detailed troubleshooting, see TROUBLESHOOTING.md")
print("\n" + "=" * 60)
