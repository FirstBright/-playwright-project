from playwright.sync_api import sync_playwright
import json
import time

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

def search_and_print(file_path="keywords.txt"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(storage_state="kbid_login.json")
        page = context.new_page()
        
        # KBID 메인 페이지 접속
        page.goto("https://www.kbid.co.kr", wait_until="load")
        print("KBID 접속 완료")

        # txt 파일 한 줄씩 읽기
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                keyword = line.strip()
                if not keyword:
                    continue

                print(f"\n검색: {keyword}")

                # 검색바에 입력
                search_selector = "#s_search_word"  # KBID 검색 input id 확인 필요
                page.fill(search_selector, keyword)
                page.press(search_selector, "Enter")                
                # 검색 결과 로딩 대기
                result_selector = "#listBody1 tr:nth-child(1) td.subject a"  # 제일 위 공고                
                try:
                    page.wait_for_selector(result_selector, timeout=5000)
                except:
                    print("검색 결과 없음")
                    continue

                with page.expect_popup() as popup_info:
                    page.click(result_selector)
                new_tab = popup_info.value
                new_tab.wait_for_load_state("load")
                # 공고 상세 내용 로딩 대기
                detail_selector = ".gongo_detail"
                try:
                    new_tab.wait_for_selector(detail_selector, timeout=50000)
                    detail_elements = new_tab.query_selector_all(detail_selector)
                    if detail_elements:
                        for detail_element in detail_elements:
                            print(detail_element.inner_text().strip())

                        # 상세 페이지에서 이미지 추출 (첫 번째 이미지만)                  
                        # detail_img_element = detail_element.query_selector('img')
                        # if detail_img_element:                            
                        #     detail_screenshot_path = f"{keyword}.png"                            
                        #     detail_img_element.screenshot(path=detail_screenshot_path)
                        #     print(f"상세 페이지 이미지 저장 완료: {detail_screenshot_path}")
                        #     #bid_inner > div.bid_main.analysis_main > div.newTabTy > div:nth-child(4) > div > div > div > div > img:nth-child(1)
                        #     # OCR on the detail page image
                        #     try:
                        #         text_from_detail_image = pytesseract.image_to_string(Image.open(detail_screenshot_path), lang='kor')
                        #         print(f"'{keyword}' 상세 페이지 이미지에서 추출된 텍스트: {text_from_detail_image.strip()}")
                        #     except Exception as e:
                        #         print(f"상세 페이지 OCR 처리 중 오류 발생: {e}")
                        # else:
                        #     print("상세 페이지에서 이미지를 찾을 수 없습니다.")
                    else:
                        print("직접확인 필요.")
                except Exception as e:
                    print(f"상세 페이지 처리 중 오류: {e}")
                finally:
                    new_tab.close() 
                page.goto("https://www.kbid.co.kr", wait_until="load")
                time.sleep(1)  # 다음 검색 전 약간 대기

        browser.close()

# 1회 로그인 상태 저장
#save_login_state()

# 이후 실행
search_and_print()