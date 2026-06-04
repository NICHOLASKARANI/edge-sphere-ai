# Quick Fix Script for Common Issues
Write-Host "🔧 Running EdgeSphere AI Quick Fix..." -ForegroundColor Cyan

# Fix Docker issues
Write-Host "`n1. Checking Docker status..." -ForegroundColor Yellow
$dockerRunning = docker ps 2>$null
if (-not $dockerRunning) {
    Write-Host "⚠ Docker is not running. Please:" -ForegroundColor Yellow
    Write-Host "   - Start Docker Desktop from Start Menu" -ForegroundColor White
    Write-Host "   - Wait for Docker engine to start" -ForegroundColor White
    Write-Host "   - Run this script again" -ForegroundColor White
    pause
    exit 1
}

# Clean up Docker containers
Write-Host "`n2. Cleaning up Docker containers..." -ForegroundColor Yellow
docker-compose down
docker-compose up -d

# Recreate Python venv if needed
Write-Host "`n3. Checking Python environment..." -ForegroundColor Yellow
if (Test-Path "backend\venv") {
    Write-Host "✓ Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    cd backend
    python -m venv venv
    .\venv\Scripts\activate
    pip install --upgrade pip
    pip install fastapi uvicorn paho-mqtt sqlalchemy psycopg2-binary redis pydantic python-dotenv
    cd ..
}

# Reinstall node modules if needed
Write-Host "`n4. Checking Node modules..." -ForegroundColor Yellow
if (-not (Test-Path "web-dashboard\node_modules")) {
    Write-Host "Installing Node dependencies..." -ForegroundColor Yellow
    cd web-dashboard
    npm install
    cd ..
} else {
    Write-Host "✓ Node modules exist" -ForegroundColor Green
}

Write-Host "`n✅ Quick fix completed!" -ForegroundColor Green
Write-Host "Run '.\start_edgesphere.ps1' to start the platform" -ForegroundColor Cyan