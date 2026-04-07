# -*- coding: utf-8 -*-
"""
E카운트 자동 데이터 수집기
메인 실행 파일
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from scheduler.job import EcountScheduler


def setup_logging():
    """로깅 설정"""
    os.makedirs(config.LOG_DIR, exist_ok=True)

    log_file = os.path.join(
        config.LOG_DIR,
        f"ecount_{datetime.now().strftime('%Y%m%d')}.log"
    )

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='E카운트 자동 데이터 수집기')
    parser.add_argument('--once', action='store_true', help='즉시 1회 실행')
    parser.add_argument('--daemon', action='store_true', help='백그라운드 스케줄러 실행')
    parser.add_argument('--test-login', action='store_true', help='로그인 테스트')
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("E카운트 자동 데이터 수집기 시작")
    logger.info("=" * 50)

    scheduler = EcountScheduler()

    if args.test_login:
        # 로그인 테스트
        from browser.ecount import EcountBrowser
        with EcountBrowser() as browser:
            if browser.login():
                logger.info("로그인 성공!")
                time.sleep(5)  # 5초 대기 후 종료
            else:
                logger.error("로그인 실패")

    elif args.once:
        # 즉시 1회 실행
        scheduler.run_once()

    elif args.daemon:
        # 백그라운드 스케줄러 실행
        logger.info(f"스케줄러 시작 - 매일 {config.SCHEDULE_START_HOUR}시~{config.SCHEDULE_END_HOUR}시 실행")
        scheduler.start()

    else:
        # 기본: 즉시 1회 실행
        scheduler.run_once()


if __name__ == "__main__":
    main()
