@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ===================================================
echo   🏗️ 건설현장 공무 자재송장 & 작업일보 실행기
echo ===================================================
echo.

if not exist .venv\Scripts\activate.bat goto CREATE_VENV
goto START_APP

:CREATE_VENV
echo [안내] 가상환경을 생성하고 필수 라이브러리를 설치합니다...
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 goto ERROR_INSTALL
goto START_APP

:START_APP
call .venv\Scripts\activate.bat
echo 대시보드 서버를 시작합니다... (포트: 8501)
echo 잠시 후 기본 웹 브라우저(Chrome/Edge)가 자동으로 열립니다!
echo.
echo 접속 주소: http://localhost:8501
echo (서버를 종료하려면 이 창에서 Ctrl+C를 누르거나 창을 닫으세요)
echo ===================================================
echo.
python -m streamlit run app.py --server.headless false
if errorlevel 1 goto ERROR_RUN
goto END

:ERROR_INSTALL
echo.
echo [오류] 필수 라이브러리 설치에 실패했습니다.
pause
goto END

:ERROR_RUN
echo.
echo [오류] 프로그램 실행이 중단되었습니다.
pause
goto END

:END