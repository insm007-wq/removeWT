@echo off
chcp 65001 > nul

echo.
echo =========================================================
echo   Python 환경 초기화 - 모든 pip 패키지 제거
echo =========================================================
echo.
echo 경고: pip와 setuptools를 제외한 모든 패키지가 제거됩니다.
echo.
pause

:: Python 경로 찾기
python --version >nul 2>&1
if %errorlevel% neq 0 (
    if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" (
        set "PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe"
    ) else if exist "C:\Python312\python.exe" (
        set "PYTHON=C:\Python312\python.exe"
    ) else (
        echo Error: Python not found
        pause
        exit /b 1
    )
) else (
    set "PYTHON=python"
)

echo.
echo 설치된 패키지 목록을 가져오는 중...
%PYTHON% -m pip list

echo.
echo 모든 패키지를 제거합니다...
echo (pip와 setuptools는 유지됩니다)
echo.

:: pip freeze로 설치된 패키지 목록 가져와서 제거
for /f "delims==" %%i in ('%PYTHON% -m pip freeze') do (
    echo 제거 중: %%i
    %PYTHON% -m pip uninstall -y %%i >nul 2>&1
)

echo.
echo =========================================================
echo   정리 완료!
echo =========================================================
echo.
echo 남은 패키지:
%PYTHON% -m pip list
echo.
pause
