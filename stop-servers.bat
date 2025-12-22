@echo off
title Debtor Portal - Stop Servers
echo ========================================
echo    Debtor Portal - Stopping Servers
echo ========================================
echo.

:: Kill Node.js processes (Vite frontend)
echo Stopping Frontend Server (Node.js/Vite)...
taskkill /F /IM node.exe 2>nul
if %errorlevel%==0 (
    echo    Frontend server stopped.
) else (
    echo    No frontend server running.
)

:: Kill Python processes (Django backend)
echo Stopping Backend Server (Python/Django)...
taskkill /F /IM python.exe 2>nul
if %errorlevel%==0 (
    echo    Backend server stopped.
) else (
    echo    No backend server running.
)

echo.
echo ========================================
echo    All servers stopped.
echo ========================================
echo.
pause
