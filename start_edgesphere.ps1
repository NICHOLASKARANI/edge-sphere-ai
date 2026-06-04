# EdgeSphere AI One-Click Startup Script
Write-Host "🚀 Starting EdgeSphere AI Platform..." -ForegroundColor Cyan

# Start Docker containers if not running
Write-Host "`n📦 Starting Docker services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to be ready
Start-Sleep -Seconds 5

# Start backend in new window
Write-Host "`n🐍 Starting Backend Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; .\venv\Scripts\activate; python main.py"

# Start dashboard in new window
Write-Host "`n⚛️ Starting React Dashboard..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\web-dashboard'; npm start"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ EdgeSphere AI is starting!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "📊 Dashboard: http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔌 API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📖 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green