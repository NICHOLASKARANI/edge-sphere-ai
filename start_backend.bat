Write-Host "Starting EdgeSphere AI Backend..." -ForegroundColor Cyan
cd backend
python -m pip install --quiet fastapi uvicorn pydantic python-dotenv
python main.py
Read-Host "Press Enter to exit"
