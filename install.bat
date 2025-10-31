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

echo [1/3] Installing base dependencies...
%PYTHON% -m pip install -r requirements.txt --user

echo.
echo [2/3] Installing Local GPU dependencies...
echo This will install PyTorch, YOLO, and other GPU libraries.
echo This may take several minutes...
echo.

echo Installing GPU dependencies...
%PYTHON% -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --user
%PYTHON% -m pip install ultralytics iopaint opencv-python numpy pillow scipy --user
echo GPU dependencies installed successfully!

echo.
echo [3/3] Creating necessary directories...
if not exist "output" mkdir output
if not exist "temp" mkdir temp
if not exist "logs" mkdir logs
if not exist "models" mkdir models

echo.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo !!                                                      !!
echo !!   *** INSTALLATION COMPLETE! ***                   !!
echo !!                                                      !!
echo !!   Run start.bat to launch the GUI                  !!
echo !!                                                      !!
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo.
pause
