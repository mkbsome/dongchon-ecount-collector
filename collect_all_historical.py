# -*- coding: utf-8 -*-
"""
E-count 전체 기간 데이터 수집 스크립트
- 2024-01 ~ 2026-03 (27개월)
- 판매현황, 구매현황, 생산입고현황
- PostgreSQL RDS 직접 업로드
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

# 프로젝트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ecount-collector'))
import config
from browser.ecount import EcountBrowser

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('collect_all.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# RDS 연결 정보
DB_CONFIG = {
    'host': 'triflow-db.cn88cwwm6cgt.ap-northeast-2.rds.amazonaws.com',
    'port': 5432,
    'database': 'triflow_ai',
    'user': 'triflow_admin',
    'password': 'tri878993+'
}

def get_db_connection():
    """PostgreSQL 연결"""
    return psycopg2.connect(**DB_CONFIG)

def select_dropdown_value(browser, button_index, data_id, target_value):
    """드롭다운에서 값 선택 (메인 페이지에서 실행)"""
    # 메인 페이지로 전환
    browser.driver.switch_to.default_content()

    # 버튼 클릭해서 드롭다운 열기
    browser.driver.execute_script(f'''
        const btns = document.querySelectorAll('button.btn-selectbox[data-id="{data_id}"]');
        if (btns[{button_index}]) btns[{button_index}].click();
    ''')
    time.sleep(0.5)

    # 드롭다운에서 값 선택
    result = browser.driver.execute_script(f'''
        const dropdown = document.querySelector('.dropdown-menu.show');
        if (dropdown) {{
            const items = dropdown.querySelectorAll('li a');
            for (const item of items) {{
                if (item.textContent.trim() === '{target_value}') {{
                    item.click();
                    return 'selected: ' + item.textContent.trim();
                }}
            }}
            return 'not found in dropdown';
        }}
        return 'no dropdown';
    ''')
    time.sleep(0.3)
    return result

def set_date_range(browser, year, month):
    """날짜 범위 설정 (시작일과 종료일 - 년월만)"""
    year_str = str(year)
    month_str = str(month).zfill(2)

    # 메인 페이지로 전환
    browser.driver.switch_to.default_content()

    # 시작일 설정 (버튼 인덱스: year=0, month=0)
    r1 = select_dropdown_value(browser, 0, "year", year_str)   # 시작 년도
    r2 = select_dropdown_value(browser, 0, "month", month_str)  # 시작 월

    # 종료일 설정 (버튼 인덱스: year=1, month=1)
    r3 = select_dropdown_value(browser, 1, "year", year_str)   # 종료 년도
    r4 = select_dropdown_value(browser, 1, "month", month_str)  # 종료 월

    logger.info(f"날짜 설정: {year}-{month_str} (결과: {r1}, {r2}, {r3}, {r4})")

def upload_sales_to_db(file_path, conn):
    """판매현황 데이터 업로드 (집계 후 UPSERT)"""
    df = pd.read_excel(file_path, header=1)
    df = df.dropna(how='all')

    cur = conn.cursor()
    sales_agg = {}

    for _, row in df.iterrows():
        raw_date = str(row.get('일자-No.', ''))
        match = re.match(r'(\d{4}/\d{2}/\d{2})\s*(-?\d+)?', raw_date)
        if not match:
            continue

        date_val = match.group(1).replace('/', '-')
        doc_no = match.group(2) if match.group(2) else ''
        product = str(row.get('품목명', ''))[:200]
        key = (date_val, doc_no, product)

        if key not in sales_agg:
            sales_agg[key] = {
                'spec': str(row.get('규격', ''))[:100] if pd.notna(row.get('규격')) else '',
                'quantity': 0,
                'unit_price': float(row.get('단가', 0)) if pd.notna(row.get('단가')) else 0,
                'supply_amount': 0,
                'vat': 0,
                'total': 0,
                'customer_name': str(row.get('거래처', ''))[:200] if pd.notna(row.get('거래처')) else '',
                'customer_code': str(row.get('거래처코드', ''))[:50] if pd.notna(row.get('거래처코드')) else ''
            }

        # 수량 합산
        sales_agg[key]['quantity'] += float(row.get('수량', 0)) if pd.notna(row.get('수량')) else 0
        sales_agg[key]['supply_amount'] += float(row.get('공급가액', 0)) if pd.notna(row.get('공급가액')) else 0
        sales_agg[key]['vat'] += float(row.get('부가세', 0)) if pd.notna(row.get('부가세')) else 0
        sales_agg[key]['total'] += float(row.get('합계', 0)) if pd.notna(row.get('합계')) else 0

    # UPSERT
    for (date_val, doc_no, product), data in sales_agg.items():
        cur.execute('''
            INSERT INTO core.ecount_sales (date, doc_no, product_name, spec, quantity, unit_price, supply_amount, vat, total, customer_name, customer_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date, doc_no, product_name) DO UPDATE SET
                quantity = EXCLUDED.quantity,
                supply_amount = EXCLUDED.supply_amount,
                vat = EXCLUDED.vat,
                total = EXCLUDED.total,
                collected_at = CURRENT_TIMESTAMP
        ''', (date_val, doc_no, product, data['spec'], data['quantity'], data['unit_price'],
              data['supply_amount'], data['vat'], data['total'], data['customer_name'], data['customer_code']))

    conn.commit()
    return len(sales_agg)

def upload_purchase_to_db(file_path, conn):
    """구매현황 데이터 업로드"""
    df = pd.read_excel(file_path, header=1)
    df = df.dropna(how='all')

    cur = conn.cursor()
    purchase_agg = {}

    for _, row in df.iterrows():
        raw_date = str(row.get('일자-No.', ''))
        match = re.match(r'(\d{4}/\d{2}/\d{2})\s*(-?\d+)?', raw_date)
        if not match:
            continue

        date_val = match.group(1).replace('/', '-')
        doc_no = match.group(2) if match.group(2) else ''
        product = str(row.get('품목명', ''))[:200]
        key = (date_val, doc_no, product)

        if key not in purchase_agg:
            purchase_agg[key] = {
                'spec': str(row.get('규격', ''))[:100] if pd.notna(row.get('규격')) else '',
                'quantity': 0,
                'unit_price': float(row.get('단가', 0)) if pd.notna(row.get('단가')) else 0,
                'supply_amount': 0,
                'vat': 0,
                'total': 0,
                'supplier_name': str(row.get('거래처', ''))[:200] if pd.notna(row.get('거래처')) else '',
                'supplier_code': str(row.get('거래처코드', ''))[:50] if pd.notna(row.get('거래처코드')) else ''
            }

        purchase_agg[key]['quantity'] += float(row.get('수량', 0)) if pd.notna(row.get('수량')) else 0
        purchase_agg[key]['supply_amount'] += float(row.get('공급가액', 0)) if pd.notna(row.get('공급가액')) else 0
        purchase_agg[key]['vat'] += float(row.get('부가세', 0)) if pd.notna(row.get('부가세')) else 0
        purchase_agg[key]['total'] += float(row.get('합계', 0)) if pd.notna(row.get('합계')) else 0

    for (date_val, doc_no, product), data in purchase_agg.items():
        cur.execute('''
            INSERT INTO core.ecount_purchase (date, doc_no, product_name, spec, quantity, unit_price, supply_amount, vat, total, supplier_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date, doc_no, product_name) DO UPDATE SET
                quantity = EXCLUDED.quantity,
                supply_amount = EXCLUDED.supply_amount,
                vat = EXCLUDED.vat,
                total = EXCLUDED.total,
                collected_at = CURRENT_TIMESTAMP
        ''', (date_val, doc_no, product, data['spec'], data['quantity'], data['unit_price'],
              data['supply_amount'], data['vat'], data['total'], data['supplier_name']))

    conn.commit()
    return len(purchase_agg)

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

def download_month_data(browser, menu_key, year, month):
    """한 달치 데이터 다운로드 - 바로 file_path 반환"""
    menu_config = config.MENU_CONFIG.get(menu_key)
    if not menu_config:
        return None

    # 페이지 리셋
    browser.reset_to_dashboard()

    # 메뉴 이동
    sub_tab_ids = {
        "영업관리": "MENUTREE_000030",
        "구매관리": "MENUTREE_000031",
        "생산/외주": "MENUTREE_000032"
    }

    browser.go_to_inventory_menu()
    sub_tab_id = sub_tab_ids.get(menu_config["tab"])
    if sub_tab_id:
        browser.go_to_sub_tab(sub_tab_id)
    browser.navigate_to_menu(menu_config["menu_id"], menu_config["name"])
    time.sleep(2)

    # 날짜 설정
    set_date_range(browser, year, month)
    time.sleep(1)

    # 검색
    browser.click_search()
    time.sleep(3)

    # 다운로드 - 바로 파일 경로 반환 (파일 이동 없이)
    file_path = browser.download_excel()
    return file_path

def collect_all_data():
    """전체 데이터 수집 및 업로드"""
    # 기간: 2024-01 ~ 2026-03 (27개월)
    months = []
    for year in [2024, 2025]:
        for month in range(1, 13):
            months.append((year, month))
    for month in range(1, 4):  # 2026년 1~3월
        months.append((2026, month))

    logger.info(f"수집 기간: {len(months)}개월")

    # DB 연결
    conn = get_db_connection()
    logger.info("DB 연결 성공")

    # 수집 함수 매핑
    upload_funcs = {
        'sales': upload_sales_to_db,
        'purchase': upload_purchase_to_db,
        'production': upload_production_to_db
    }

    results = {'sales': 0, 'purchase': 0, 'production': 0}

    try:
        with EcountBrowser() as browser:
            browser.login()
            time.sleep(3)

            # 판매현황은 이미 완료됨, 구매/생산만 수집
            for menu_key in ['purchase', 'production']:
                logger.info(f"\n{'='*50}")
                logger.info(f"=== {menu_key.upper()} 데이터 수집 시작 ===")
                logger.info(f"{'='*50}")

                for year, month in months:
                    try:
                        logger.info(f"[{menu_key}] {year}-{str(month).zfill(2)} 처리 중...")

                        file_path = download_month_data(browser, menu_key, year, month)

                        if file_path and os.path.exists(file_path):
                            count = upload_funcs[menu_key](file_path, conn)
                            results[menu_key] += count
                            logger.info(f"[{menu_key}] {year}-{str(month).zfill(2)}: {count}건 업로드")
                            # 업로드 후 파일 삭제 (정리)
                            try:
                                os.remove(file_path)
                            except:
                                pass
                        else:
                            logger.warning(f"[{menu_key}] {year}-{str(month).zfill(2)}: 데이터 없음")

                    except Exception as e:
                        logger.error(f"[{menu_key}] {year}-{str(month).zfill(2)} 오류: {e}")
                        continue

    finally:
        conn.close()

    logger.info(f"\n{'='*50}")
    logger.info("=== 수집 완료 ===")
    logger.info(f"판매현황: {results['sales']}건")
    logger.info(f"구매현황: {results['purchase']}건")
    logger.info(f"생산입고: {results['production']}건")
    logger.info(f"{'='*50}")

    return results

if __name__ == "__main__":
    collect_all_data()
