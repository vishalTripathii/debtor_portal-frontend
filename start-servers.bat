@echo off
title Debtor Portal - Server Launcher
echo ========================================
echo    Debtor Portal - Starting Servers
echo ========================================
echo.

:: Get the directory where the batch file is located
set "ROOT_DIR=%~dp0"

:: Start Backend Server (Django)
echo [1/2] Starting Backend Server (Django)...
start "Backend Server - Django" cmd /k "cd /d %ROOT_DIR%backend && python manage.py runserver 8000"

:: Wait a moment for backend to initialize
timeout /t 2 /nobreak > nul

:: Start Frontend Server (Vite)
echo [2/2] Starting Frontend Server (Vite)...
start "Frontend Server - Vite" cmd /k "cd /d %ROOT_DIR% && npm run dev"

echo.
echo ========================================
echo    Both servers are starting...
echo ========================================
echo.
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:5173
echo.
echo    Close this window or press any key to exit.
echo    (The server windows will remain open)
echo ========================================
pause > nul
