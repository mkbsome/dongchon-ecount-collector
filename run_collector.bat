@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [%date% %time%] E-count 자동 수집 시작 >> collector_scheduler.log

python auto_collector.py >> collector_scheduler.log 2>&1

echo [%date% %time%] E-count 자동 수집 완료 >> collector_scheduler.log
echo. >> collector_scheduler.log
