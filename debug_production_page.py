# -*- coding: utf-8 -*-
"""생산입고현황 페이지 날짜 선택 분석"""

import os
import sys
import time
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ecount-collector'))
import config
from browser.ecount import EcountBrowser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_production_page():
    """생산입고현황 페이지 분석"""
    with EcountBrowser() as browser:
        browser.login()
        time.sleep(3)

        # 생산입고현황으로 이동
        browser.reset_to_dashboard()
        browser.go_to_inventory_menu()
        browser.go_to_sub_tab("MENUTREE_000032")  # 생산/외주
        browser.navigate_to_menu("MENUTREE_000534", "생산입고현황")
        time.sleep(2)

        logger.info("=== 생산입고현황 페이지 분석 ===")
        browser.driver.switch_to.default_content()

        # 모든 selectbox 버튼 분석
        buttons_info = browser.driver.execute_script('''
            const btns = document.querySelectorAll('button.btn-selectbox');
            return Array.from(btns).map((btn, i) => ({
                index: i,
                dataId: btn.getAttribute('data-id'),
                text: btn.textContent.trim(),
                className: btn.className
            }));
        ''')

        logger.info(f"selectbox 버튼 수: {len(buttons_info)}")
        for btn in buttons_info:
            logger.info(f"  [{btn['index']}] data-id={btn['dataId']}, text='{btn['text']}'")

        # 날짜 입력 필드 확인
        date_inputs = browser.driver.execute_script('''
            const inputs = document.querySelectorAll('input');
            return Array.from(inputs).filter(inp => {
                const val = inp.value || '';
                const placeholder = inp.placeholder || '';
                const name = inp.name || '';
                const id = inp.id || '';
                return val.match(/\\d{4}/) || placeholder.includes('날짜') ||
                       name.includes('date') || name.includes('Date') ||
                       id.includes('date') || id.includes('Date');
            }).map(inp => ({
                id: inp.id,
                name: inp.name,
                value: inp.value,
                placeholder: inp.placeholder,
                className: inp.className,
                type: inp.type
            }));
        ''')

        logger.info(f"\n날짜 입력 필드:")
        for inp in date_inputs:
            logger.info(f"  {inp}")

        # 모든 data-id 속성 확인
        all_data_ids = browser.driver.execute_script('''
            const elements = document.querySelectorAll('[data-id]');
            return Array.from(elements).map(el => ({
                tag: el.tagName,
                dataId: el.getAttribute('data-id'),
                text: el.textContent.trim().substring(0, 30)
            }));
        ''')

        logger.info(f"\n모든 data-id 속성:")
        for el in all_data_ids:
            if 'date' in el['dataId'].lower() or 'yy' in el['dataId'].lower() or 'mm' in el['dataId'].lower() or 'year' in el['dataId'].lower() or 'month' in el['dataId'].lower():
                logger.info(f"  {el}")

        # 툴바 분석
        toolbar_info = browser.driver.execute_script('''
            const toolbar = document.querySelector('.ec-top-toolbar, .search-bar, .filter-area, [class*="toolbar"]');
            if (toolbar) {
                const inputs = toolbar.querySelectorAll('input, select, button');
                return Array.from(inputs).map(el => ({
                    tag: el.tagName,
                    id: el.id,
                    name: el.name,
                    value: el.value || el.textContent.trim().substring(0, 20),
                    className: el.className.substring(0, 50)
                }));
            }
            return [];
        ''')

        logger.info(f"\n툴바 요소:")
        for el in toolbar_info:
            logger.info(f"  {el}")

if __name__ == "__main__":
    analyze_production_page()
