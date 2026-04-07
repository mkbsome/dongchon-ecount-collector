# -*- coding: utf-8 -*-
"""수정된 날짜 선택 테스트"""

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
    """드롭다운에서 값 선택 (메인 페이지에서 실행)"""
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
    """2024-01 날짜 선택 테스트 후 다운로드"""
    with EcountBrowser() as browser:
        browser.login()
        time.sleep(3)

        # 구매현황으로 이동
        browser.reset_to_dashboard()
        browser.go_to_inventory_menu()
        browser.go_to_sub_tab("MENUTREE_000031")
        browser.navigate_to_menu("MENUTREE_000513", "구매현황")
        time.sleep(2)

        logger.info("=== 날짜 설정 테스트: 2024-01 ===")

        # 시작 날짜: 2024-01
        r1 = select_dropdown_value(browser, 0, "year", "2024")
        logger.info(f"시작 년도: {r1}")
        r2 = select_dropdown_value(browser, 0, "month", "01")
        logger.info(f"시작 월: {r2}")

        # 종료 날짜: 2024-01
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

        # 검색 클릭
        logger.info("검색 클릭...")
        browser.click_search()
        time.sleep(3)

        # 다운로드
        download_dir = "C:/Users/mkbso/ecount_downloads"
        before_files = set(glob.glob(os.path.join(download_dir, "*.xlsx")))

        file_path = browser.download_excel()

        if file_path:
            logger.info(f"다운로드 완료: {file_path}")
            # 파일 내용 확인
            import pandas as pd
            df = pd.read_excel(file_path, header=1)
            if len(df) > 0 and '일자-No.' in df.columns:
                first_date = str(df['일자-No.'].iloc[0])
                last_date = str(df['일자-No.'].iloc[-1])
                logger.info(f"데이터 범위: {first_date} ~ {last_date}")
                logger.info(f"행 수: {len(df)}")

                # 2024/01 데이터가 있는지 확인
                jan_2024_rows = df[df['일자-No.'].astype(str).str.startswith('2024/01')]
                logger.info(f"2024/01 데이터 행 수: {len(jan_2024_rows)}")
        else:
            logger.warning("다운로드 실패")

if __name__ == "__main__":
    test_date_selection()
