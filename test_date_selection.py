# -*- coding: utf-8 -*-
"""날짜 선택 테스트 - 2024-01만 선택해서 다운로드"""

import os
import sys
import time
import glob
import logging

from selenium.webdriver.common.by import By

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ecount-collector'))
import config
from browser.ecount import EcountBrowser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def switch_to_content_iframe(browser):
    """컨텐츠 iframe으로 전환"""
    browser.driver.switch_to.default_content()
    try:
        iframe = browser.driver.find_element(By.ID, "s_page")
        browser.driver.switch_to.frame(iframe)
        logger.info("iframe 전환 성공")
        return True
    except Exception as e:
        logger.error(f"iframe 전환 실패: {e}")
        return False

def select_dropdown_value(browser, button_index, data_id, target_value):
    """드롭다운에서 값 선택"""
    logger.info(f"드롭다운 선택: data_id={data_id}, index={button_index}, value={target_value}")

    # 버튼 찾기 확인
    btns_check = browser.driver.execute_script(f'''
        const btns = document.querySelectorAll('button.btn-selectbox[data-id="{data_id}"]');
        return btns.length;
    ''')
    logger.info(f"  버튼 수: {btns_check}")

    # 버튼 클릭
    browser.driver.execute_script(f'''
        const btns = document.querySelectorAll('button.btn-selectbox[data-id="{data_id}"]');
        if (btns[{button_index}]) btns[{button_index}].click();
    ''')
    time.sleep(0.5)

    # 드롭다운 확인
    dropdown_check = browser.driver.execute_script('''
        const dropdown = document.querySelector('.dropdown-menu.show');
        if (dropdown) {
            const items = dropdown.querySelectorAll('li a');
            return Array.from(items).map(i => i.textContent.trim()).join(', ');
        }
        return 'no dropdown';
    ''')
    logger.info(f"  드롭다운 항목: {dropdown_check}")

    # 값 선택
    result = browser.driver.execute_script(f'''
        const dropdown = document.querySelector('.dropdown-menu.show');
        if (dropdown) {{
            const items = dropdown.querySelectorAll('li a');
            for (const item of items) {{
                if (item.textContent.trim() === '{target_value}') {{
                    item.click();
                    return 'clicked: ' + item.textContent.trim();
                }}
            }}
            return 'not found';
        }}
        return 'no dropdown';
    ''')
    logger.info(f"  선택 결과: {result}")
    time.sleep(0.3)

def test_date_selection():
    """2024-01 날짜 선택 테스트"""
    with EcountBrowser() as browser:
        browser.login()
        time.sleep(3)

        # 구매현황으로 이동
        browser.reset_to_dashboard()
        browser.go_to_inventory_menu()
        browser.go_to_sub_tab("MENUTREE_000031")  # 구매관리
        browser.navigate_to_menu("MENUTREE_000513", "구매현황")
        time.sleep(2)

        logger.info("=== iframe 전환 후 날짜 선택 테스트 ===")

        # iframe 전환
        if not switch_to_content_iframe(browser):
            logger.error("iframe 전환 실패!")
            return

        # 2024-01 설정
        select_dropdown_value(browser, 0, "selbox_YY", "2024")
        select_dropdown_value(browser, 0, "selbox_MM", "01")
        select_dropdown_value(browser, 0, "selbox_DD", "01")

        select_dropdown_value(browser, 1, "selbox_YY", "2024")
        select_dropdown_value(browser, 1, "selbox_MM", "01")
        select_dropdown_value(browser, 1, "selbox_DD", "31")

        # 메인 프레임 복귀
        browser.driver.switch_to.default_content()

        logger.info("날짜 설정 완료, 검색 클릭...")
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
        else:
            logger.warning("다운로드 실패")

if __name__ == "__main__":
    test_date_selection()
