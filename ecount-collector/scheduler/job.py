# -*- coding: utf-8 -*-
"""
스케줄러 및 작업 관리
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Optional
import schedule

import config
from browser.ecount import EcountBrowser
from parser.excel_parser import ExcelParser
from api.client import APIClient

logger = logging.getLogger(__name__)


class EcountScheduler:
    """E카운트 데이터 수집 스케줄러"""

    def __init__(self):
        self.api_client = APIClient()
        self.last_run_date: Optional[str] = None
        self.is_running = False

    def run_collection(self):
        """데이터 수집 실행"""
        if self.is_running:
            logger.info("Collection already running, skipping")
            return

        self.is_running = True
        today = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Starting data collection for {today}")

        try:
            with EcountBrowser() as browser:
                # 로그인
                if not browser.login():
                    logger.error("Login failed")
                    return

                # 각 리포트 다운로드 및 처리
                for menu_key in config.MENU_CONFIG.keys():
                    try:
                        self._process_report(browser, menu_key)
                    except Exception as e:
                        logger.error(f"Failed to process {menu_key}: {e}")

            self.last_run_date = today
            logger.info(f"Collection completed for {today}")

        except Exception as e:
            logger.error(f"Collection failed: {e}")
        finally:
            self.is_running = False

    def _process_report(self, browser: EcountBrowser, menu_key: str):
        """리포트 다운로드 및 처리"""
        logger.info(f"Processing {menu_key}...")

        # 날짜 범위 결정 (누락된 날짜 확인)
        end_date = datetime.now()
        start_date = self._get_start_date(menu_key, end_date)

        # 다운로드
        file_path = browser.download_report(menu_key, start_date, end_date)
        if not file_path:
            logger.warning(f"No file downloaded for {menu_key}")
            return

        logger.info(f"Downloaded: {file_path}")

        # 파싱
        records = ExcelParser.parse(file_path, menu_key)
        logger.info(f"Parsed {len(records)} records from {menu_key}")

        # 업로드
        if records:
            result = self.api_client.upload(menu_key, records)
            logger.info(f"Upload result for {menu_key}: {result}")

    def _get_start_date(self, menu_key: str, end_date: datetime) -> datetime:
        """시작 날짜 결정 (누락된 날짜 포함)"""
        # API에서 마지막 동기화 날짜 조회
        last_sync = self.api_client.get_last_sync_date(menu_key)

        if last_sync:
            try:
                last_date = datetime.strptime(last_sync, "%Y-%m-%d")
                # 마지막 동기화 다음 날부터
                return last_date + timedelta(days=1)
            except ValueError:
                pass

        # 기본값: 이번 달 1일
        return end_date.replace(day=1)

    def check_and_run(self):
        """시간 확인 후 실행"""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        # 이미 오늘 실행했는지 확인
        if self.last_run_date == today:
            return

        # 12시~13시 사이인지 확인
        if config.SCHEDULE_START_HOUR <= now.hour < config.SCHEDULE_END_HOUR:
            self._try_run_with_retry()

    def _try_run_with_retry(self):
        """재시도 로직 포함 실행"""
        for attempt in range(config.RETRY_COUNT):
            try:
                self.run_collection()
                return  # 성공하면 종료
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < config.RETRY_COUNT - 1:
                    logger.info(f"Retrying in {config.RETRY_INTERVAL} seconds...")
                    time.sleep(config.RETRY_INTERVAL)

    def start(self):
        """스케줄러 시작"""
        logger.info("Starting scheduler...")

        # 매 분마다 시간 체크
        schedule.every(1).minutes.do(self.check_and_run)

        # 무한 루프
        while True:
            schedule.run_pending()
            time.sleep(30)

    def run_once(self):
        """즉시 1회 실행 (테스트용)"""
        self.run_collection()
