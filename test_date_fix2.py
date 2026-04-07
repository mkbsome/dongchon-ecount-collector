# -*- coding: utf-8 -*-
"""수정된 날짜 선택 테스트 v2 - 검색 방식 확인"""

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

def test_search_methods():
    """다양한 검색 방법 테스트"""
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
        select_dropdown_value(browser, 0, "year", "2024")
        select_dropdown_value(browser, 0, "month", "01")
        select_dropdown_value(browser, 1, "year", "2024")
        select_dropdown_value(browser, 1, "month", "01")

        # 검색 버튼 분석
        search_info = browser.driver.execute_script('''
            const searchBtns = [];
            // 검색 버튼 찾기
            const allBtns = document.querySelectorAll('button, a, span, div');
            for (const btn of allBtns) {
                const text = btn.textContent.trim();
                if (text === '검색' || text === '조회' || text.includes('Search')) {
                    searchBtns.push({
                        tag: btn.tagName,
                        text: text,
                        id: btn.id,
                        className: btn.className,
                        onclick: btn.getAttribute('onclick')
                    });
                }
            }
            return searchBtns;
        ''')
        logger.info(f"검색 버튼들: {search_info}")

        # 툴바 영역에서 검색 버튼 찾기
        toolbar_search = browser.driver.execute_script('''
            // 메인 툴바의 검색 버튼 찾기
            const toolbar = document.querySelector('.ec-top-toolbar, .toolbar, #toolbar');
            if (toolbar) {
                const searchBtn = toolbar.querySelector('[data-action="search"], .search-btn, button[type="submit"]');
                return searchBtn ? {found: true, tag: searchBtn.tagName, className: searchBtn.className} : {found: false};
            }
            return {found: false, message: 'no toolbar'};
        ''')
        logger.info(f"툴바 검색 버튼: {toolbar_search}")

        # F5 또는 새로고침으로 검색 (일부 시스템은 이 방식)
        # 먼저 현재 URL에 날짜 파라미터가 있는지 확인
        current_url = browser.driver.current_url
        logger.info(f"현재 URL: {current_url}")

        # 직접 조회 버튼 클릭 시도
        logger.info("조회 버튼 직접 클릭 시도...")
        click_result = browser.driver.execute_script('''
            // 조회/검색 버튼 찾기
            const btns = document.querySelectorAll('button, a');
            for (const btn of btns) {
                const text = btn.textContent.trim();
                if (text === '조회' || text === '검색') {
                    btn.click();
                    return {clicked: true, text: text};
                }
            }
            return {clicked: false};
        ''')
        logger.info(f"클릭 결과: {click_result}")

        time.sleep(3)

        # 키보드 Enter로 검색 시도
        logger.info("Enter 키로 검색 시도...")
        from selenium.webdriver.common.keys import Keys
        browser.driver.find_element("tag name", "body").send_keys(Keys.ENTER)
        time.sleep(3)

        # 다운로드 시도
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

if __name__ == "__main__":
    test_search_methods()
