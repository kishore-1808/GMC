@echo off
echo ================================================
echo   GLOBAL DEPLOYMENT - STARTING
echo ================================================
echo.

cd /d "%~dp0"

echo Starting Flask server...
start /b python app.py > server.log 2>&1

timeout /t 3 /nobreak > nul

echo.
echo Starting ngrok tunnel...
echo Your public URL will appear below:
echo ================================================

ngrok.exe http 5000

pause
