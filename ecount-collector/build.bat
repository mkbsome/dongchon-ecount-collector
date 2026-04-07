@echo off
echo E카운트 자동 데이터 수집기 빌드
echo ================================

REM 가상환경 생성 (없으면)
if not exist "venv" (
    echo 가상환경 생성 중...
    python -m venv venv
)

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM 패키지 설치
echo 패키지 설치 중...
pip install -r requirements.txt

REM PyInstaller로 exe 빌드
echo exe 빌드 중...
pyinstaller --onefile --noconsole --name EcountCollector ^
    --add-data "config.py;." ^
    --hidden-import=selenium ^
    --hidden-import=webdriver_manager ^
    --hidden-import=pandas ^
    --hidden-import=openpyxl ^
    main.py

echo.
echo 빌드 완료!
echo 실행 파일: dist\EcountCollector.exe
pause
