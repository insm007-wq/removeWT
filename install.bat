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

echo [1/4] Installing base dependencies...
%PYTHON% -m pip install -r requirements.txt --user

echo.
echo [2/4] Installing GPU dependencies...
echo This will install PyTorch, YOLO, LAMA, and other GPU libraries.
echo This may take several minutes...
echo.

echo Installing PyTorch with CUDA support...
%PYTHON% -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --user
%PYTHON% -m pip install ultralytics iopaint opencv-python numpy pillow scipy nvidia-ml-py3 psutil --user
echo GPU dependencies installed successfully!

echo.
echo [3/4] Creating necessary directories...
if not exist "output" mkdir output
if not exist "temp" mkdir temp
if not exist "logs" mkdir logs
if not exist "models" mkdir models

echo.
echo [4/4] Downloading FFmpeg...
if exist "ffmpeg\ffmpeg.exe" (
    echo FFmpeg already exists at: %cd%\ffmpeg\ffmpeg.exe
) else (
    echo Downloading FFmpeg (this may take a few minutes)...
    %PYTHON% -m pip install requests -q

    %PYTHON% -c ^
    "^
    import requests ^
    import os ^
    import shutil ^
    import zipfile ^
    ^
    print('Downloading FFmpeg...') ^
    url = 'https://github.com/GyanD/codexffmpeg/releases/download/6.1/ffmpeg-6.1-full_build.zip' ^
    zip_path = 'ffmpeg_temp.zip' ^
    extract_path = 'ffmpeg_extract' ^
    ^
    try: ^
        if not os.path.exists('ffmpeg'): ^
            os.makedirs('ffmpeg') ^
        ^
        response = requests.get(url, stream=True, timeout=30) ^
        total_size = int(response.headers.get('content-length', 0)) ^
        downloaded = 0 ^
        ^
        with open(zip_path, 'wb') as f: ^
            for chunk in response.iter_content(chunk_size=8192): ^
                if chunk: ^
                    f.write(chunk) ^
                    downloaded += len(chunk) ^
                    if total_size: ^
                        percent = (downloaded / total_size) * 100 ^
                        print(f'Downloaded: {percent:.1f}%%', end='\r') ^
        ^
        print('Extracting...') ^
        with zipfile.ZipFile(zip_path, 'r') as zip_ref: ^
            zip_ref.extractall(extract_path) ^
        ^
        print('Organizing files...') ^
        for root, dirs, files in os.walk(extract_path): ^
            for file in files: ^
                if file in ['ffmpeg.exe', 'ffprobe.exe']: ^
                    src = os.path.join(root, file) ^
                    dst = os.path.join('ffmpeg', file) ^
                    shutil.copy2(src, dst) ^
                    print(f'Copied: {file}') ^
        ^
        shutil.rmtree(extract_path) ^
        os.remove(zip_path) ^
        print('FFmpeg setup complete!') ^
    except Exception as e: ^
        print(f'Warning: FFmpeg download failed: {e}') ^
    "

    if errorlevel 1 (
        echo Warning: FFmpeg download failed. You can manually download from:
        echo https://github.com/GyanD/codexffmpeg/releases/download/6.1/ffmpeg-6.1-full_build.zip
        echo Extract to: ffmpeg folder
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
