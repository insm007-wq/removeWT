@echo off
setlocal enabledelayexpansion

echo.
echo ========================================
echo  Watermark Removal System Installer
echo ========================================
echo.

:: Python 버전 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/3] Installing base dependencies...
pip install -r requirements.txt --user

echo.
echo [2/3] Installing Local GPU dependencies (optional)...
echo This will install PyTorch, YOLO, and other GPU libraries.
echo This may take several minutes...
echo.

set /p gpu_install="Do you want to install Local GPU support? (y/n): "
if /i "%gpu_install%"=="y" (
    echo Installing GPU dependencies...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --user
    pip install ultralytics iopaint opencv-python numpy pillow scipy --user
    echo GPU dependencies installed successfully!
) else (
    echo Skipping GPU dependencies. Replicate API only mode will be used.
)

echo.
echo [3/3] Creating necessary directories...
if not exist "output" mkdir output
if not exist "temp" mkdir temp
if not exist "logs" mkdir logs
if not exist "models" mkdir models

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Create .env file with your Replicate API token:
echo    REPLICATE_API_TOKEN=your_token_here
echo.
echo 2. Run the application:
echo    python -m start.bat
echo    or
echo    python gui.py
echo.
pause
