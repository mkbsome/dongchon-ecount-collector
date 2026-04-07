# -*- coding: utf-8 -*-
"""
E-count 자동 데이터 수집기
- DB에서 마지막 수집 일자 확인
- 마지막 일자 ~ 오늘까지 데이터 수집
- 수집 로그 기록
"""

import os
import sys
import time
import re
import glob
import logging
from datetime import datetime, timedelta

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ecount-collector'))
import config
from browser.ecount import EcountBrowser

# 로깅 설정
log_dir = os.path.dirname(__file__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, 'auto_collector.log'), encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# DB 설정
DB_CONFIG = {
    'host': 'triflow-db.cn88cwwm6cgt.ap-northeast-2.rds.amazonaws.com',
    'port': 5432,
    'database': 'triflow_ai',
    'user': 'triflow_admin',
    'password': 'tri878993+'
}

# RDS 스키마
DB_SCHEMA = 'core'

# 테이블 설정
TABLE_CONFIG = {
    'sales': {
        'table': f'{DB_SCHEMA}.ecount_sales',
        'menu_key': 'sales',
        'tab_id': 'MENUTREE_000030',  # 영업관리
        'menu_id': 'MENUTREE_000494',  # 판매현황
        'menu_name': '판매현황',
        'date_selector': 'standard'  # data-id="year", "month" 사용
    },
    'purchase': {
        'table': f'{DB_SCHEMA}.ecount_purchase',
        'menu_key': 'purchase',
        'tab_id': 'MENUTREE_000031',  # 구매관리
        'menu_id': 'MENUTREE_000513',
        'menu_name': '구매현황',
        'date_selector': 'standard'
    },
    'production': {
        'table': f'{DB_SCHEMA}.ecount_production',
        'menu_key': 'production',
        'tab_id': 'MENUTREE_000032',  # 생산/외주
        'menu_id': 'MENUTREE_000534',
        'menu_name': '생산입고현황',
        'date_selector': 'wrapper'  # wrapper-datepicker 사용
    }
}


def get_db_connection():
    """DB 연결"""
    return psycopg2.connect(**DB_CONFIG)


def init_log_table(conn):
    """수집 로그 테이블 생성"""
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS core.ecount_collection_log (
            id SERIAL PRIMARY KEY,
            data_type VARCHAR(50) NOT NULL,
            target_date DATE NOT NULL,
            records_count INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'pending',
            error_message TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            UNIQUE(data_type, target_date)
        )
    ''')
    conn.commit()
    logger.info("수집 로그 테이블 준비 완료")


def get_last_collected_date(conn, data_type):
    """마지막 수집 일자 조회"""
    table_name = TABLE_CONFIG[data_type]['table']
    cur = conn.cursor()

    # 데이터 테이블에서 최대 날짜 확인
    cur.execute(f'SELECT MAX(date) FROM {table_name}')
    result = cur.fetchone()[0]

    if result:
        logger.info(f"[{data_type}] 마지막 데이터 일자: {result}")
        return result
    else:
        # 데이터가 없으면 2024-01-01부터
        logger.info(f"[{data_type}] 기존 데이터 없음, 2024-01-01부터 시작")
        return datetime(2024, 1, 1).date()


def get_months_to_collect(last_date, today=None):
    """수집이 필요한 월 목록 반환"""
    if today is None:
        today = datetime.now().date()

    months = []
    current = datetime(last_date.year, last_date.month, 1).date()
    end = datetime(today.year, today.month, 1).date()

    while current <= end:
        months.append((current.year, current.month))
        # 다음 월
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1).date()
        else:
            current = datetime(current.year, current.month + 1, 1).date()

    return months


def log_collection_start(conn, data_type, target_date):
    """수집 시작 로그"""
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO core.ecount_collection_log (data_type, target_date, status, started_at)
        VALUES (%s, %s, 'running', CURRENT_TIMESTAMP)
        ON CONFLICT (data_type, target_date)
        DO UPDATE SET status = 'running', started_at = CURRENT_TIMESTAMP, error_message = NULL
    ''', (data_type, target_date))
    conn.commit()


def log_collection_complete(conn, data_type, target_date, records_count):
    """수집 완료 로그"""
    cur = conn.cursor()
    cur.execute('''
        UPDATE core.ecount_collection_log
        SET status = 'completed', records_count = %s, completed_at = CURRENT_TIMESTAMP
        WHERE data_type = %s AND target_date = %s
    ''', (records_count, data_type, target_date))
    conn.commit()


