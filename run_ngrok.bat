@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo   📱 ngrok 스마트폰/외부 기기 접속 터널 실행기
echo ========================================================
echo.

set NGROK_BIN=
where ngrok >nul 2>&1
if not errorlevel 1 set NGROK_BIN=ngrok
if "%NGROK_BIN%"=="" (
    if exist "C:\laragon\bin\ngrok\ngrok.exe" set NGROK_BIN=C:\laragon\bin\ngrok\ngrok.exe
)

if "%NGROK_BIN%"=="" goto ERROR_NO_NGROK

netstat -ano | findstr ":8501" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 goto START_SERVER
goto RUN_TUNNEL

:START_SERVER
echo [안내] 대시보드 서버(8501 포트)가 꺼져 있어 새 창으로 자동 실행합니다...
start "공무 자재관리 대시보드" cmd /c "run.bat"
echo 서버 준비 대기 중 (5초)...
timeout /t 5 /nobreak >nul
goto RUN_TUNNEL

:RUN_TUNNEL
echo.
echo ========================================================
echo [안내] 아래 Forwarding 주소로 스마트폰에서 접속하세요.
echo (주의: 주소 뒤에 /app 등을 붙이지 말고 주소 그대로 접속)
echo ========================================================
echo.
echo ngrok 8501 터널을 시작합니다...
"%NGROK_BIN%" http 8501
if errorlevel 1 goto ERROR_NGROK
goto END

:ERROR_NO_NGROK
echo [오류] ngrok 프로그램을 찾을 수 없습니다.
echo https://ngrok.com 에서 ngrok을 설치해 주세요.
pause
goto END

:ERROR_NGROK
echo.
echo [오류] ngrok 실행에 실패했습니다.
echo 인증 토큰 등록 여부를 확인해 주세요: ngrok config add-authtoken 내토큰
pause
goto END

:END