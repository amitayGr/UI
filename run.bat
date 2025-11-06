@echo off
REM Batch script to run the Flask UI server on Windows
REM Run this script with: run.bat

echo.
echo ======================================================
echo   Starting Geometry Learning System UI Server
echo ======================================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo [OK] Found virtual environment: venv
    call venv\Scripts\activate.bat
) else if exist "uivenv\Scripts\activate.bat" (
    echo [OK] Found virtual environment: uivenv
    call uivenv\Scripts\activate.bat
) else (
    echo [INFO] No virtual environment found. Creating one...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo [INFO] Checking API server connectivity...

REM Test API connectivity
curl -s http://localhost:17654/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] API server is running on http://localhost:17654
) else (
    echo [WARNING] Cannot connect to API server on http://localhost:17654
    echo           Make sure the API server is running for full functionality.
)

echo.
echo [INFO] Starting Flask UI Server...
echo        Server will be available at: http://localhost:10000
echo        Press Ctrl+C to stop the server
echo.

REM Set environment variables
set FLASK_APP=app.py
set FLASK_ENV=development

REM Run the Flask application
python app.py

pause
