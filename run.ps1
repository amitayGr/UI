# PowerShell script to run the Flask UI server
# Run this script with: .\run.ps1

Write-Host "🚀 Starting Geometry Learning System UI Server..." -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
$venvPaths = @(".\venv\Scripts\Activate.ps1", ".\uivenv\Scripts\Activate.ps1")
$venvFound = $false

foreach ($path in $venvPaths) {
    if (Test-Path $path) {
        Write-Host "✅ Found virtual environment: $path" -ForegroundColor Green
        & $path
        $venvFound = $true
        break
    }
}

if (-not $venvFound) {
    Write-Host "⚠️  No virtual environment found. Creating one..." -ForegroundColor Yellow
    python -m venv venv
    & .\venv\Scripts\Activate.ps1
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "🔍 Checking API server connectivity..." -ForegroundColor Cyan

# Test API connectivity
try {
    $response = Invoke-WebRequest -Uri "http://localhost:17654/api/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✅ API server is running on http://localhost:17654" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Warning: Cannot connect to API server on http://localhost:17654" -ForegroundColor Yellow
    Write-Host "   Make sure the API server is running for full functionality." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🌐 Starting Flask UI Server..." -ForegroundColor Cyan
Write-Host "   Server will be available at: http://localhost:10000" -ForegroundColor White
Write-Host "   Press Ctrl+C to stop the server" -ForegroundColor White
Write-Host ""

# Set environment variables
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"

# Run the Flask application
python app.py
