@echo off
REM FFmpeg 자동 다운로드 스크립트

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Downloading FFmpeg
echo ========================================
echo.

cd /d "%~dp0"

REM FFmpeg 디렉토리 확인
if not exist "ffmpeg" mkdir ffmpeg

REM 이미 있는지 확인
if exist "ffmpeg\ffmpeg.exe" (
    echo FFmpeg already exists!
    echo Location: %cd%\ffmpeg\ffmpeg.exe
    exit /b 0
)

REM Python이 있는지 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    pause
    exit /b 1
)

REM Python으로 다운로드 (requests 필요)
echo Checking for requests module...
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Installing requests...
    python -m pip install requests -q
)

REM Python 다운로드 스크립트 실행
python -c ^
"^
import requests ^
import os ^
import shutil ^
from pathlib import Path ^
^
print('Downloading FFmpeg...') ^
url = 'https://github.com/GyanD/codexffmpeg/releases/download/6.1/ffmpeg-6.1-full_build.zip' ^
zip_path = 'ffmpeg_temp.zip' ^
extract_path = 'ffmpeg_extract' ^
^
try: ^
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
                    print(f'Downloaded: {percent:.1f}%', end='\r') ^
    ^
    print('Download complete!') ^
    ^
    print('Extracting...') ^
    import zipfile ^
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
    ^
    print('FFmpeg setup complete!') ^
^
except Exception as e: ^
    print(f'Error: {e}') ^
    exit(1) ^
"

if errorlevel 1 (
    echo Error downloading FFmpeg
    pause
    exit /b 1
)

echo.
echo ========================================
echo FFmpeg successfully downloaded!
echo Location: %cd%\ffmpeg
echo ========================================
echo.

pause
