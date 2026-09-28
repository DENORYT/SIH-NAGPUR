@echo off
title ShadowLink Intelligence Platform
color 0B

echo ========================================================
echo   SHADOWLINK ENTERPRISE - UNIFIED LAUNCHER
echo ========================================================
echo.
echo Starting the FastAPI server (Backend + Frontend)...

cd backend

:: Start the Uvicorn server in a new dedicated console window
start "ShadowLink API Server" cmd /k ".\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo Waiting for the server to initialize...
timeout /t 3 /nobreak > NUL

echo Opening the dashboard in your default web browser...
start http://127.0.0.1:8000/

echo.
echo ========================================================
echo System is running!
echo You can safely close this launcher window.
echo To STOP ShadowLink, close the other "ShadowLink API Server" window.
echo ========================================================
pause > NUL
