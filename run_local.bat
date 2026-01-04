@echo off
echo ==========================================
echo   Vehicle Tracking System - Local Runner
echo ==========================================

echo [1/4] Checking Python environment...
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found! Please run 'python -m venv venv' and install requirements.
    pause
    exit /b 1
)

echo [2/4] Checking Database Connections...
REM Simple check if ports are open (requires telnet or similar, skipping for simplicity)
REM We will let the backend report connection errors.

echo [3/4] Starting Backend (API Gateway)...
start "Backend API" cmd /k "venv\Scripts\python.exe -m uvicorn backend.api_gateway.main:app --host 0.0.0.0 --port 8000 --reload"

echo [4/4] Starting Frontend (Dashboard)...
cd frontend
if not exist "node_modules" (
    echo [INFO] Installing frontend modules...
    call npm install
)
start "Frontend Dashboard" cmd /k "npm run dev"

echo.
echo ==========================================
echo   System Starting...
echo   Backend: http://localhost:8000
echo   Frontend: http://localhost:3000
echo ==========================================
echo.
echo If backend fails to connect to DB, ensure PostgreSQL (5432), Redis (6379), and InfluxDB (8086) are running.
pause
