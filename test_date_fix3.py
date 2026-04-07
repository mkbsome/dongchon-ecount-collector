# -*- coding: utf-8 -*-
"""수정된 날짜 선택 테스트 v3 - 올바른 검색 흐름"""

import os
import sys
import time
import glob
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ecount-collector'))
import config
from browser.ecount import EcountBrowser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def select_dropdown_value(browser, button_index, data_id, target_value):
    """드롭다운에서 값 선택"""
    browser.driver.switch_to.default_content()

    # 버튼 클릭
    browser.driver.execute_script(f'''
        const btns = document.querySelectorAll('button.btn-selectbox[data-id="{data_id}"]');
        if (btns[{button_index}]) btns[{button_index}].click();
    ''')
    time.sleep(0.5)

    # 값 선택
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
            return 'not found';
        }}
        return 'no dropdown';
    ''')
    time.sleep(0.3)
    return result

def test_date_selection():
    """2024-01 날짜 선택 후 검색 및 다운로드"""
    with EcountBrowser() as browser:
        browser.login()
        time.sleep(3)

        # 구매현황으로 이동
        browser.reset_to_dashboard()
        browser.go_to_inventory_menu()
        browser.go_to_sub_tab("MENUTREE_000031")
        browser.navigate_to_menu("MENUTREE_000513", "구매현황")
        time.sleep(2)

        logger.info("=== 날짜 설정: 2024-01 ===")

        # 날짜 설정
        r1 = select_dropdown_value(browser, 0, "year", "2024")
        logger.info(f"시작 년도: {r1}")
        r2 = select_dropdown_value(browser, 0, "month", "01")
        logger.info(f"시작 월: {r2}")
        r3 = select_dropdown_value(browser, 1, "year", "2024")
        logger.info(f"종료 년도: {r3}")
        r4 = select_dropdown_value(browser, 1, "month", "01")
        logger.info(f"종료 월: {r4}")

        # 현재 선택된 값 확인
        current_values = browser.driver.execute_script('''
            const btns = document.querySelectorAll('button.btn-selectbox');
            return Array.from(btns).map(b => b.textContent.trim());
        ''')
        logger.info(f"현재 버튼 값들: {current_values}")

        # browser.click_search() 사용
        logger.info("click_search() 호출...")
        browser.click_search()
        time.sleep(5)  # 충분한 대기

        # 데이터 존재 확인
        data_check = browser.driver.execute_script('''
            const rows = document.querySelectorAll('.grid-row, .tbl_list tr, tbody tr');
            const dataRows = Array.from(rows).filter(r => !r.classList.contains('header'));
            return {count: dataRows.length, hasData: dataRows.length > 0};
        ''')
        logger.info(f"검색 후 데이터: {data_check}")

        # 다운로드
        download_dir = "C:/Users/mkbso/ecount_downloads"
        file_path = browser.download_excel()

        if file_path:
            logger.info(f"다운로드 완료: {file_path}")
            import pandas as pd
            df = pd.read_excel(file_path, header=1)
            if len(df) > 0 and '일자-No.' in df.columns:
                # 날짜별 분포 확인
                df['date_only'] = df['일자-No.'].astype(str).str[:7]
                date_counts = df['date_only'].value_counts().sort_index()
                logger.info(f"월별 데이터 분포:\n{date_counts}")

                # 2024/01 데이터만 있는지 확인
                all_jan_2024 = all(d.startswith('2024/01') for d in df['date_only'] if d != 'nan')
                logger.info(f"2024/01 데이터만 있는지: {all_jan_2024}")
        else:
            logger.warning("다운로드 실패")

if __name__ == "__main__":
    test_date_selection()
