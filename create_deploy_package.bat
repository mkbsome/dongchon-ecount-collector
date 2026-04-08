@echo off
chcp 65001 >nul
echo ============================================
echo E-count 자동 수집기 배포 패키지 생성
echo ============================================
echo.

set "SOURCE=%~dp0"
set "DEPLOY=%SOURCE%deploy_package"

:: 기존 배포 폴더 삭제
if exist "%DEPLOY%" rmdir /s /q "%DEPLOY%"

:: 배포 폴더 생성
mkdir "%DEPLOY%"
mkdir "%DEPLOY%\ecount-collector"
mkdir "%DEPLOY%\ecount-collector\browser"
mkdir "%DEPLOY%\ecount-collector\debug"
mkdir "%DEPLOY%\ecount-collector\downloads"
mkdir "%DEPLOY%\ecount-collector\logs"

:: 메인 파일 복사
copy "%SOURCE%auto_collector.py" "%DEPLOY%\"
copy "%SOURCE%run_collector.bat" "%DEPLOY%\"
copy "%SOURCE%run_collector_silent.vbs" "%DEPLOY%\"
copy "%SOURCE%setup_scheduler.bat" "%DEPLOY%\"
copy "%SOURCE%uninstall_scheduler.bat" "%DEPLOY%\"
copy "%SOURCE%설치가이드.txt" "%DEPLOY%\"

:: ecount-collector 모듈 복사
copy "%SOURCE%ecount-collector\config.py" "%DEPLOY%\ecount-collector\"
copy "%SOURCE%ecount-collector\__init__.py" "%DEPLOY%\ecount-collector\" 2>nul
copy "%SOURCE%ecount-collector\browser\*.py" "%DEPLOY%\ecount-collector\browser\"

echo.
echo [완료] 배포 패키지가 생성되었습니다.
echo 위치: %DEPLOY%
echo.
echo 포함된 파일:
dir /b "%DEPLOY%"
echo.
pause
