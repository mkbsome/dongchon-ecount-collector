# -*- coding: utf-8 -*-
"""생산입고현황 드롭다운 구조 분석"""

import os
import sys
import time
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ecount-collector'))
import config
from browser.ecount import EcountBrowser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_dropdown():
    """드롭다운 구조 분석"""
    with EcountBrowser() as browser:
        browser.login()
        time.sleep(3)

        browser.reset_to_dashboard()
        browser.go_to_inventory_menu()
        browser.go_to_sub_tab("MENUTREE_000032")
        browser.navigate_to_menu("MENUTREE_000534", "생산입고현황")
        time.sleep(2)

        logger.info("=== 드롭다운 분석 ===")

        # 날짜 버튼 영역 분석
        date_area = browser.driver.execute_script('''
            const btns = document.querySelectorAll('button.btn-selectbox');
            // 버튼 7 (시작 년도)의 부모 요소 분석
            const btn = btns[7];
            if (!btn) return {error: 'button not found'};

            const parent = btn.parentElement;
            return {
                parentTag: parent ? parent.tagName : null,
                parentClass: parent ? parent.className : null,
                parentId: parent ? parent.id : null,
                btnClass: btn.className,
                btnText: btn.textContent.trim(),
                siblings: parent ? Array.from(parent.children).map(c => ({
                    tag: c.tagName,
                    class: c.className.substring(0, 50),
                    text: c.textContent.trim().substring(0, 20)
                })) : []
            };
        ''')
        logger.info(f"날짜 영역 구조: {date_area}")

        # 버튼 클릭 후 변화 확인
        logger.info("\n버튼 7 (시작 년도) 클릭 후 분석...")
        browser.driver.execute_script('''
            const btns = document.querySelectorAll('button.btn-selectbox');
            btns[7].click();
        ''')
        time.sleep(1)

        # 열린 드롭다운/팝업 확인
        dropdowns = browser.driver.execute_script('''
            const results = [];

            // 다양한 드롭다운 패턴 검색
            const patterns = [
                '.dropdown-menu',
                '.dropdown-menu.show',
                '.dropdown',
                '.ec-dropdown',
                '[class*="dropdown"]',
                '[class*="popup"]',
                '[class*="select"]',
                '.open',
                '.show',
                '.ui-menu',
                '.list-group'
            ];

            for (const pattern of patterns) {
                const els = document.querySelectorAll(pattern);
                for (const el of els) {
                    if (el.offsetParent !== null && el.offsetHeight > 0) {
                        results.push({
                            pattern: pattern,
                            tag: el.tagName,
                            class: el.className.substring(0, 80),
                            children: el.children.length,
                            text: el.textContent.trim().substring(0, 100)
                        });
                    }
                }
            }

            return results;
        ''')
        logger.info(f"열린 요소들: {len(dropdowns)}개")
        for d in dropdowns[:10]:
            logger.info(f"  {d}")

        # UL/LI 기반 목록 확인
        lists = browser.driver.execute_script('''
            const uls = document.querySelectorAll('ul');
            const visibleLists = [];
            for (const ul of uls) {
                if (ul.offsetParent !== null && ul.children.length > 0) {
                    const items = Array.from(ul.querySelectorAll('li')).slice(0, 5);
                    if (items.length > 0) {
                        visibleLists.push({
                            class: ul.className.substring(0, 50),
                            itemCount: ul.children.length,
                            samples: items.map(i => i.textContent.trim().substring(0, 20))
                        });
                    }
                }
            }
            return visibleLists;
        ''')
        logger.info(f"\n보이는 UL 목록: {len(lists)}개")
        for l in lists[:5]:
            logger.info(f"  {l}")

if __name__ == "__main__":
    analyze_dropdown()
