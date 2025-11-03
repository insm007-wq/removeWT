@echo off
REM Build Watermark Remover - Unified build script for EXE and Installer
REM 1. PyInstaller로 .exe 생성
REM 2. NSIS로 최종 설치 프로그램 생성 (선택 사항)

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Building Watermark Remover
echo ========================================
echo.

cd /d "%~dp0"

REM Python 찾기
set "PYTHON_EXE="

REM 먼저 PATH에서 python 찾기
for /f "tokens=*" %%i in ('where python 2^>nul') do set "PYTHON_EXE=%%i"

REM PATH에 없으면 일반적인 설치 위치 확인
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

REM Step 1: PyInstaller 설치 확인
echo.
echo [Step 1/4] Checking PyInstaller...
"%PYTHON_EXE%" -m pip list | findstr /i pyinstaller >nul
if errorlevel 1 (
    echo Installing PyInstaller...
    "%PYTHON_EXE%" -m pip install pyinstaller -q
)

REM Step 2: 기존 빌드 디렉토리 정리
echo [Step 2/4] Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
echo Cleaned!

REM Step 3: PyInstaller로 .exe 생성
echo.
echo [Step 3/4] Running PyInstaller...
echo This may take several minutes...
echo.
"%PYTHON_EXE%" -m PyInstaller watermark_remover.spec --noconfirm
if errorlevel 1 (
    echo Error: PyInstaller failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo  PyInstaller Complete!
echo ========================================
echo.
echo Created: dist\WatermarkRemover\WatermarkRemover.exe
echo.

REM Step 4: NSIS 설치 프로그램 생성 (선택 사항)
echo [Step 4/4] Checking for NSIS installer...
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    echo Building installer with NSIS...
    "C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
    if errorlevel 1 (
        echo Warning: NSIS build failed. Check if installer.nsi is correct.
    ) else (
        echo.
        echo ========================================
        echo  INSTALLER CREATED SUCCESSFULLY!
        echo ========================================
        echo.
        echo Created: WatermarkRemover_Installer.exe
        echo.
    )
) else (
    echo.
    echo Note: NSIS not installed. Skipping installer creation.
    echo To create an installer:
    echo 1. Install NSIS: https://nsis.sourceforge.io/
    echo 2. Run this script again
    echo.
)

echo ========================================
echo  BUILD COMPLETE!
echo ========================================
echo.
echo Output:
echo - Executable: dist\WatermarkRemover\WatermarkRemover.exe
if exist "WatermarkRemover_Installer.exe" (
    echo - Installer: WatermarkRemover_Installer.exe
)
echo.

pause
