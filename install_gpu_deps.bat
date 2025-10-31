@echo off
REM GPU 의존성 자동 설치 스크립트
REM 설치 프로그램에서 실행됨

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Installing GPU Dependencies
echo ========================================
echo.

REM 현재 디렉토리
cd /d "%~dp0"

REM Python 실행 파일 찾기
set "PYTHON_EXE=%~dp0python.exe"

if not exist "%PYTHON_EXE%" (
    echo Error: python.exe not found in installation directory
    pause
    exit /b 1
)

echo Found Python: %PYTHON_EXE%
echo.

REM PyTorch (CUDA 118 버전)
echo [1/4] Installing PyTorch with CUDA support...
"%PYTHON_EXE%" -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --user -q
if errorlevel 1 (
    echo Warning: PyTorch installation encountered issues
)

REM YOLOv11 (ultralytics)
echo [2/4] Installing YOLOv11...
"%PYTHON_EXE%" -m pip install ultralytics -q
if errorlevel 1 (
    echo Warning: ultralytics installation encountered issues
)

REM LAMA (IOPaint)
echo [3/4] Installing LAMA inpainting model...
"%PYTHON_EXE%" -m pip install iopaint -q
if errorlevel 1 (
    echo Warning: iopaint installation encountered issues
)

REM 추가 의존성
echo [4/4] Installing additional libraries...
"%PYTHON_EXE%" -m pip install opencv-python numpy pillow scipy -q
if errorlevel 1 (
    echo Warning: Additional libraries installation encountered issues
)

echo.
echo ========================================
echo GPU dependencies installation complete!
echo ========================================
echo.

REM 로그 저장
echo GPU Installation Log - %date% %time% >> "%~dp0install_log.txt"

exit /b 0
