@echo off
cd /d "%~dp0"

REM Start Python with window hidden but capture output
start /b pythonw app.py 2>&1

timeout /t 2 /nobreak > nul

echo Server started! 
echo Open http://127.0.0.1:5000 in your browser
echo.
echo To stop: Task Manager -> End task -> pythonw.exe
pause
