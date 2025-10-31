@echo off
REM 워터마크 제거 프로그램 실행 스크립트

cd /d "%~dp0"

echo.
echo ========================================
echo  Watermark Removal System
echo ========================================
echo.

if exist "dist\WatermarkRemover.exe" (
    echo Starting application...
    start "" "dist\WatermarkRemover.exe"
) else (
    echo Error: WatermarkRemover.exe not found!
    echo Please run build_exe.bat first to build the executable.
    pause
)
