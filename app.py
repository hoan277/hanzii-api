import json
import urllib.parse
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup

# Thay thế Selenium bằng Playwright
from playwright.sync_api import sync_playwright

app = Flask(__name__)

def crawl_with_playwright(keyword):
    """
    Crawls Hanzii.net for examples using Playwright to handle JavaScript rendering.
    """
    results = []
    if not keyword:
        return results
    
    encoded_keyword = urllib.parse.quote(keyword)
    URL_TO_CRAWL = f"https://hanzii.net/search/example/{encoded_keyword}?hl=vi"
    
    # ----------------------------------------------------------------------
    # KHỞI ĐỘNG PLAYWRIGHT VÀ CHROMIUM HEADLESS
    try:
        with sync_playwright() as p:
            # Base Image đã có Chromium, chỉ cần launch
            browser = p.chromium.launch(headless=True) 
            page = browser.new_page()
            
            page.goto(URL_TO_CRAWL, wait_until='networkidle') 
            
            # Chờ DOM cần thiết xuất hiện (tương đương WebDriverWait)
            page.wait_for_selector('.example-container', timeout=15000) 
            
            html_content = page.content()
            browser.close()
            
            # Dùng BeautifulSoup để phân tích cú pháp DOM đã được render
            soup = BeautifulSoup(html_content, 'html.parser')

            example_container = soup.find('div', class_='example-container')
            if not example_container:
                print("Không tìm thấy khối 'example-container' sau khi render.")
                return results

            example_items = example_container.find_all('div', class_='bg-inverse mb-12')

            for item in example_items:
                # --- 1. Câu Tiếng Trung (e) ---
                cn_div = item.find('div', class_='font-18 fw-400 cl-pr-sm')
                chinese_sentence_wrap = cn_div.find('span', class_='simple-tradition-wrap') if cn_div else None
                
                sentence_cn = ""
                if chinese_sentence_wrap:
                    for content in chinese_sentence_wrap.contents:
                        if content.name == 'span' and 'wrap-convert' in content.get('class', []):
                            break
                        if content.string:
                            sentence_cn += content.string.strip()
                        elif content.name == 'span':
                             sentence_cn += content.get_text(strip=True)
                    sentence_cn = sentence_cn.strip()
                
                # --- 2. Pinyin (p) ---
                pinyin_div = item.find('div', class_='txt-pinyin')
                sentence_pinyin = pinyin_div.get_text(strip=True) if pinyin_div else ""

                # --- 3. Bản Dịch tiếng Việt (m) ---
                viet_container = item.find('div', class_='flex-center space-between font-16 fw-400 cl-pr-sm')
                viet_translation = viet_container.find('div') if viet_container else None
                sentence_vi = viet_translation.get_text(strip=True) if viet_translation else ""
                
                
                if sentence_cn and sentence_pinyin and sentence_vi:
                    results.append({
                        "e": sentence_cn,
                        "p": sentence_pinyin,
                        "m": sentence_vi
                    })
            
            return results

    except Exception as e:
        print(f"Lỗi Playwright (Đảm bảo endpoint/selectors chính xác): {e}")
        return []
    
@app.route('/crawl', methods=['GET'])
def crawl_api():
    """Endpoint API để gọi hàm crawl, nhận keyword qua query parameter."""
    keyword = request.args.get('keyword')
    
    if not keyword:
        return jsonify({"error": "Vui lòng cung cấp keyword"}), 400
        
    print(f"Bắt đầu crawl (Playwright) cho từ khóa: {keyword}")
    data = crawl_with_playwright(keyword)
    print(f"Hoàn thành crawl, trả về {len(data)} ví dụ.")
    
    return jsonify(data) 

if __name__ == '__main__':
    # Chỉ dùng để test local
    app.run(debug=True, host='0.0.0.0', port=5000)
