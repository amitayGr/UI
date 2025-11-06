# 🔧 Troubleshooting Guide - API Integration Issues

This guide covers common issues you might encounter with the API integration and their solutions.

---

## 🚨 SQLite Threading Error

### Error Message:
```
SQLite objects created in a thread can only be used in that same thread. 
The object was created in thread id XXXXX and this is thread id YYYYY.
```

### Cause:
Flask runs in multi-threaded mode by default, and SQLite connections are not thread-safe. When the API server uses SQLite, it can cause threading conflicts when multiple requests come from the UI.

### Solutions Implemented:

#### 1. **Thread-Local Sessions in API Client** ✅
The `api_client.py` has been updated to use thread-local storage:

```python
# Each thread gets its own requests.Session object
self._local = threading.local()

@property
def session(self):
    """Get or create a thread-local requests session."""
    if not hasattr(self._local, 'session'):
        self._local.session = requests.Session()
    return self._local.session
```

This ensures that each Flask request thread has its own isolated HTTP session.

#### 2. **API Server Should Use Thread-Local SQLite Connections**

The API server (on port 17654) should also implement thread-local database connections. Ensure your API server has code like this:

```python
import threading

class GeometryDatabase:
    def __init__(self):
        self._local = threading.local()
    
    @property
    def connection(self):
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect('database.db', check_same_thread=False)
        return self._local.conn
```

#### 3. **Alternative: Run Flask in Single-Threaded Mode**

If the problem persists, you can run Flask in single-threaded mode (not recommended for production):

**In `app.py`:**
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, threaded=False)
```

**Or in launch.json:**
```json
"args": [
    "run",
    "--host=0.0.0.0",
    "--port=10000",
    "--no-reload",
    "--without-threads"
]
```

#### 4. **API Server Configuration**

If you control the API server, consider using connection pooling or switching to a thread-safe database like PostgreSQL for production.

---

## 🔌 API Connection Issues

### Error: "Cannot connect to API server"

#### Symptoms:
- Validation script fails
- Questions don't load
- Error messages about localhost:17654

#### Solutions:

1. **Verify API Server is Running**
   ```powershell
   # Test connectivity
   curl http://localhost:17654/api/health
   
   # Or in PowerShell
   Invoke-WebRequest -Uri "http://localhost:17654/api/health"
   ```

2. **Check Port Availability**
   ```powershell
   # Check if port 17654 is in use
   netstat -an | findstr "17654"
   ```

3. **Check Firewall Settings**
   - Ensure Windows Firewall allows connections to port 17654
   - Add an inbound rule for port 17654 if needed

4. **Verify API Server Configuration**
   - Check that API server is configured to listen on `0.0.0.0:17654` or `localhost:17654`
   - Review API server logs for startup errors

5. **Test with Different Base URL**
   
   Try changing in `api_client.py`:
   ```python
   self.base_url = "http://127.0.0.1:17654/api"  # Instead of localhost
   ```

---

## 🔐 Session Management Issues

### Error: "No active session found"

#### Cause:
API sessions expire or are not properly initialized.

#### Solutions:

1. **Auto-Session Creation**
   The UI automatically creates sessions, but you can manually test:
   ```python
   from api_client import api_client
   result = api_client.start_session()
   print(result)
   ```

2. **Check Session Timeout**
   API sessions may timeout after inactivity. The UI handles this by creating new sessions automatically.

3. **Clear Browser Cookies**
   Sometimes stale session cookies can cause issues:
   - Clear browser cache and cookies
   - Try in incognito/private browsing mode

---

## 📊 Data Format Issues

### Error: "Invalid JSON response"

#### Cause:
API returns unexpected data format or non-JSON response.

#### Solutions:

1. **Check API Response Format**
   ```powershell
   # Test API response
   curl http://localhost:17654/api/questions/first
   ```

2. **Verify API Version Compatibility**
   - Ensure API server matches the expected version
   - Check `API_DOCUMENTATION.md` for endpoint specifications

3. **Review API Server Logs**
   - Check for errors on the API server side
   - Look for database or configuration issues

---

## 🐛 Database Connection Issues

### Error: Database connection failed

#### For User Authentication (Local Database):

1. **Check `db_config.py`**
   ```python
   DB_CONFIG = {
       'driver': 'SQL Server',
       'server': 'YOUR_SERVER_NAME',  # Update this
       'database': 'YOUR_DATABASE_NAME',  # Update this
       'trusted_connection': 'yes'
   }
   ```

2. **Verify SQL Server is Running**
   - Open SQL Server Management Studio
   - Test connection to your server
   - Ensure Windows Authentication is enabled

3. **Check ODBC Driver**
   ```powershell
   # List available ODBC drivers
   Get-OdbcDriver
   ```

4. **Test Database Connection**
   ```python
   from db_utils import get_db_connection
   try:
       conn = get_db_connection()
       print("Database connection successful!")
       conn.close()
   except Exception as e:
       print(f"Connection failed: {e}")
   ```

---

## 🔄 Session State Issues

### Problem: Weights not updating / Questions repeating

#### Solutions:

1. **Clear Flask Session**
   - Delete files in `flask_session/` directory
   - Restart the server

2. **Reset API Session**
   ```python
   from api_client import api_client
   api_client.reset_session()
   ```

3. **Check API Session Status**
   ```python
   from api_client import api_client
   status = api_client.get_session_status()
   print(status)
   ```

---

## ⚡ Performance Issues

### Problem: Slow response times

#### Solutions:

1. **Enable Request Pooling**
   The API client already uses session pooling, but you can tune it:
   ```python
   # In api_client.py, add connection pooling
   from requests.adapters import HTTPAdapter
   from requests.packages.urllib3.util.retry import Retry
   
   adapter = HTTPAdapter(
       pool_connections=10,
       pool_maxsize=20,
       max_retries=Retry(total=3, backoff_factor=0.3)
   )
   self.session.mount('http://', adapter)
   ```

2. **Check Network Latency**
   ```powershell
   # Test response time
   Measure-Command { 
       Invoke-WebRequest -Uri "http://localhost:17654/api/health" 
   }
   ```

3. **Monitor API Server Load**
   - Check API server CPU and memory usage
   - Look for database query performance issues

---

## 🔒 CORS Issues (if using different domains)

### Error: "CORS policy blocked"

#### Solution:

If you're running UI and API on different domains, ensure the API server has CORS enabled:

```python
# In API server
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:10000"])
```

---

## 🔍 Debugging Tips

### Enable Detailed Logging

1. **In `api_client.py`:**
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **In Flask app:**
   ```python
   app.config['DEBUG'] = True
   ```

3. **View Request/Response Details:**
   ```python
   import requests
   import logging
   
   logging.basicConfig(level=logging.DEBUG)
   logging.getLogger('requests').setLevel(logging.DEBUG)
   logging.getLogger('urllib3').setLevel(logging.DEBUG)
   ```

### Test Individual API Endpoints

Create a test script:

```python
from api_client import api_client

