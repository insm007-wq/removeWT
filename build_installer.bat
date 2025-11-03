@echo off
REM Watermark Remover - Full Installer Builder
REM Builds exe with PyInstaller and packages with NSIS
REM All dependencies included: FFmpeg, YOLO model, and Python runtime

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Watermark Removal System Installer
echo  Building Full Installer...
echo ========================================
echo.

cd /d "%~dp0"

REM Python 찾기
set "PYTHON_EXE="

for /f "tokens=*" %%i in ('where python 2^>nul') do set "PYTHON_EXE=%%i"

if "%PYTHON_EXE%"=="" (
    if exist "C:\Users\paul\AppData\Local\Programs\Python\Python312\python.exe" (
        set "PYTHON_EXE=C:\Users\paul\AppData\Local\Programs\Python\Python312\python.exe"
    )
)
if "%PYTHON_EXE%"=="" (
    if exist "C:\Python312\python.exe" (
        set "PYTHON_EXE=C:\Python312\python.exe"
    )
)
if "%PYTHON_EXE%"=="" (
    if exist "C:\Python311\python.exe" (
        set "PYTHON_EXE=C:\Python311\python.exe"
    )
)

if "%PYTHON_EXE%"=="" (
    echo ERROR: Python not found!
    echo Please ensure Python is installed and in PATH
    pause
    exit /b 1
)

echo Found Python: %PYTHON_EXE%
echo.

REM Step 1: 필수 파일 존재 확인
echo [Step 1/3] Checking required files...
echo.

set "MISSING_FILES=0"

if not exist "ffmpeg\ffmpeg.exe" (
    echo WARNING: ffmpeg\ffmpeg.exe not found
    set "MISSING_FILES=1"
)
if not exist "ffmpeg\ffprobe.exe" (
    echo WARNING: ffmpeg\ffprobe.exe not found
    set "MISSING_FILES=1"
)
if not exist "models\best.pt" (
    echo WARNING: models\best.pt not found
    set "MISSING_FILES=1"
)

if %MISSING_FILES% equ 1 (
    echo.
    echo These files are recommended but can be added later:
    echo - ffmpeg\ffmpeg.exe (FFmpeg binary)
    echo - ffmpeg\ffprobe.exe (FFmpeg probe)
    echo - models\best.pt (YOLO model)
    echo.
    echo You can download them by running: install.bat
    echo.
)

REM Step 2: 기존 빌드 정리 및 PyInstaller 실행
echo.
echo [Step 2/3] Building executable with PyInstaller...
echo This may take several minutes...
echo.

if exist "build" (
    echo Removing old build...
    rmdir /s /q "build" >nul 2>&1
)
if exist "dist" (
    echo Removing old dist...
    rmdir /s /q "dist" >nul 2>&1
)

REM PyInstaller 실행
"%PYTHON_EXE%" -m PyInstaller watermark_remover.spec --noconfirm

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller failed!
    echo Please check:
    echo 1. watermark_remover.spec exists
    echo 2. All source files are in place
    echo 3. PyInstaller is installed (pip install pyinstaller)
    echo.
    pause
    exit /b 1
)

echo.
echo PyInstaller completed successfully!

REM Step 3: NSIS로 인스톨러 생성
echo.
echo [Step 3/3] Building installer with NSIS...
echo.

REM NSIS 찾기
set "NSIS_EXE="

if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    set "NSIS_EXE=C:\Program Files (x86)\NSIS\makensis.exe"
)
if exist "C:\Program Files\NSIS\makensis.exe" (
    set "NSIS_EXE=C:\Program Files\NSIS\makensis.exe"
)

if "%NSIS_EXE%"=="" (
    echo.
    echo ERROR: NSIS not found!
    echo Please install NSIS: https://nsis.sourceforge.io/
    echo.
    pause
    exit /b 1
)

echo Found NSIS: %NSIS_EXE%
echo.

"%NSIS_EXE%" installer.nsi

if errorlevel 1 (
    echo.
    echo ERROR: NSIS build failed!
    echo Please check installer.nsi for errors.
    echo.
    pause
    exit /b 1
)

REM 최종 결과 표시
echo.
echo ========================================
echo  BUILD COMPLETE!
echo ========================================
echo.

if exist "WatermarkRemover_Installer.exe" (
    echo Successfully created: WatermarkRemover_Installer.exe
    echo.
    for /f "tokens=*" %%A in ('dir /s /b "WatermarkRemover_Installer.exe"') do (
        echo Location: %%~dpA
        for /F %%B in ('dir %%A ^| findstr /R ".*"') do (
            echo %%B
        )
    )
) else (
    echo ERROR: Installer not created!
)

echo.
echo Next steps:
echo 1. Share WatermarkRemover_Installer.exe with users
echo 2. Users run it to install the application
echo 3. No Python or dependencies needed on user's PC
echo.

pause
