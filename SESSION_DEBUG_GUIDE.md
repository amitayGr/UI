# Session Cookie Debugging Guide 🔍

## Run This First!

```powershell
python test_session_flow.py
```

This will test if the API is setting cookies correctly and if `requests.Session()` is storing them.

## What to Look For

### Expected Output (Working):
```
1. Testing /api/session/start
   Response status: 200
   Cookies after request: {'session': 'eyJzZXNzaW9uX2lkIjo...'}
   ✅ Session cookie found

2. Testing /api/questions/first
   Response status: 200
   ✅ SUCCESS! Session cookie is working!
```

### Problem Output (Not Working):
```
1. Testing /api/session/start
   Response status: 200
   Cookies after request: {}
   ❌ No 'session' cookie found!
```

## Common Issues & Fixes

### Issue 1: API Not Setting Cookie

**Symptoms:**
- `test_session_flow.py` shows no cookies after `/session/start`
- Response headers don't include `Set-Cookie`

**Causes:**
1. API server not running
2. Wrong port (should be 17654)
3. API server not configured to set cookies

**Fix:**
```powershell
# Check if API is running
curl http://localhost:17654/api/health

# Check response headers
curl -v http://localhost:17654/api/session/start -X POST
# Look for: Set-Cookie: session=...
```

### Issue 2: Cookie Set But Not Sent

**Symptoms:**
- `test_session_flow.py` shows cookie after `/session/start`
- But `/questions/first` fails with "please start a new session first"

**Causes:**
1. Using different `requests.Session()` instances
2. Thread-local storage issue
3. Cookie being cleared between requests

**Fix - Check api_client.py:**
```python
# Make sure you're using thread-local sessions correctly
@property
def session(self):
    if not hasattr(self._local, 'session'):
        self._local.session = self._create_session()
    return self._local.session
```

**Debug - Add logging:**
```python
# In api_client.py, add to each method:
logger.info(f"Session object ID: {id(self.session)}")
logger.info(f"Cookies: {dict(self.session.cookies)}")
```

If the session object ID changes between calls, you have a problem!

### Issue 3: Session Lost Between Flask Requests

**Symptoms:**
- First request works
- Second request (e.g., submit answer) fails

**Causes:**
- New thread = new thread-local = new session object = no cookies

**Fix - This is the ACTUAL problem!**

The issue is that Flask uses different threads for different requests. Each thread gets its own `thread-local` storage, so the cookies from the first request don't carry over!

**Solution: Store session in Flask session, not thread-local!**

Let me create the proper fix:
