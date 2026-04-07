# -*- coding: utf-8 -*-
"""생산입고현황 날짜 선택 테스트"""

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

def select_production_date(browser, button_index, target_value):
    """생산입고현황 페이지에서 날짜 선택"""
    browser.driver.switch_to.default_content()

    # 버튼 클릭
    browser.driver.execute_script(f'''
        const btns = document.querySelectorAll('button.btn-selectbox');
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
            return 'not found';
        }}
        return 'no dropdown';
    ''')
    time.sleep(0.3)
    return result

def test_production_date():
    """생산입고현황 2024-01 테스트"""
    with EcountBrowser() as browser:
        browser.login()
        time.sleep(3)

        browser.reset_to_dashboard()
        browser.go_to_inventory_menu()
        browser.go_to_sub_tab("MENUTREE_000032")
        browser.navigate_to_menu("MENUTREE_000534", "생산입고현황")
        time.sleep(2)

        logger.info("=== 생산입고현황 날짜 설정: 2024-01 ===")

        # 버튼 인덱스: 7=시작년, 8=시작월, 9=종료년, 10=종료월
        r1 = select_production_date(browser, 7, "2024")
        logger.info(f"시작 년도: {r1}")
        r2 = select_production_date(browser, 8, "01")
        logger.info(f"시작 월: {r2}")
        r3 = select_production_date(browser, 9, "2024")
        logger.info(f"종료 년도: {r3}")
        r4 = select_production_date(browser, 10, "01")
        logger.info(f"종료 월: {r4}")

        # 현재 버튼 값 확인
        current_values = browser.driver.execute_script('''
            const btns = document.querySelectorAll('button.btn-selectbox');
            return Array.from(btns).slice(7, 11).map(b => b.textContent.trim());
        ''')
        logger.info(f"현재 날짜 버튼 값: {current_values}")

        # 검색
        logger.info("검색 클릭...")
        browser.click_search()
        time.sleep(5)

        # 다운로드
        file_path = browser.download_excel()
        if file_path:
            logger.info(f"다운로드 완료: {file_path}")
            import pandas as pd
            df = pd.read_excel(file_path, header=1)
            if len(df) > 0 and '일자-No.' in df.columns:
                df['date_only'] = df['일자-No.'].astype(str).str[:7]
                date_counts = df['date_only'].value_counts().sort_index()
                logger.info(f"월별 분포:\n{date_counts}")
        else:
            logger.warning("다운로드 실패")

if __name__ == "__main__":
    test_production_date()
