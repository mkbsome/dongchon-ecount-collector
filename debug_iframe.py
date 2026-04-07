# -*- coding: utf-8 -*-
"""iframe 구조 디버그"""

import os
import sys
import time
import logging

from selenium.webdriver.common.by import By

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ecount-collector'))
import config
from browser.ecount import EcountBrowser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def explore_iframes(browser, depth=0, max_depth=3):
    """iframe 구조 탐색"""
    prefix = "  " * depth

    # 현재 프레임에서 셀렉트박스 버튼 확인
    selbox_count = browser.driver.execute_script('''
        return document.querySelectorAll('button.btn-selectbox').length;
    ''')
    selbox_yy = browser.driver.execute_script('''
        return document.querySelectorAll('button.btn-selectbox[data-id="selbox_YY"]').length;
    ''')
    logger.info(f"{prefix}현재 프레임: selectbox={selbox_count}, selbox_YY={selbox_yy}")

    if selbox_yy > 0:
        # 찾았다! 년도 드롭다운의 현재 값 확인
        current_year = browser.driver.execute_script('''
            const btn = document.querySelector('button.btn-selectbox[data-id="selbox_YY"]');
            return btn ? btn.textContent.trim() : 'not found';
        ''')
        logger.info(f"{prefix}>>> 년도 버튼 발견! 현재 값: {current_year}")
        return True

    if depth >= max_depth:
        return False

    # 하위 iframe 탐색
    iframes = browser.driver.find_elements(By.TAG_NAME, "iframe")
    logger.info(f"{prefix}iframe 수: {len(iframes)}")

    for i, iframe in enumerate(iframes):
        iframe_id = iframe.get_attribute("id") or f"no-id-{i}"
        iframe_name = iframe.get_attribute("name") or "no-name"
        logger.info(f"{prefix}iframe[{i}]: id={iframe_id}, name={iframe_name}")

        try:
            browser.driver.switch_to.frame(iframe)
            found = explore_iframes(browser, depth + 1, max_depth)
            browser.driver.switch_to.parent_frame()
            if found:
                logger.info(f"{prefix}>>> 경로: iframe[{i}] (id={iframe_id})")
                return True
        except Exception as e:
            logger.warning(f"{prefix}iframe[{i}] 전환 실패: {e}")

    return False

def debug_iframe_structure():
    """iframe 구조 분석"""
    with EcountBrowser() as browser:
        browser.login()
        time.sleep(3)

        # 구매현황으로 이동
        browser.reset_to_dashboard()
        browser.go_to_inventory_menu()
        browser.go_to_sub_tab("MENUTREE_000031")
        browser.navigate_to_menu("MENUTREE_000513", "구매현황")
        time.sleep(2)

        logger.info("=== iframe 구조 탐색 ===")
        browser.driver.switch_to.default_content()
        explore_iframes(browser)

if __name__ == "__main__":
    debug_iframe_structure()
