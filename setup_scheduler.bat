@echo off
chcp 65001 >nul
echo ============================================
echo E-count 자동 수집기 스케줄러 설정
echo ============================================
echo.

:: 현재 디렉토리 확인
set "SCRIPT_DIR=%~dp0"
set "VBS_FILE=%SCRIPT_DIR%run_collector_silent.vbs"

echo 설치 경로: %SCRIPT_DIR%
echo 실행 파일: %VBS_FILE% (백그라운드 실행)
echo.

:: 기존 작업 삭제 (있으면)
schtasks /delete /tn "EcountAutoCollector" /f >nul 2>&1

:: 새 작업 생성 - 매일 12:30에 실행 (VBS로 백그라운드 실행)
schtasks /create ^
    /tn "EcountAutoCollector" ^
    /tr "wscript.exe \"%VBS_FILE%\"" ^
    /sc daily ^
    /st 12:30 ^
    /rl highest ^
    /f

if %errorlevel% equ 0 (
    echo.
    echo [성공] 작업 스케줄러 등록 완료!
    echo.
    echo 설정 내용:
    echo   - 작업 이름: EcountAutoCollector
    echo   - 실행 시간: 매일 오후 12:30
    echo   - 실행 방식: 백그라운드 (창 없음)
    echo.
    echo 확인 방법:
    echo   1. Windows 검색에서 "작업 스케줄러" 실행
    echo   2. "작업 스케줄러 라이브러리"에서 "EcountAutoCollector" 확인
    echo.
    echo 로그 확인:
    echo   - collector_scheduler.log 파일 확인
    echo.
) else (
    echo.
    echo [실패] 작업 스케줄러 등록 실패
    echo 관리자 권한으로 다시 실행해주세요.
    echo.
)

pause