# Test health
print("Health:", api_client.health_check())

# Test session
print("Start:", api_client.start_session())
print("Status:", api_client.get_session_status())

# Test question
print("First Q:", api_client.get_first_question())
```

---

## 📝 Common Error Messages Reference

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| `Connection refused` | API server not running | Start API server on port 17654 |
| `Timeout` | Network/firewall issue | Check firewall, increase timeout |
| `404 Not Found` | Wrong endpoint URL | Verify API_DOCUMENTATION.md |
| `400 Bad Request` | Invalid request data | Check request payload format |
| `500 Internal Server Error` | API server error | Check API server logs |
| `SQLite threading error` | Thread-safety issue | Use thread-local sessions (already fixed) |
| `No active session` | Session expired | UI auto-creates, check API server |
| `Invalid JSON` | API response format issue | Verify API response with curl |

---

## 🆘 Emergency Fixes

### Complete Reset

If all else fails, perform a complete reset:

1. **Stop all servers**
2. **Clear sessions:**
   ```powershell
   Remove-Item -Path "flask_session\*" -Force
   ```
3. **Reset virtual environment:**
   ```powershell
   Remove-Item -Path "venv" -Recurse -Force
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
4. **Restart API server**
5. **Run validation:**
   ```powershell
   python validate_api_integration.py
   ```
6. **Restart UI server**

---

## 📞 Getting Help

### Information to Gather

When seeking help, collect:

1. **Error message** (full stack trace)
2. **Steps to reproduce** the issue
3. **Environment details:**
   - Python version: `python --version`
   - Flask version: `pip show flask`
   - OS version: `systeminfo | findstr /C:"OS"`
4. **API server logs**
5. **UI server logs** (Debug Console output)
6. **Validation script output**

### Log Locations

- **Flask Debug Console**: VS Code Debug Console
- **API Client Logs**: Check console output
- **UserLogger**: Check UserLogger.py for log file location
- **Flask Session**: `flask_session/` directory

---

## ✅ Health Check Script

Create `health_check.py`:

```python
#!/usr/bin/env python3
"""Quick health check for the integrated system."""

from api_client import api_client, check_api_health
from db_utils import get_db_connection

print("🏥 System Health Check")
print("=" * 50)

# Check API
print("\n1. API Server Health:")
try:
    if check_api_health():
        print("   ✅ API is healthy")
        status = api_client.get_session_status()
        print(f"   ✅ Active sessions: {status.get('active', 'N/A')}")
    else:
        print("   ❌ API is not healthy")
except Exception as e:
    print(f"   ❌ API Error: {str(e)}")

# Check Database
print("\n2. User Database:")
try:
    conn = get_db_connection()
    print("   ✅ Database connection successful")
    conn.close()
except Exception as e:
    print(f"   ❌ Database Error: {str(e)}")

# Check Endpoints
print("\n3. Critical Endpoints:")
endpoints = [
    ("Health", "/health", "GET"),
    ("Session Start", "/session/start", "POST"),
    ("First Question", "/questions/first", "GET"),
]

for name, endpoint, method in endpoints:
    try:
        url = f"{api_client.base_url}{endpoint}"
        if method == "GET":
            response = api_client.session.get(url, timeout=5)
        else:
            response = api_client.session.post(url, json={}, timeout=5)
        
        status = "✅" if response.status_code == 200 else "⚠️"
        print(f"   {status} {name}: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ {name}: {str(e)}")

print("\n" + "=" * 50)
print("Health check complete!")
```

Run with: `python health_check.py`

---

**Last Updated:** November 6, 2025  
**Issue Tracking:** See `API_INTEGRATION_SUMMARY.md` for known issues and updates
