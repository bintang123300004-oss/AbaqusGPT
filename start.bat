@echo off
title AbaqusGPT - Starting Services
color 0A

echo ============================================
echo   AbaqusGPT - AI Documentation Assistant
echo ============================================
echo.
echo Starting backend and frontend servers...
echo.

REM Start backend API in new window
echo [1/2] Starting Backend API (Port 8000)...
start "AbaqusGPT Backend" cmd /k "cd /d "%~dp0" && python -m uvicorn src.api.main:app --reload --port 8000"

REM Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

REM Start frontend server in new window
echo [2/2] Starting Frontend UI (Port 3000)...
start "AbaqusGPT Frontend" cmd /k "cd /d "%~dp0frontend" && python -m http.server 3000"

REM Wait a moment for frontend to start
timeout /t 2 /nobreak >nul

echo.
echo ============================================
echo   Services Started Successfully!
echo ============================================
echo.
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo Frontend UI:  http://localhost:3000
echo.
echo Press any key to open the chat interface...
pause >nul

REM Open browser
start http://localhost:3000

echo.
echo Both services are running in separate windows.
echo Close those windows to stop the services.
echo.
pause
