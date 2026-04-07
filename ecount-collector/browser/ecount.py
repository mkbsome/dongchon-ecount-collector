# -*- coding: utf-8 -*-
"""
E카운트 ERP 브라우저 자동화
"""

import os
import time
import glob
import logging
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import config
from browser.driver import create_driver, close_driver

logger = logging.getLogger(__name__)


class EcountBrowser:
    def __init__(self):
        self.driver = None

    def start(self):
        """브라우저 시작"""
        self.driver = create_driver()
        return self

    def stop(self):
        """브라우저 종료"""
        close_driver(self.driver)
        self.driver = None

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def login(self):
        """E카운트 로그인"""
        logger.info("Logging in to E-count...")
        self.driver.get(config.ECOUNT_LOGIN_URL)
        time.sleep(2)

        # 회사코드 입력 (첫 번째 텍스트 필드)
        inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
        if len(inputs) >= 2:
            inputs[0].clear()
            inputs[0].send_keys(config.ECOUNT_COMPANY_CODE)
            inputs[1].clear()
            inputs[1].send_keys(config.ECOUNT_USER_ID)

        # 비밀번호 입력
        pw_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        pw_input.clear()
        pw_input.send_keys(config.ECOUNT_PASSWORD)

        # 로그인 버튼 클릭
        login_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '로그인')]")
        login_btn.click()
        time.sleep(3)

        # 새 기기 로그인 알림 처리
        try:
            logger.info("Checking for device registration popup...")
            # 여러 방법으로 '등록안함' 버튼 찾기
            skip_btn = None

            # 방법 1: 정확한 텍스트 매칭
            try:
                skip_btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='등록안함']"))
                )
            except TimeoutException:
                pass

            # 방법 2: contains로 찾기
            if not skip_btn:
                try:
                    skip_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '등록안함')]")
                except NoSuchElementException:
                    pass

            # 방법 3: JavaScript로 찾기
            if not skip_btn:
                result = self.driver.execute_script("""
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const skipBtn = buttons.find(btn => btn.textContent.includes('등록안함'));
                    if (skipBtn) {
                        skipBtn.click();
                        return 'clicked';
                    }
                    // 버튼 목록 반환
                    return 'not found: ' + buttons.map(b => b.textContent.trim()).join(', ');
                """)
                logger.info(f"JS skip button result: {result}")
                if result == 'clicked':
                    time.sleep(2)
                    skip_btn = True  # 이미 클릭됨

            if skip_btn and skip_btn != True:
                skip_btn.click()
                logger.info("Clicked '등록안함' button")
                time.sleep(2)

        except Exception as e:
            logger.warning(f"Device registration popup handling: {e}")

        logger.info("Login successful")
        # 대시보드 로딩 대기
        time.sleep(3)

        # 디버그: 현재 URL 및 페이지 상태 확인
        logger.info(f"Current URL after login: {self.driver.current_url}")
        self._save_debug_screenshot("after_login")

        return True

    def _save_debug_screenshot(self, name: str):
        """디버그용 스크린샷 저장"""
        try:
            screenshot_dir = os.path.join(config.BASE_DIR, "debug")
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, f"{name}_{datetime.now().strftime('%H%M%S')}.png")
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.warning(f"Failed to save screenshot: {e}")

    def wait_for_menu(self, timeout=15):
        """메뉴가 로드될 때까지 대기"""
        logger.info("Waiting for menu to load...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 현재 URL 체크
            current_url = self.driver.current_url
            logger.info(f"Current URL: {current_url}")

            # iframe 체크
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                logger.info(f"Found {len(iframes)} iframes")
                for i, iframe in enumerate(iframes):
                    iframe_id = iframe.get_attribute("id") or "no-id"
                    iframe_src = iframe.get_attribute("src") or "no-src"
                    logger.info(f"  iframe[{i}]: id={iframe_id}, src={iframe_src[:50]}...")

            # 메뉴 요소 체크 (여러 방법)
            result = self.driver.execute_script("""
                // 방법 1: 직접 ID로 찾기
                const directFind = document.getElementById('link_depth1_MENUTREE_000004');
                if (directFind) return { found: true, method: 'direct' };

                // 방법 2: 모든 link_depth1 요소 찾기
                const depth1Links = document.querySelectorAll('[id^="link_depth1"]');
                if (depth1Links.length > 0) {
                    return { found: true, method: 'query', count: depth1Links.length };
                }

                // 방법 3: 메뉴 컨테이너 찾기
                const menuContainer = document.querySelector('.lnb_menu, #menuTree, .menu-tree, nav');
                if (menuContainer) {
                    return { found: false, method: 'container', html: menuContainer.innerHTML.substring(0, 200) };
                }

                // 방법 4: body의 일부 HTML 반환
                return { found: false, bodyPreview: document.body.innerHTML.substring(0, 500) };
            """)

            logger.info(f"Menu check result: {result}")

            if result and result.get('found'):
                self._save_debug_screenshot("menu_found")
                return True

            time.sleep(1)

        # 타임아웃 시 스크린샷 저장
        self._save_debug_screenshot("menu_timeout")
        logger.warning("Menu wait timeout - saving debug info")

        # 전체 페이지 소스 일부 로깅
        page_source = self.driver.page_source[:2000]
        logger.info(f"Page source preview: {page_source}")

        return False

    def go_to_inventory_menu(self):
        """재고 I 탭으로 이동"""
        logger.info("Navigating to 재고 I tab...")

        # 메뉴 로드 대기
        if not self.wait_for_menu():
            logger.warning("Menu not loaded yet, waiting more...")
            time.sleep(3)

        script = """
        const link = document.getElementById('link_depth1_MENUTREE_000004');
        if (link) {
            link.click();
            return 'clicked';
        }
        // 모든 depth1 링크 확인
        const links = Array.from(document.querySelectorAll('[id^="link_depth1"]'));
        return 'not found, available: ' + links.map(l => l.id).join(', ');
        """
        result = self.driver.execute_script(script)
        logger.info(f"Inventory menu result: {result}")
        time.sleep(2)
        return 'clicked' in str(result)

    def go_to_sub_tab(self, tab_menu_id: str):
        """서브 탭으로 이동 (영업관리, 구매관리, 생산/외주)"""
        logger.info(f"Navigating to sub tab: {tab_menu_id}")
        script = f"""
        const link = document.getElementById('link_depth2_{tab_menu_id}');
        if (link) {{
            link.click();
            return true;
        }}
        return false;
        """
        result = self.driver.execute_script(script)
        time.sleep(2)
        return result

    def navigate_to_menu(self, menu_id: str, menu_name: str = None):
        """특정 메뉴로 이동 (판매현황, 구매현황 등)"""
        logger.info(f"Navigating to menu: {menu_name} ({menu_id})")

        # ID로 찾기
        script = f"""
        const link = document.getElementById('link_depth4_{menu_id}');
        if (link) {{
            link.click();
            return true;
        }}
        // 이름으로 찾기
        const links = Array.from(document.querySelectorAll('a'));
        const menuLink = links.find(l => l.textContent.trim() === '{menu_name}');
        if (menuLink) {{
            menuLink.click();
            return true;
        }}
        return false;
        """
        result = self.driver.execute_script(script)
        logger.info(f"Navigate result: {result}")
        time.sleep(2)
        return result

    def click_search(self):
        """검색 버튼 클릭"""
        logger.info("Clicking search button...")
        script = """
        const buttons = Array.from(document.querySelectorAll('button'));
        const searchBtn = buttons.find(btn => btn.textContent.includes('검색'));
        if (searchBtn) {
            searchBtn.click();
            return true;
        }
        return false;
        """
        result = self.driver.execute_script(script)
        logger.info(f"Search click result: {result}")
        # 검색 결과 로딩 대기 (더 긴 시간)
        time.sleep(5)
        return result

    def download_excel(self) -> str:
        """Excel(화면) 버튼 클릭하여 다운로드"""
        logger.info("Downloading Excel...")

        # 실제 다운로드 경로 사용 (driver.py에서 설정됨)
        download_dir = getattr(config, 'ACTUAL_DOWNLOAD_DIR', config.DOWNLOAD_DIR)
        logger.info(f"Using download directory: {download_dir}")

        # 다운로드 전 파일 목록 저장
        os.makedirs(download_dir, exist_ok=True)
        before_files = set(glob.glob(os.path.join(download_dir, "*.xlsx")))
        logger.info(f"Before files count: {len(before_files)}")

        # 데이터 존재 여부 확인
        data_exists = self.driver.execute_script("""
            // 그리드에 데이터가 있는지 확인
            const rows = document.querySelectorAll('.grid-row, .tbl_list tr, tbody tr');
            // 헤더 제외하고 데이터 행이 있는지
            const dataRows = Array.from(rows).filter(r => !r.classList.contains('header'));
            return dataRows.length > 0;
        """)
        logger.info(f"Data exists check: {data_exists}")

        # 현재 윈도우 핸들 저장
        main_window = self.driver.current_window_handle
        window_count_before = len(self.driver.window_handles)

        # Excel 버튼 클릭 - footer toolbar의 Excel(화면) 버튼 사용
        script = """
        // 방법 1: footer toolbar의 Excel 버튼 (가장 정확)
        let excelBtn = document.querySelector('#footer_toolbar_toolbar_item_excel_view button');
        if (excelBtn) {
            excelBtn.click();
            return { clicked: true, text: excelBtn.textContent.trim(), method: 'footer_toolbar' };
        }

        // 방법 2: 화면에 보이는 Excel(화면) 버튼
        const allButtons = Array.from(document.querySelectorAll('button'));
        excelBtn = allButtons.find(btn => {
            const text = btn.textContent.trim();
            return text.includes('Excel') && !text.includes('Email') && btn.offsetParent !== null;
        });
        if (excelBtn) {
            excelBtn.click();
            return { clicked: true, text: excelBtn.textContent.trim(), method: 'visible_button' };
        }

        // 방법 3: 일반 검색
        const elements = Array.from(document.querySelectorAll('button, a, span'));
        excelBtn = elements.find(el => {
            const text = el.textContent.trim();
            return (text === 'Excel(화면)' || text === 'Excel') && !text.includes('Email');
        });
        if (excelBtn) {
            excelBtn.click();
            return { clicked: true, text: excelBtn.textContent.trim(), method: 'general_search' };
        }

        return { clicked: false, buttons: allButtons.filter(b => b.textContent.includes('Excel')).map(b => b.textContent.trim()).join(', ') };
        """
        result = self.driver.execute_script(script)
        logger.info(f"Excel click result: {result}")

        if not result.get('clicked'):
            logger.warning(f"Excel button not found. Available: {result.get('buttons', 'none')}")
            self._save_debug_screenshot("excel_not_found")
            return None

        # 새 창이 열렸는지 확인
        time.sleep(1)
        if len(self.driver.window_handles) > window_count_before:
            logger.info("New window opened, switching to it...")
            for handle in self.driver.window_handles:
                if handle != main_window:
                    self.driver.switch_to.window(handle)
                    time.sleep(2)
                    # 새 창에서 다운로드 트리거가 있을 수 있음
                    self.driver.close()
                    self.driver.switch_to.window(main_window)
                    break

        # 다운로드 완료 대기
        timeout = 15
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 크롬 다운로드 임시 파일 체크 (.crdownload)
            downloading = glob.glob(os.path.join(download_dir, "*.crdownload"))
            if downloading:
                logger.info("Download in progress...")

            current_files = set(glob.glob(os.path.join(download_dir, "*.xlsx")))
            new_files = current_files - before_files
            if new_files:
                new_file = list(new_files)[0]
                logger.info(f"Downloaded: {new_file}")
                time.sleep(1)  # 파일 쓰기 완료 대기
                return new_file
            time.sleep(0.5)

        # 데이터가 없어서 다운로드되지 않았을 수 있음
        if not data_exists:
            logger.info("No data in grid - download may have been skipped")
        else:
            logger.warning("Download timeout - no new file detected")
            self._save_debug_screenshot("download_timeout")

        return None

    def reset_to_dashboard(self):
        """대시보드로 초기화 - 페이지 새로고침으로 완전 리셋"""
        logger.info("Resetting to dashboard...")
        # 현재 URL에서 hash 제거하고 새로고침
        current_url = self.driver.current_url
        base_url = current_url.split('#')[0]
        self.driver.get(base_url)
        time.sleep(3)

        # 메뉴 로드 대기
        self.wait_for_menu(timeout=10)

    def download_report(self, menu_key: str, start_date: datetime, end_date: datetime) -> str:
        """특정 메뉴의 리포트 다운로드"""
        menu_config = config.MENU_CONFIG.get(menu_key)
        if not menu_config:
            raise ValueError(f"Unknown menu key: {menu_key}")

        logger.info(f"=== Downloading report: {menu_config['name']} ===")

        # 서브탭 ID 매핑
        sub_tab_ids = {
            "영업관리": "MENUTREE_000030",
            "구매관리": "MENUTREE_000031",
            "생산/외주": "MENUTREE_000032"
        }

        # 0. 메뉴 상태 초기화 (이전 메뉴 닫기)
        self.reset_to_dashboard()

        # 1. 재고 I 탭 클릭
        self.go_to_inventory_menu()

        # 2. 서브 탭 클릭
        sub_tab_id = sub_tab_ids.get(menu_config["tab"])
        if sub_tab_id:
            self.go_to_sub_tab(sub_tab_id)

        # 3. 메뉴 이동
        self.navigate_to_menu(menu_config["menu_id"], menu_config["name"])

        # 4. 검색
        self.click_search()

        # 5. Excel 다운로드
        file_path = self.download_excel()

        if file_path:
            # 파일명 변경 - 실제 다운로드 경로 사용
            download_dir = getattr(config, 'ACTUAL_DOWNLOAD_DIR', config.DOWNLOAD_DIR)
            new_name = f"{menu_config['file_prefix']}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
            new_path = os.path.join(download_dir, new_name)
            if os.path.exists(new_path):
                os.remove(new_path)
            os.rename(file_path, new_path)
            logger.info(f"Renamed to: {new_path}")
            return new_path

        return None

    def download_all_reports(self, start_date: datetime = None, end_date: datetime = None):
        """모든 리포트 다운로드"""
        if start_date is None:
            start_date = datetime.now().replace(day=1)
        if end_date is None:
            end_date = datetime.now()

        results = {}
        for menu_key in config.MENU_CONFIG.keys():
            try:
                file_path = self.download_report(menu_key, start_date, end_date)
                results[menu_key] = {"success": True, "file": file_path}
            except Exception as e:
                logger.error(f"Failed to download {menu_key}: {e}")
                results[menu_key] = {"success": False, "error": str(e)}

        return results
