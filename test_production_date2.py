# -*- coding: utf-8 -*-
"""생산입고현황 날짜 선택 테스트 v2 - wrapper-datepicker 기반"""

import os
import sys
import time
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ecount-collector'))
import config
from browser.ecount import EcountBrowser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def select_production_date(browser, button_index, target_value):
    """wrapper-datepicker 내의 버튼으로 날짜 선택"""
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
                    return 'selected: ' + item.textContent.trim();
                }}
            }}
            document.body.click();
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

        # wrapper-datepicker 내 버튼: 0=시작년, 1=시작월, 2=종료년, 3=종료월
        r1 = select_production_date(browser, 0, "2024")
        logger.info(f"시작 년도: {r1}")
        r2 = select_production_date(browser, 1, "01")
        logger.info(f"시작 월: {r2}")
        r3 = select_production_date(browser, 2, "2024")
        logger.info(f"종료 년도: {r3}")
        r4 = select_production_date(browser, 3, "01")
        logger.info(f"종료 월: {r4}")

        # 현재 버튼 값 확인
        current_values = browser.driver.execute_script('''
            const wrapper = document.querySelector('.wrapper-datepicker');
            const btns = wrapper.querySelectorAll('button.btn-selectbox');
            return Array.from(btns).map(b => b.textContent.trim());
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

                jan_2024 = df[df['date_only'] == '2024/01']
                logger.info(f"2024/01 데이터 수: {len(jan_2024)}")
        else:
            logger.warning("다운로드 실패")

if __name__ == "__main__":
    test_production_date()
