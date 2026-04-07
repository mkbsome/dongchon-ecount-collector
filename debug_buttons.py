# -*- coding: utf-8 -*-
"""버튼 구조 상세 분석"""

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

def analyze_buttons():
    """버튼 구조 분석"""
    with EcountBrowser() as browser:
        browser.login()
        time.sleep(3)

        # 구매현황으로 이동
        browser.reset_to_dashboard()
        browser.go_to_inventory_menu()
        browser.go_to_sub_tab("MENUTREE_000031")
        browser.navigate_to_menu("MENUTREE_000513", "구매현황")
        time.sleep(2)

        logger.info("=== 메인 페이지 버튼 분석 ===")
        browser.driver.switch_to.default_content()

        # 모든 selectbox 버튼 분석
        buttons_info = browser.driver.execute_script('''
            const btns = document.querySelectorAll('button.btn-selectbox');
            return Array.from(btns).map((btn, i) => ({
                index: i,
                dataId: btn.getAttribute('data-id'),
                text: btn.textContent.trim(),
                className: btn.className,
                parentId: btn.parentElement ? btn.parentElement.id : 'no-parent-id'
            }));
        ''')

        logger.info(f"버튼 수: {len(buttons_info)}")
        for btn in buttons_info:
            logger.info(f"  [{btn['index']}] data-id={btn['dataId']}, text='{btn['text']}', parent={btn['parentId']}")

        # 년도 관련 버튼 찾기
        year_buttons = browser.driver.execute_script('''
            const btns = document.querySelectorAll('button.btn-selectbox');
            const yearBtns = [];
            for (const btn of btns) {
                const text = btn.textContent.trim();
                if (text.match(/^20\\d{2}$/)) {
                    yearBtns.push({
                        text: text,
                        dataId: btn.getAttribute('data-id'),
                        id: btn.id
                    });
                }
            }
            return yearBtns;
        ''')

        logger.info(f"\n년도 버튼: {year_buttons}")

        # 월 관련 버튼 찾기
        month_buttons = browser.driver.execute_script('''
            const btns = document.querySelectorAll('button.btn-selectbox');
            const monthBtns = [];
            for (const btn of btns) {
                const text = btn.textContent.trim();
                if (text.match(/^\\d{2}$/) && parseInt(text) <= 12) {
                    monthBtns.push({
                        text: text,
                        dataId: btn.getAttribute('data-id')
                    });
                }
            }
            return monthBtns;
        ''')

        logger.info(f"월 버튼: {month_buttons}")

        # 날짜 입력 필드 확인
        date_inputs = browser.driver.execute_script('''
            const inputs = document.querySelectorAll('input[type="text"]');
            const dateInputs = [];
            for (const inp of inputs) {
                const val = inp.value;
                if (val && val.match(/\\d{4}[\\/-]\\d{2}[\\/-]\\d{2}/)) {
                    dateInputs.push({
                        id: inp.id,
                        name: inp.name,
                        value: val,
                        className: inp.className
                    });
                }
            }
            return dateInputs;
        ''')

        logger.info(f"\n날짜 입력 필드: {date_inputs}")

        # 날짜 관련 모든 요소 확인
        date_elements = browser.driver.execute_script('''
            const elements = [];
            // data-id에 YY, MM, DD가 포함된 요소
            const allElements = document.querySelectorAll('[data-id]');
            for (const el of allElements) {
                const dataId = el.getAttribute('data-id');
                if (dataId && (dataId.includes('YY') || dataId.includes('MM') || dataId.includes('DD') || dataId.includes('date') || dataId.includes('Date'))) {
                    elements.push({
                        tag: el.tagName,
                        dataId: dataId,
                        text: el.textContent.trim().substring(0, 50),
                        className: el.className
                    });
                }
            }
            return elements;
        ''')

        logger.info(f"\n날짜 관련 요소: {date_elements}")

if __name__ == "__main__":
    analyze_buttons()
