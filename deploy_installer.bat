@echo off
chcp 65001 > nul

echo.
echo =========================================================
echo   Watermark Removal System - 설치 프로그램
echo =========================================================
echo.
echo 바탕화면에 removeWT_release 폴더를 설치합니다.
echo.

:: 관리자 권한 확인 및 자동 재실행
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process cmd -ArgumentList '/c %~s0' -Verb RunAs" >nul 2>&1
    exit /b 0
)

:: 바탕화면 경로
for /f "tokens=3" %%A in ('reg query "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop') do set "DESKTOP=%%A"

echo 설치 경로: %DESKTOP%\removeWT_release
echo.

:: 이미 폴더가 있으면 삭제
if exist "%DESKTOP%\removeWT_release" (
    rmdir /s /q "%DESKTOP%\removeWT_release"
)

echo.
echo 필수 파일을 복사합니다...

:: 대상 폴더 생성
mkdir "%DESKTOP%\removeWT_release"
mkdir "%DESKTOP%\removeWT_release\api_clients"
mkdir "%DESKTOP%\removeWT_release\utils"

:: 현재 디렉토리에서 파일 찾기
cd /d "%~dp0"

echo 메인 파일 복사...
copy "gui.py" "%DESKTOP%\removeWT_release\" /Y >nul 2>&1
copy "watermark_remover.py" "%DESKTOP%\removeWT_release\" /Y >nul 2>&1
copy "config.py" "%DESKTOP%\removeWT_release\" /Y >nul 2>&1
copy "requirements.txt" "%DESKTOP%\removeWT_release\" /Y >nul 2>&1
copy "download_ffmpeg.py" "%DESKTOP%\removeWT_release\" /Y >nul 2>&1
copy ".env" "%DESKTOP%\removeWT_release\" /Y >nul 2>&1
copy "start.bat" "%DESKTOP%\removeWT_release\" /Y >nul 2>&1
copy "install.bat" "%DESKTOP%\removeWT_release\" /Y >nul 2>&1

echo 모듈 폴더 복사...
copy "api_clients\__init__.py" "%DESKTOP%\removeWT_release\api_clients\" /Y >nul 2>&1
copy "api_clients\local_gpu_client.py" "%DESKTOP%\removeWT_release\api_clients\" /Y >nul 2>&1
copy "api_clients\replicate_client.py" "%DESKTOP%\removeWT_release\api_clients\" /Y >nul 2>&1
copy "utils\__init__.py" "%DESKTOP%\removeWT_release\utils\" /Y >nul 2>&1
copy "utils\gpu_utils.py" "%DESKTOP%\removeWT_release\utils\" /Y >nul 2>&1
copy "utils\logger.py" "%DESKTOP%\removeWT_release\utils\" /Y >nul 2>&1
copy "utils\security_utils.py" "%DESKTOP%\removeWT_release\utils\" /Y >nul 2>&1
copy "utils\video_utils.py" "%DESKTOP%\removeWT_release\utils\" /Y >nul 2>&1

echo.
echo =========================================================
echo   설치 완료!
echo =========================================================
echo.
echo 바탕화면의 removeWT_release 폴더에 설치되었습니다.
echo.
pause
