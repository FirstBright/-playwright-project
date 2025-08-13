from playwright.sync_api import sync_playwright
import json
import time
import re

# 키워드 설정
keywords_to_check = ["경상남도", "시약제조업", "차량렌트업", "직접생산", "직접 생산", "부산광역시", "대전광역시"]
count_keyword = "제안서"

def save_login_state():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=100,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        context = browser.new_context(
            viewport=None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            permissions=["geolocation"],
        )
        page = context.new_page()
        page.goto("https://www.kbid.co.kr/login/common_login.htm", wait_until="load")
        
        print("로그인 페이지가 열렸습니다. 직접 로그인하고 엔터를 누르세요.")
        input("로그인 후 엔터를 누르면 세션이 저장됩니다.")
        
        context.storage_state(path="kbid_login.json")
        print("로그인 세션 저장 완료: kbid_login.json")
        browser.close()

def search_and_save_results(input_file="keywords.txt", output_file="results.txt"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(storage_state="kbid_login.json")
        page = context.new_page()
        
        # KBID 메인 페이지 접속
        page.goto("https://www.kbid.co.kr", wait_until="load", timeout=30000)
        
        # 결과를 저장할 파일 열기
        with open(output_file, "w", encoding="utf-8") as out_f:
            # txt 파일 한 줄씩 읽기
            with open(input_file, "r", encoding="utf-8") as f:
                for keyword in f:
                    keyword = keyword.strip()
                    if not keyword:
                        continue

                    # 검색바에 입력
                    search_selector = "#s_search_word"
                    page.fill(search_selector, keyword)
                    page.press(search_selector, "Enter")

                    # 검색 결과 로딩 대기
                    result_selector = "#listBody1 tr:nth-child(1) td.subject a"
                    result_text = ""
                    try:
                        page.wait_for_selector(result_selector, timeout=10000)
                    except:
                        result_text = f"{keyword}: 검색 결과 없음"
                        out_f.write(result_text + "\n")
                        continue

                    # 새 탭 열기
                    with page.expect_popup() as popup_info:
                        page.click(result_selector)
                    new_tab = popup_info.value
                    new_tab.wait_for_load_state("networkidle", timeout=30000)

                    # 상세 페이지 로딩
                    detail_selector = ".gongo_detail"
                    try:
                        new_tab.wait_for_selector(detail_selector, timeout=60000)
                        new_tab.wait_for_function(
                            "() => document.querySelector('.gongo_detail')?.innerText?.length > 0",
                            timeout=60000
                        )
                        detail_elements = new_tab.query_selector_all(detail_selector)
                        subject_number = 0
                        matched_keywords = []

                        if detail_elements:
                            for detail_element in detail_elements:
                                text = detail_element.inner_text().strip()
                                time.sleep(1)
                                if not text:
                                    continue
                                if re.search(count_keyword, text):
                                    subject_number += 1
                                # 키워드 검색
                                for kw in keywords_to_check:
                                    if re.search(kw, text) and kw not in matched_keywords:
                                        matched_keywords.append(kw)
                            
                            if not matched_keywords and subject_number == 0:
                                result_text = f"{keyword}: 가능, 직접확인 필요."
                            elif not matched_keywords and subject_number > 0:
                                result_text = f"{keyword}: 가능, 제안서 수: {subject_number}"
                            else:
                                result_text = f"{keyword}: 02 {'. '.join(matched_keywords)}"
                        else:
                            result_text = f"{keyword}: 공고문 이미지형태, 직접확인 필요."
                    except Exception as e:
                        result_text = f"{keyword}: 상세 페이지 처리 중 오류: {e}"
                    finally:
                        new_tab.close()

                    # 결과 기록
                    out_f.write(result_text + "\n")

                    # 다음 검색 준비
                    page.goto("https://www.kbid.co.kr", wait_until="load", timeout=30000)
                    time.sleep(2)

        browser.close()

# 1회 로그인 상태 저장 (필요 시 주석 해제)
# save_login_state()

# 검색 및 결과 저장
search_and_save_results()