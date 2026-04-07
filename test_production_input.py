# -*- coding: utf-8 -*-
"""생산입고현황 날짜 입력 테스트 - input 필드 직접 조작"""

import os
import sys
import time
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ecount-collector'))
import config
from browser.ecount import EcountBrowser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_input_manipulation():
    """input 필드 직접 조작 테스트"""
    with EcountBrowser() as browser:
        browser.login()
        time.sleep(3)

        browser.reset_to_dashboard()
        browser.go_to_inventory_menu()
        browser.go_to_sub_tab("MENUTREE_000032")
        browser.navigate_to_menu("MENUTREE_000534", "생산입고현황")
        time.sleep(2)

        logger.info("=== datepicker 구조 분석 ===")

        # datepicker wrapper 분석
        datepicker = browser.driver.execute_script('''
            const wrapper = document.querySelector('.wrapper-datepicker');
            if (!wrapper) return {error: 'wrapper not found'};

            const inputs = wrapper.querySelectorAll('input');
            const buttons = wrapper.querySelectorAll('button');

            return {
                inputs: Array.from(inputs).map((inp, i) => ({
                    index: i,
                    class: inp.className,
                    value: inp.value,
                    name: inp.name,
                    id: inp.id,
                    type: inp.type
                })),
                buttons: Array.from(buttons).map((btn, i) => ({
                    index: i,
                    class: btn.className.substring(0, 50),
                    text: btn.textContent.trim()
                }))
            };
        ''')
        logger.info(f"datepicker 구조:\n{datepicker}")

        # hidden input에 날짜 직접 설정 시도
        logger.info("\n날짜 값 직접 설정 시도...")
        result = browser.driver.execute_script('''
            const wrapper = document.querySelector('.wrapper-datepicker');
            const inputs = wrapper.querySelectorAll('input');

            // hidden input들 (년/월)
            const yearInputs = [];
            const monthInputs = [];
            const dayInputs = [];

            for (const inp of inputs) {
                if (inp.className.includes('select-direct-input')) {
                    // 이전 값 기반으로 년/월 구분
                    const btn = inp.previousElementSibling;
                    if (btn && btn.tagName === 'BUTTON') {
                        const val = btn.textContent.trim();
                        if (val.length === 4) {  // 년도
                            yearInputs.push(inp);
                        } else if (val.length === 2) {  // 월
                            monthInputs.push(inp);
                        }
                    }
                } else if (inp.className.includes('form-control') && !inp.className.includes('hidden')) {
                    dayInputs.push(inp);
                }
            }

            return {
                yearInputs: yearInputs.length,
                monthInputs: monthInputs.length,
                dayInputs: dayInputs.length
            };
        ''')
        logger.info(f"입력 필드 분석: {result}")

        # 버튼 클릭으로 팝업 열기 테스트
        logger.info("\n버튼 클릭 후 팝업 확인...")
        browser.driver.execute_script('''
            const wrapper = document.querySelector('.wrapper-datepicker');
            const btns = wrapper.querySelectorAll('button.btn-selectbox');
            if (btns[0]) {
                btns[0].click();  // 시작 년도 버튼
            }
        ''')
        time.sleep(1)

        # 팝업/드롭다운 확인
        popup = browser.driver.execute_script('''
            // 모든 동적 요소 찾기
            const allElements = document.querySelectorAll('*');
            const results = [];
            for (const el of allElements) {
                const style = window.getComputedStyle(el);
                if (style.display !== 'none' && style.visibility !== 'hidden') {
                    if (el.className && (
                        el.className.includes('popup') ||
                        el.className.includes('dropdown') ||
                        el.className.includes('list') ||
                        el.className.includes('menu') ||
                        el.className.includes('year') ||
                        el.className.includes('picker')
                    )) {
                        const items = el.querySelectorAll('li, a, div');
                        const hasNumbers = Array.from(items).some(i => /^20\\d{2}$/.test(i.textContent.trim()));
                        if (hasNumbers || items.length > 5) {
                            results.push({
                                tag: el.tagName,
                                class: el.className.substring(0, 80),
                                childCount: items.length,
                                samples: Array.from(items).slice(0, 5).map(i => i.textContent.trim().substring(0, 10))
                            });
                        }
                    }
                }
            }
            return results;
        ''')
        logger.info(f"팝업 요소: {popup}")

        # wrapper 내 버튼의 다음 형제 요소(dropdown) 확인
        dropdown = browser.driver.execute_script('''
            const wrapper = document.querySelector('.wrapper-datepicker');
            const btn = wrapper.querySelector('button.btn-selectbox');
            if (!btn) return null;

            let sibling = btn.nextElementSibling;
            while (sibling) {
                if (sibling.tagName === 'UL' || sibling.tagName === 'DIV') {
                    return {
                        tag: sibling.tagName,
                        class: sibling.className,
                        children: sibling.children.length,
                        content: sibling.textContent.substring(0, 100)
                    };
                }
                sibling = sibling.nextElementSibling;
            }
            return null;
        ''')
        logger.info(f"버튼 형제 요소: {dropdown}")

if __name__ == "__main__":
    test_input_manipulation()
