# -*- coding: utf-8 -*-
"""
Selenium WebDriver 관리
"""

import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import config


def create_driver():
    """Chrome WebDriver 생성"""
    options = Options()

    # 다운로드 폴더 설정 - 한글 경로 문제 해결을 위해 사용자 홈 폴더 사용
    download_dir = config.DOWNLOAD_DIR

    # 한글 경로가 포함된 경우 사용자 홈 폴더 사용
    try:
        download_dir.encode('ascii')
    except UnicodeEncodeError:
        # 한글 경로인 경우 사용자 홈 폴더 내에 다운로드 폴더 생성
        home_dir = os.path.expanduser("~")
        download_dir = os.path.join(home_dir, "ecount_downloads")

    os.makedirs(download_dir, exist_ok=True)

    # 전역 변수로 실제 다운로드 경로 저장 (다른 모듈에서 사용)
    config.ACTUAL_DOWNLOAD_DIR = download_dir

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    # 헤드리스 모드 설정
    if config.CHROME_HEADLESS:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")

    # 기타 옵션
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--start-minimized")  # 최소화 상태로 시작

    # 자동 드라이버 설치 및 실행
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.implicitly_wait(config.ELEMENT_WAIT_TIMEOUT)
    driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)

    return driver


def close_driver(driver):
    """WebDriver 종료"""
    if driver:
        try:
            driver.quit()
        except Exception:
            pass
