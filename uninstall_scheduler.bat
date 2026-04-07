@echo off
chcp 65001 >nul
echo ============================================
echo E-count 자동 수집기 스케줄러 제거
echo ============================================
echo.

schtasks /delete /tn "EcountAutoCollector" /f

if %errorlevel% equ 0 (
    echo [성공] 작업 스케줄러에서 제거되었습니다.
) else (
    echo [알림] 등록된 작업이 없거나 이미 제거되었습니다.
)

echo.
pause
