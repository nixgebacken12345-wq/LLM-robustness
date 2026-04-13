@echo off
title Whisper Telemetry Collector - Installation
echo Installing Whisper Telemetry Collector...
echo.

:: Check admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Administrator privileges required.
    pause
    exit /b 1
)

:: Install Python dependencies
pip install -r requirements.txt

:: Install as Windows service
python src\main.py --service install

:: Start service
net start WhisperTelemetry

echo.
echo Installation complete.
echo Logs: C:\ProgramData\WhisperTelemetry\logs\
pause
