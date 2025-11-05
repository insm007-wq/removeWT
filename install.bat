@echo off
cd /d "%~dp0"

echo.
echo ========================================
echo  Watermark Removal System Installer
echo ========================================
echo.

:: Python 경로 찾기
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not in PATH. Searching for Python installation...

    if exist "C:\Users\paul\AppData\Local\Programs\Python\Python312\python.exe" (
        set "PYTHON=C:\Users\paul\AppData\Local\Programs\Python\Python312\python.exe"
    ) else if exist "C:\Python311\python.exe" (
        set "PYTHON=C:\Python311\python.exe"
    ) else if exist "C:\Python310\python.exe" (
        set "PYTHON=C:\Python310\python.exe"
    ) else if exist "C:\AppData\Local\Programs\Python\Python311\python.exe" (
        set "PYTHON=C:\AppData\Local\Programs\Python\Python311\python.exe"
    ) else if exist "C:\AppData\Local\Programs\Python\Python310\python.exe" (
        set "PYTHON=C:\AppData\Local\Programs\Python\Python310\python.exe"
    ) else (
        echo Error: Python not found
        pause
        exit /b 1
    )
    echo Found Python: %PYTHON%
) else (
    set "PYTHON=python"
)

echo [1/2] Installing all dependencies from requirements.txt...
echo This will install PyTorch, YOLO, LAMA, and other libraries.
echo This may take several minutes...
echo.

%PYTHON% -m pip install -r requirements.txt --user
if errorlevel 1 (
    echo.
    echo ERROR: Installation failed!
    echo Please check your internet connection and try again.
    echo.
    pause
    exit /b 1
)
echo.
echo ========================================
echo All dependencies installed successfully!
echo ========================================
echo.
echo Press any key to continue...
pause >nul

echo.
echo [2/3] Creating necessary directories...
if not exist "output" mkdir output
if not exist "temp" mkdir temp
if not exist "logs" mkdir logs
if not exist "models" mkdir models

echo.
echo [3/3] Downloading FFmpeg...
if exist "ffmpeg\ffmpeg.exe" (
    echo FFmpeg already exists at: %cd%\ffmpeg\ffmpeg.exe
    echo ========================================
    echo FFmpeg download skipped (already installed)
    echo ========================================
) else (
    echo Downloading FFmpeg (this may take a few minutes)...
    %PYTHON% -m pip install requests -q

    %PYTHON% download_ffmpeg.py

    if errorlevel 1 (
        echo.
        echo ========================================
        echo WARNING: FFmpeg download failed
        echo ========================================
        echo You can manually download from:
        echo https://github.com/GyanD/codexffmpeg/releases/download/6.1/ffmpeg-6.1-full_build.zip
        echo Then extract to: ffmpeg folder
        echo.
    ) else (
        echo.
        echo ========================================
        echo FFmpeg download completed successfully!
        echo ========================================
    )
)

echo.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo !!                                                      !!
echo !!   *** INSTALLATION COMPLETE! ***                   !!
echo !!                                                      !!
echo !!   Development Mode:                                !!
echo !!   - Run: start.bat                                 !!
echo !!                                                      !!
echo !!   Build Executable:                                !!
echo !!   - Run: build.bat                                 !!
echo !!                                                      !!
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo.
pause
