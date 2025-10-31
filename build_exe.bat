@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Building Watermark Remover EXE
echo ========================================
echo.

REM 현재 디렉토리로 이동
cd /d "%~dp0"

echo Current directory: %cd%

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

REM 기존 빌드 정리
if exist "build" (
    echo Removing old build...
    rmdir /s /q "build"
)
if exist "dist" (
    echo Removing old dist...
    rmdir /s /q "dist"
)

REM PyInstaller 실행
echo.
echo Building executable... (This may take several minutes)
echo.

"%PYTHON_EXE%" -m PyInstaller watermark_remover.spec --noconfirm

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  BUILD COMPLETE!
    echo ========================================
    echo.
    if exist "dist\WatermarkRemover.exe" (
        echo Output file: dist\WatermarkRemover.exe
        dir "dist\WatermarkRemover.exe"
    )
) else (
    echo.
    echo ERROR: Build failed!
    echo Please check the error messages above.
)

echo.
pause
