@echo off
echo Starting EdgeSphere AI Dashboard...
cd web-dashboard
if not exist node_modules (
  echo Installing dependencies (first time only)...
  call npm install
)
npm start
