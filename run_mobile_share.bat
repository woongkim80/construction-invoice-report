@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo   스마트폰/외부 접속을 위한 보안 터널을 시작합니다.
echo ========================================================
echo.

netstat -ano | findstr ":8501" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo [안내] 대시보드(run.bat)가 실행되지 않아 새 창으로 자동 실행합니다...
    start "공무 자재관리 대시보드" cmd /c "run.bat"
    timeout /t 5 /nobreak >nul
)

where cloudflared >nul 2>&1
if not errorlevel 1 (
    echo [Cloudflare Tunnel 감지] 무료 HTTPS 터널을 생성합니다...
    cloudflared tunnel --url http://localhost:8501
    pause
    goto END
)

where ngrok >nul 2>&1
if not errorlevel 1 (
    echo [ngrok 감지] ngrok을 이용해 포트 8501로 연결합니다...
    echo (접속 주소: Forwarding 옆의 https://... 주소를 사용하세요)
    echo.
    ngrok http 8501
    pause
    goto END
)

if exist "C:\laragon\bin\ngrok\ngrok.exe" (
    echo [Laragon ngrok 감지] ngrok을 이용해 포트 8501로 연결합니다...
    C:\laragon\bin\ngrok\ngrok.exe http 8501
    pause
    goto END
)

echo [오류] 외부 접속 도구(ngrok 또는 cloudflared)를 찾을 수 없습니다.
echo.
pause

:END