def log_collection_error(conn, data_type, target_date, error_message):
    """수집 오류 로그"""
    cur = conn.cursor()
    cur.execute('''
        UPDATE core.ecount_collection_log
        SET status = 'error', error_message = %s, completed_at = CURRENT_TIMESTAMP
        WHERE data_type = %s AND target_date = %s
    ''', (str(error_message)[:500], data_type, target_date))
    conn.commit()


# ===== 날짜 선택 함수 =====

def select_standard_date(browser, button_index, data_id, target_value):
    """표준 드롭다운 날짜 선택 (판매/구매현황)"""
    browser.driver.switch_to.default_content()

    browser.driver.execute_script(f'''
        const btns = document.querySelectorAll('button.btn-selectbox[data-id="{data_id}"]');
        if (btns[{button_index}]) btns[{button_index}].click();
    ''')
    time.sleep(0.5)

    result = browser.driver.execute_script(f'''
        const dropdown = document.querySelector('.dropdown-menu.show');
        if (dropdown) {{
            const items = dropdown.querySelectorAll('li a');
            for (const item of items) {{
                if (item.textContent.trim() === '{target_value}') {{
                    item.click();
                    return 'selected';
                }}
            }}
            return 'not found';
        }}
        return 'no dropdown';
    ''')
    time.sleep(0.3)
    return 'selected' in result


def select_wrapper_date(browser, button_index, target_value):
    """wrapper-datepicker 날짜 선택 (생산입고현황)"""
    browser.driver.switch_to.default_content()

    browser.driver.execute_script(f'''
        const wrapper = document.querySelector('.wrapper-datepicker');
        const btns = wrapper.querySelectorAll('button.btn-selectbox');
        if (btns[{button_index}]) btns[{button_index}].click();
    ''')
    time.sleep(0.5)

    result = browser.driver.execute_script(f'''
        const dropdown = document.querySelector('.dropdown-menu-selectbox');
        if (dropdown) {{
            const items = dropdown.querySelectorAll('li a, li');
            for (const item of items) {{
                if (item.textContent.trim() === '{target_value}') {{
                    item.click();
                    return 'selected';
                }}
            }}
            document.body.click();
            return 'not found';
        }}
        return 'no dropdown';
    ''')
    time.sleep(0.3)
    return 'selected' in result


def set_date_range(browser, data_type, year, month):
    """날짜 범위 설정"""
    cfg = TABLE_CONFIG[data_type]
    year_str = str(year)
    month_str = str(month).zfill(2)

    browser.driver.switch_to.default_content()

    if cfg['date_selector'] == 'standard':
        # 판매/구매현황: data-id="year", "month"
        r1 = select_standard_date(browser, 0, "year", year_str)
        r2 = select_standard_date(browser, 0, "month", month_str)
        r3 = select_standard_date(browser, 1, "year", year_str)
        r4 = select_standard_date(browser, 1, "month", month_str)
    else:
        # 생산입고현황: wrapper-datepicker
        r1 = select_wrapper_date(browser, 0, year_str)
        r2 = select_wrapper_date(browser, 1, month_str)
        r3 = select_wrapper_date(browser, 2, year_str)
        r4 = select_wrapper_date(browser, 3, month_str)

    success = all([r1, r2, r3, r4])
    logger.info(f"날짜 설정: {year}-{month_str} (성공: {success})")
    return success


# ===== 데이터 업로드 함수 =====

def upload_sales(file_path, conn):
    """판매현황 업로드"""
    df = pd.read_excel(file_path, header=1)
    df = df.dropna(how='all')

    cur = conn.cursor()
    agg = {}

    for _, row in df.iterrows():
        raw_date = str(row.get('일자-No.', ''))
        match = re.match(r'(\d{4}/\d{2}/\d{2})\s*(-?\d+)?', raw_date)
        if not match:
            continue

        date_val = match.group(1).replace('/', '-')
        doc_no = match.group(2) if match.group(2) else ''
        product = str(row.get('품목명', ''))[:200]
        key = (date_val, doc_no, product)

        if key not in agg:
            agg[key] = {
                'spec': str(row.get('규격', ''))[:100] if pd.notna(row.get('규격')) else '',
                'quantity': 0,
                'unit_price': float(row.get('단가', 0)) if pd.notna(row.get('단가')) else 0,
                'supply_amount': 0,
                'vat': 0,
                'total': 0,
                'customer_name': str(row.get('거래처', ''))[:200] if pd.notna(row.get('거래처')) else '',
                'customer_code': str(row.get('거래처코드', ''))[:50] if pd.notna(row.get('거래처코드')) else ''
            }

        agg[key]['quantity'] += float(row.get('수량', 0)) if pd.notna(row.get('수량')) else 0
        agg[key]['supply_amount'] += float(row.get('공급가액', 0)) if pd.notna(row.get('공급가액')) else 0
        agg[key]['vat'] += float(row.get('부가세', 0)) if pd.notna(row.get('부가세')) else 0
        agg[key]['total'] += float(row.get('합계', 0)) if pd.notna(row.get('합계')) else 0

    for (date_val, doc_no, product), data in agg.items():
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
    return len(agg)


