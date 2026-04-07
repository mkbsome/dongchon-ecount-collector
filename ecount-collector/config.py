# -*- coding: utf-8 -*-
"""
E카운트 자동 데이터 수집기 설정
"""

# E카운트 로그인 정보
ECOUNT_LOGIN_URL = "https://login.ecount.com/"
ECOUNT_COMPANY_CODE = "623943"
ECOUNT_USER_ID = "AI파일럿"
ECOUNT_PASSWORD = "dongchonfs4511"

# 다운로드할 메뉴 정보
# URL 패턴: https://sbo.ecount.com/ECERP/ECMENU/...
MENU_CONFIG = {
    "sales": {
        "name": "판매현황",
        "menu_id": "MENUTREE_000494",
        "program_id": "E040205",  # 판매현황 프로그램 ID
        "tab": "영업관리",
        "file_prefix": "sales"
    },
    "purchase": {
        "name": "구매현황",
        "menu_id": "MENUTREE_000513",
        "program_id": "E040405",  # 구매현황 프로그램 ID
        "tab": "구매관리",
        "file_prefix": "purchase"
    },
    "production": {
        "name": "생산입고현황",
        "menu_id": "MENUTREE_000534",
        "program_id": "E050305",  # 생산입고현황 프로그램 ID
        "tab": "생산/외주",
        "file_prefix": "production"
    }
}

# 스케줄 설정
SCHEDULE_START_HOUR = 12  # 12시
SCHEDULE_END_HOUR = 13    # 1시
RETRY_COUNT = 3           # 재시도 횟수
RETRY_INTERVAL = 300      # 재시도 간격 (초)

# 파일 경로 설정
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# REST API 설정 (나중에 채워넣기)
API_BASE_URL = ""
API_KEY = ""

# 크롬 드라이버 설정
CHROME_HEADLESS = False  # 디버깅 시 False, 운영 시 True
CHROME_DOWNLOAD_DIR = DOWNLOAD_DIR
PAGE_LOAD_TIMEOUT = 30
ELEMENT_WAIT_TIMEOUT = 10
