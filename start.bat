@echo off
REM Watermark Removal System - Quick Start GUI

setlocal enabledelayedexpansion

title Watermark Removal System - GUI

cd /d %~dp0

echo.
echo ============================================================
echo Watermark Removal System - GUI
echo ============================================================
echo.
echo Starting Watermark Removal GUI...
echo.

if not exist "gui.py" (
    echo [ERROR] gui.py not found
    exit /b 1
)

echo Starting GUI...
python gui.py

if errorlevel 1 (
    echo.
    echo [ERROR] GUI failed to start
    echo Error code: %errorlevel%
)

pause
