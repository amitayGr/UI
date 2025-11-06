# 🚀 Quick Start Guide - Running the Flask UI Server in VS Code

This guide will help you run the Geometry Learning System UI server in Visual Studio Code.

---

## 📋 Prerequisites

Before you start, make sure you have:

1. **Python 3.8+** installed on your system
2. **Visual Studio Code** installed
3. **Python Extension for VS Code** installed ([Install here](https://marketplace.visualstudio.com/items?itemName=ms-python.python))
4. **The API Server** running on `http://localhost:17654` (required for geometry learning features)

---

## 🔧 Setup Instructions

### Step 1: Open the Project in VS Code

1. Open VS Code
2. Go to `File` → `Open Folder`
3. Select the `UI` folder: `c:\Users\lahavor\am\UI`

### Step 2: Set Up Python Environment

#### Option A: Using the Existing Virtual Environment

If you have the `uivenv` folder:

1. Open VS Code Command Palette (`Ctrl+Shift+P` or `F1`)
2. Type: `Python: Select Interpreter`
3. Choose the interpreter from: `.\uivenv\Scripts\python.exe`

#### Option B: Create a New Virtual Environment

1. Open the integrated terminal in VS Code (`Ctrl+`` or View → Terminal)
2. Create a new virtual environment:
   ```powershell
   python -m venv venv
   ```
3. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   
   > **Note:** If you get an execution policy error, run:
   > ```powershell
   > Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   > ```

### Step 3: Install Dependencies

With the virtual environment activated, install all required packages:

```powershell
pip install -r requirements.txt
```

This will install Flask, requests, and all other necessary dependencies.

### Step 4: Configure Database Connection

Make sure your `db_config.py` is properly configured with your database connection details:

```python
DB_CONFIG = {
    'driver': 'SQL Server',
    'server': 'your_server_name',
    'database': 'your_database_name',
    'trusted_connection': 'yes'
}
```

---

## ▶️ Running the Server

### Method 1: Using VS Code Debug Configuration (Recommended)

1. Go to the **Run and Debug** view (`Ctrl+Shift+D`)
2. Select one of the following configurations from the dropdown:
   - **"Flask UI Server (Development)"** - Best for development with auto-reload
   - **"Flask UI Server (Production)"** - For production-like testing
3. Click the green **Start Debugging** button (or press `F5`)

The server will start and you'll see output in the **Debug Console**.

### Method 2: Using the Integrated Terminal

1. Open the integrated terminal (`Ctrl+``)
2. Make sure your virtual environment is activated
3. Run one of these commands:

   **For Development (with auto-reload):**
   ```powershell
   python app.py
   ```

   **Or using Flask CLI:**
   ```powershell
   $env:FLASK_APP = "app.py"
   $env:FLASK_ENV = "development"
   flask run --host=0.0.0.0 --port=10000
   ```

### Method 3: Quick Run Script

Create a `run.ps1` file (I'll create this for you next) and run it:

```powershell
.\run.ps1
```

---

## 🌐 Accessing the Application

Once the server is running, you can access the application at:

- **Local:** http://localhost:10000
- **Network:** http://0.0.0.0:10000
- **Specific IP:** http://127.0.0.1:10000

---

## 🔍 Validating API Integration

Before running the UI server, validate that the API integration is working:

### Using VS Code Debug Configuration:

1. Go to **Run and Debug** view (`Ctrl+Shift+D`)
2. Select **"Run Validation Script"**
3. Press `F5`

### Using Terminal:

```powershell
python validate_api_integration.py
```

This will test all API endpoints and confirm connectivity to `http://localhost:17654`.

---

## 🐛 Debugging

### Enable Debug Mode

The "Flask UI Server (Development)" configuration already has debugging enabled. You can:

1. Set breakpoints by clicking next to line numbers
2. Step through code with `F10` (step over) and `F11` (step into)
3. View variables in the **Variables** panel
4. Use the **Debug Console** to execute Python commands

### Common Issues and Solutions

#### Issue 1: "No module named 'flask'"
**Solution:** Make sure you've activated the virtual environment and installed requirements:
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### Issue 2: "Address already in use"
**Solution:** Another process is using port 10000. Either:
- Kill the existing process
- Change the port in `app.py` or launch configuration

#### Issue 3: "Cannot connect to API server"
**Solution:** Make sure the API server is running on `http://localhost:17654`
```powershell
# Test API connectivity
curl http://localhost:17654/api/health
```

#### Issue 4: Database connection errors
**Solution:** 
- Check `db_config.py` settings
- Ensure SQL Server is running
- Verify network connectivity to database server

#### Issue 5: "Execution Policy" error on Windows
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📁 Project Structure

```
UI/
├── app.py                          # Main Flask application
├── api_client.py                   # NEW: API client for localhost:17654
├── requirements.txt                # Python dependencies
├── validate_api_integration.py     # NEW: API validation script
├── API_INTEGRATION_SUMMARY.md      # NEW: Technical documentation
├── .vscode/
│   └── launch.json                 # VS Code debug configurations
├── pages/
│   ├── Question_Page/              # Geometry question interface (UPDATED)
│   ├── Feedback_Page/              # User feedback (UPDATED)
│   ├── User_Profile_Page/          # User profiles (UPDATED)
│   ├── Login_Page/                 # User authentication
│   ├── Registration_Page/          # User registration
│   ├── Home_Page/                  # Landing page
│   └── Contact_Page/               # Contact form
├── static/                         # CSS, images, media
├── templates/                      # HTML templates
└── flask_session/                  # Session data storage
```

---

## 🎯 Testing the Integration

### 1. Start the API Server
Make sure the Geometry Learning API is running on port 17654.

### 2. Run the Validation Script
```powershell
python validate_api_integration.py
```

Expected output:
```
🚀 Geometry Learning System - API Integration Validator
Target API: http://localhost:17654/api
============================================================
🔍 Starting API Integration Validation
==================================================
✅ PASS API Connectivity: API is healthy with 0 active sessions
...
📊 Test Results Summary
==================================================
Total Tests: 15
Passed: 15 ✅
Failed: 0 ❌
Success Rate: 100.0%
🎉 All tests passed! API integration is working correctly.
```

### 3. Start the UI Server
Use any of the methods described above.

### 4. Test the Flow
1. Open browser to `http://localhost:10000`
2. Register or login with a user account
3. Navigate to the question page
4. Answer questions and observe theorem recommendations
5. Submit feedback

---

## 🔄 Development Workflow

### Typical Development Session:

1. **Start API Server** (Terminal 1)
   ```powershell
   # In the API project directory
   python api_server.py
   ```

2. **Start UI Server** (VS Code Debug)
   - Press `F5` with "Flask UI Server (Development)" selected
   - Or use integrated terminal

3. **Make Changes**
   - Edit Python files
   - Server auto-reloads on file changes (in development mode)
   - Refresh browser to see changes

4. **Debug Issues**
   - Check Debug Console in VS Code
   - Set breakpoints in code
   - Inspect variables

5. **Test Changes**
   - Run validation script
   - Manually test in browser
   - Check logs for errors

---

## 📊 Monitoring

### View Logs

Logs appear in different places:

- **VS Code Debug Console:** Application logs when running with F5
- **Integrated Terminal:** Direct output when running from terminal
- **Flask Session Files:** `flask_session/` directory
- **UserLogger:** Logs user activity (check UserLogger.py for configuration)

### Monitor API Health

Check API status:
```powershell
curl http://localhost:17654/api/health
```

Or in Python:
```python
from api_client import check_api_health
print("API Healthy:", check_api_health())
```

---

## 🛠️ Advanced Configuration

### Changing the Server Port

Edit `app.py`:
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)  # Change port here
```

Or set environment variable:
```powershell
$env:PORT = "8080"
python app.py
```

### Changing API Endpoint

Edit `api_client.py`:
```python
def __init__(self):
    self.base_url = "http://localhost:17654/api"  # Change here
```

### Production Deployment

For production, consider using:
- **Gunicorn** (already in requirements.txt)
- **nginx** as reverse proxy
- **Environment variables** for configuration
- **SSL/TLS** for HTTPS

---

## 📚 Additional Resources

- **API Documentation:** `API_DOCUMENTATION.md` - Complete API reference
- **Integration Summary:** `API_INTEGRATION_SUMMARY.md` - Technical details
- **Flask Documentation:** https://flask.palletsprojects.com/
- **VS Code Python:** https://code.visualstudio.com/docs/python/python-tutorial

---

## 🆘 Getting Help

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Review logs in Debug Console
3. Run the validation script to test API connectivity
4. Check `API_INTEGRATION_SUMMARY.md` for technical details
5. Review error messages carefully

---

## ✅ Quick Checklist

Before starting development, verify:

- [ ] Python 3.8+ installed
- [ ] VS Code with Python extension installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database connection configured in `db_config.py`
- [ ] API server running on `http://localhost:17654`
- [ ] Validation script passes all tests

Once verified, press `F5` in VS Code and start coding! 🎉

---

**Last Updated:** November 6, 2025  
**Server:** Flask UI on port 10000  
**API:** Geometry Learning System on port 17654
