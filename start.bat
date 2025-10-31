@echo off
cd /d "%~dp0"

echo.
echo ========================================
echo  Watermark Removal System
echo ========================================
echo.

:: .env 파일 확인
if not exist ".env" (
    echo Error: .env file not found!
    echo Please create .env file with your Replicate API token:
    echo    REPLICATE_API_TOKEN=your_token_here
    echo.
    pause
    exit /b 1
)

:: Python 경로 찾기
python --version >nul 2>&1
if errorlevel 1 (
    if exist "C:\Users\paul\AppData\Local\Programs\Python\Python312\python.exe" (
        set "PYTHON=C:\Users\paul\AppData\Local\Programs\Python\Python312\python.exe"
    ) else (
        echo Error: Python not found
        pause
        exit /b 1
    )
) else (
    set "PYTHON=python"
)

:: GUI 실행
echo Starting GUI...
%PYTHON% gui.py
if errorlevel 1 (
    echo.
    echo Error running GUI. Please check:
    echo 1. Python is installed
    echo 2. All dependencies are installed (run install.bat)
    echo 3. .env file exists with valid API token
    echo.
    pause
    exit /b 1
)
