@echo off
echo ========================================
echo    EdgeSphere AI Platform
echo ========================================
echo.
echo Starting Backend Server...
start "EdgeSphere Backend" cmd /k "cd backend && python main.py"
timeout /t 3 /nobreak >nul
echo Starting Dashboard...
start "EdgeSphere Dashboard" cmd /k "cd web-dashboard && npm start"
echo.
echo ========================================
echo Platform starting!
echo Backend: http://localhost:8000
echo Dashboard: http://localhost:3000
echo ========================================
echo.
echo Press any key to stop all services...
pause >nul
taskkill /F /IM node.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
echo Services stopped.