def upload_purchase(file_path, conn):
    """구매현황 업로드"""
    df = pd.read_excel(file_path, header=1)
    df = df.dropna(how='all')

    cur = conn.cursor()
    agg = {}

    for _, row in df.iterrows():
        raw_date = str(row.get('일자-No.', ''))
        match = re.match(r'(\d{4}/\d{2}/\d{2})\s*(-?\d+)?', raw_date)
        if not match:
            continue

        date_val = match.group(1).replace('/', '-')
        doc_no = match.group(2) if match.group(2) else ''
        product = str(row.get('품목명', ''))[:200]
        key = (date_val, doc_no, product)

        if key not in agg:
            agg[key] = {
                'spec': str(row.get('규격', ''))[:100] if pd.notna(row.get('규격')) else '',
                'quantity': 0,
                'unit_price': float(row.get('단가', 0)) if pd.notna(row.get('단가')) else 0,
                'supply_amount': 0,
                'vat': 0,
                'total': 0,
                'supplier_name': str(row.get('거래처', ''))[:200] if pd.notna(row.get('거래처')) else ''
            }

        agg[key]['quantity'] += float(row.get('수량', 0)) if pd.notna(row.get('수량')) else 0
        agg[key]['supply_amount'] += float(row.get('공급가액', 0)) if pd.notna(row.get('공급가액')) else 0
        agg[key]['vat'] += float(row.get('부가세', 0)) if pd.notna(row.get('부가세')) else 0
        agg[key]['total'] += float(row.get('합계', 0)) if pd.notna(row.get('합계')) else 0

    for (date_val, doc_no, product), data in agg.items():
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
    return len(agg)


def upload_production(file_path, conn):
    """생산입고현황 업로드"""
    df = pd.read_excel(file_path, header=1)
    df = df.dropna(how='all')

    cur = conn.cursor()
    agg = {}

    for _, row in df.iterrows():
        raw_date = str(row.get('일자-No.', ''))
        match = re.match(r'(\d{4}/\d{2}/\d{2})\s*(-?\d+)?', raw_date)
        if not match:
            continue

        date_val = match.group(1).replace('/', '-')
        doc_no = match.group(2) if match.group(2) else ''
        product = str(row.get('품목명', ''))[:200]
        key = (date_val, doc_no, product)

        if key not in agg:
            agg[key] = {
                'spec': str(row.get('규격', ''))[:100] if pd.notna(row.get('규격')) else '',
                'quantity': 0,
                'production_amount': 0,
                'from_warehouse': str(row.get('출고창고', ''))[:100] if pd.notna(row.get('출고창고')) else '',
                'to_warehouse': str(row.get('입고창고', ''))[:100] if pd.notna(row.get('입고창고')) else '',
                'memo': str(row.get('비고', ''))[:500] if pd.notna(row.get('비고')) else ''
            }

        agg[key]['quantity'] += float(row.get('수량', 0)) if pd.notna(row.get('수량')) else 0
        agg[key]['production_amount'] += float(row.get('금액', 0)) if pd.notna(row.get('금액')) else 0

    for (date_val, doc_no, product), data in agg.items():
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
    return len(agg)


UPLOAD_FUNCS = {
    'sales': upload_sales,
    'purchase': upload_purchase,
    'production': upload_production
}


# ===== 메인 수집 함수 =====

