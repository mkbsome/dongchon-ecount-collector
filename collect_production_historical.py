# -*- coding: utf-8 -*-
"""
생산입고현황 전체 기간 데이터 수집 스크립트
- 2024-01 ~ 2026-03 (27개월)
- PostgreSQL RDS 직접 업로드
- 생산입고현황 페이지는 data-id가 없어서 인덱스로 접근
"""

import os
import sys
import time
import re
import glob
import logging
from datetime import datetime

import pandas as pd
import psycopg2
from selenium.webdriver.common.by import By

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ecount-collector'))
import config
from browser.ecount import EcountBrowser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('collect_production.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'triflow-db.cn88cwwm6cgt.ap-northeast-2.rds.amazonaws.com',
    'port': 5432,
    'database': 'triflow_ai',
    'user': 'triflow_admin',
    'password': 'tri878993+'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def select_production_date(browser, button_index, target_value):
    """생산입고현황 페이지에서 날짜 선택 (wrapper-datepicker 내부 버튼)
    버튼 인덱스 (wrapper-datepicker 내):
    - 0: 시작 년도
    - 1: 시작 월
    - 2: 종료 년도
    - 3: 종료 월
    """
    browser.driver.switch_to.default_content()

    # wrapper-datepicker 내의 버튼 클릭
    browser.driver.execute_script(f'''
        const wrapper = document.querySelector('.wrapper-datepicker');
        const btns = wrapper.querySelectorAll('button.btn-selectbox');
        if (btns[{button_index}]) btns[{button_index}].click();
    ''')
    time.sleep(0.5)

    # 드롭다운에서 값 선택 (dropdown-menu-selectbox 클래스 사용)
    result = browser.driver.execute_script(f'''
        const dropdown = document.querySelector('.dropdown-menu-selectbox');
        if (dropdown) {{
            const items = dropdown.querySelectorAll('li a, li');
            for (const item of items) {{
                if (item.textContent.trim() === '{target_value}') {{
                    item.click();
                    return 'selected: ' + item.textContent.trim();
                }}
            }}
            // 값을 찾지 못한 경우 드롭다운 닫기
            document.body.click();
            return 'not found in: ' + Array.from(items).map(i => i.textContent.trim()).slice(0, 5).join(',');
        }}
        return 'no dropdown';
    ''')
    time.sleep(0.3)
    return result

def set_production_date_range(browser, year, month):
    """생산입고현황 날짜 범위 설정"""
    year_str = str(year)
    month_str = str(month).zfill(2)

    browser.driver.switch_to.default_content()

    # wrapper-datepicker 내 버튼 인덱스: 0=시작년, 1=시작월, 2=종료년, 3=종료월
    r1 = select_production_date(browser, 0, year_str)   # 시작 년도
    r2 = select_production_date(browser, 1, month_str)  # 시작 월
    r3 = select_production_date(browser, 2, year_str)   # 종료 년도
    r4 = select_production_date(browser, 3, month_str)  # 종료 월

    logger.info(f"날짜 설정: {year}-{month_str} (결과: {r1}, {r2}, {r3}, {r4})")
    return all('selected' in str(r) for r in [r1, r2, r3, r4])

def upload_production_to_db(file_path, conn):
    """생산입고현황 데이터 업로드"""
    df = pd.read_excel(file_path, header=1)
    df = df.dropna(how='all')

    cur = conn.cursor()
    production_agg = {}

    for _, row in df.iterrows():
        raw_date = str(row.get('일자-No.', ''))
        match = re.match(r'(\d{4}/\d{2}/\d{2})\s*(-?\d+)?', raw_date)
        if not match:
            continue

        date_val = match.group(1).replace('/', '-')
        doc_no = match.group(2) if match.group(2) else ''
        product = str(row.get('품목명', ''))[:200]
        key = (date_val, doc_no, product)

        if key not in production_agg:
            production_agg[key] = {
                'spec': str(row.get('규격', ''))[:100] if pd.notna(row.get('규격')) else '',
                'quantity': 0,
                'production_amount': 0,
                'from_warehouse': str(row.get('출고창고', ''))[:100] if pd.notna(row.get('출고창고')) else '',
                'to_warehouse': str(row.get('입고창고', ''))[:100] if pd.notna(row.get('입고창고')) else '',
                'memo': str(row.get('비고', ''))[:500] if pd.notna(row.get('비고')) else ''
            }

        production_agg[key]['quantity'] += float(row.get('수량', 0)) if pd.notna(row.get('수량')) else 0
        production_agg[key]['production_amount'] += float(row.get('금액', 0)) if pd.notna(row.get('금액')) else 0

    for (date_val, doc_no, product), data in production_agg.items():
        cur.execute('''
            INSERT INTO core.ecount_production (date, doc_no, product_name, spec, quantity, from_warehouse, to_warehouse, production_amount, memo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date, doc_no, product_name) DO UPDATE SET
                quantity = EXCLUDED.quantity,
                production_amount = EXCLUDED.production_amount,
                collected_at = CURRENT_TIMESTAMP
        ''', (date_val, doc_no, product, data['spec'], data['quantity'], data['from_warehouse'],
              data['to_warehouse'], data['production_amount'], data['memo']))

    conn.commit()
    return len(production_agg)

def download_production_month(browser, year, month):
    """한 달치 생산입고 데이터 다운로드"""
    # 페이지 리셋
    browser.reset_to_dashboard()

    # 메뉴 이동
    browser.go_to_inventory_menu()
    browser.go_to_sub_tab("MENUTREE_000032")  # 생산/외주
    browser.navigate_to_menu("MENUTREE_000534", "생산입고현황")
    time.sleep(2)

    # 날짜 설정
    success = set_production_date_range(browser, year, month)
    if not success:
        logger.warning(f"날짜 설정 실패: {year}-{month}")
    time.sleep(1)

    # 검색
    browser.click_search()
    time.sleep(3)

    # 다운로드
    file_path = browser.download_excel()
    return file_path

def collect_production_data():
    """생산입고 데이터 수집"""
    # 기간: 2024-01 ~ 2026-03 (27개월)
    months = []
    for year in [2024, 2025]:
        for month in range(1, 13):
            months.append((year, month))
    for month in range(1, 4):
        months.append((2026, month))

    logger.info(f"수집 기간: {len(months)}개월")

    conn = get_db_connection()
    logger.info("DB 연결 성공")

    total_count = 0

    try:
        with EcountBrowser() as browser:
            browser.login()
            time.sleep(3)

            logger.info("\n" + "="*50)
            logger.info("=== 생산입고현황 데이터 수집 시작 ===")
            logger.info("="*50)

            for year, month in months:
                try:
                    logger.info(f"[production] {year}-{str(month).zfill(2)} 처리 중...")

                    file_path = download_production_month(browser, year, month)

                    if file_path and os.path.exists(file_path):
                        count = upload_production_to_db(file_path, conn)
                        total_count += count
                        logger.info(f"[production] {year}-{str(month).zfill(2)}: {count}건 업로드")
                        try:
                            os.remove(file_path)
                        except:
                            pass
                    else:
                        logger.warning(f"[production] {year}-{str(month).zfill(2)}: 데이터 없음")

                except Exception as e:
                    logger.error(f"[production] {year}-{str(month).zfill(2)} 오류: {e}")
                    continue

    finally:
        conn.close()

    logger.info(f"\n{'='*50}")
    logger.info("=== 수집 완료 ===")
    logger.info(f"생산입고: {total_count}건")
    logger.info(f"{'='*50}")

    return total_count

if __name__ == "__main__":
    collect_production_data()