def collect_month_data(browser, conn, data_type, year, month):
    """한 달치 데이터 수집"""
    cfg = TABLE_CONFIG[data_type]
    target_date = datetime(year, month, 1).date()

    # 수집 시작 로그
    log_collection_start(conn, data_type, target_date)

    try:
        # 페이지 이동 - go_to_inventory_menu()는 "재고 I" 탭으로 가므로
        # 먼저 대시보드 리셋 후 바로 sub_tab으로 이동
        browser.reset_to_dashboard()
        time.sleep(1)
        browser.go_to_inventory_menu()  # 메뉴 영역 활성화
        time.sleep(0.5)
        browser.go_to_sub_tab(cfg['tab_id'])  # 영업관리/구매관리/생산외주 탭 이동
        time.sleep(1)
        browser.navigate_to_menu(cfg['menu_id'], cfg['menu_name'])
        time.sleep(2)

        # 날짜 설정
        set_date_range(browser, data_type, year, month)
        time.sleep(1)

        # 검색
        browser.click_search()
        time.sleep(3)

        # 다운로드
        file_path = browser.download_excel()

        if file_path and os.path.exists(file_path):
            # 업로드
            count = UPLOAD_FUNCS[data_type](file_path, conn)

            # 파일 삭제
            try:
                os.remove(file_path)
            except:
                pass

            # 완료 로그
            log_collection_complete(conn, data_type, target_date, count)
            logger.info(f"[{data_type}] {year}-{str(month).zfill(2)}: {count}건 수집 완료")
            return count
        else:
            log_collection_complete(conn, data_type, target_date, 0)
            logger.warning(f"[{data_type}] {year}-{str(month).zfill(2)}: 데이터 없음")
            return 0

    except Exception as e:
        log_collection_error(conn, data_type, target_date, str(e))
        logger.error(f"[{data_type}] {year}-{str(month).zfill(2)} 오류: {e}")
        return -1


def run_auto_collection(data_types=None):
    """자동 수집 실행"""
    if data_types is None:
        data_types = ['sales', 'purchase', 'production']

    logger.info("="*60)
    logger.info("E-count 자동 데이터 수집 시작")
    logger.info(f"수집 대상: {data_types}")
    logger.info("="*60)

    conn = get_db_connection()
    init_log_table(conn)

    today = datetime.now().date()
    results = {}

    try:
        with EcountBrowser() as browser:
            browser.login()
            time.sleep(3)

            for data_type in data_types:
                logger.info(f"\n{'='*40}")
                logger.info(f"[{data_type.upper()}] 수집 시작")
                logger.info(f"{'='*40}")

                # 마지막 수집 일자 확인
                last_date = get_last_collected_date(conn, data_type)

                # 수집할 월 목록
                months = get_months_to_collect(last_date, today)
                logger.info(f"수집 대상 월: {len(months)}개월")

                total = 0
                for year, month in months:
                    count = collect_month_data(browser, conn, data_type, year, month)
                    if count > 0:
                        total += count

                results[data_type] = total
                logger.info(f"[{data_type}] 총 {total}건 수집 완료")

    finally:
        conn.close()

    logger.info("\n" + "="*60)
    logger.info("수집 완료 요약")
    logger.info("="*60)
    for dtype, count in results.items():
        logger.info(f"  {dtype}: {count}건")

    return results


def show_collection_status():
    """수집 상태 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 로그 테이블 초기화 (없으면 생성)
    init_log_table(conn)

    print("\n" + "="*60)
    print("데이터 수집 현황")
    print("="*60)

    for data_type, cfg in TABLE_CONFIG.items():
        table = cfg['table']
        cur.execute(f'SELECT COUNT(*) as cnt, MIN(date) as min_date, MAX(date) as max_date FROM {table}')
        result = cur.fetchone()
        print(f"\n[{data_type}] {cfg['menu_name']}")
        print(f"  총 레코드: {result['cnt']:,}건")
        print(f"  기간: {result['min_date']} ~ {result['max_date']}")

    # 최근 수집 로그
    print("\n" + "-"*40)
    print("최근 수집 로그 (최근 10건)")
    print("-"*40)

    cur.execute('''
        SELECT data_type, target_date, records_count, status, completed_at
        FROM core.ecount_collection_log
        ORDER BY completed_at DESC NULLS LAST
        LIMIT 10
    ''')

    rows = cur.fetchall()
    if not rows:
        print("  (수집 로그 없음 - 첫 자동 수집 후 기록됩니다)")
    else:
        for row in rows:
            status_icon = "[OK]" if row['status'] == 'completed' else "[ERR]" if row['status'] == 'error' else "[RUN]"
            print(f"  {status_icon} [{row['data_type']}] {row['target_date']}: {row['records_count']}건 ({row['status']})")

    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='E-count 자동 데이터 수집')
    parser.add_argument('--status', action='store_true', help='수집 상태 조회')
    parser.add_argument('--types', nargs='+', choices=['sales', 'purchase', 'production'],
                        help='수집할 데이터 유형 (기본: 전체)')

    args = parser.parse_args()

    if args.status:
        show_collection_status()
    else:
        run_auto_collection(args.types)
