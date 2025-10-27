# Ví dụ cấu trúc file app.py

import json
from playwright.sync_api import sync_playwright
from flask import Flask, request, jsonify
import urllib.parse

app = Flask(__name__)

def crawl_with_playwright(keyword):
    results = []
    if not keyword:
        return results
    
    encoded_keyword = urllib.parse.quote(keyword)
    URL_TO_CRAWL = f"https://hanzii.net/search/example/{encoded_keyword}?hl=vi"
    
    try:
        with sync_playwright() as p:
            # Khởi động trình duyệt Chromium ẩn
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 1. Tải trang
            page.goto(URL_TO_CRAWL, wait_until='networkidle') # Chờ mạng ổn định
            
            # 2. Chờ cho DOM cần thiết xuất hiện
            # Đây là bước quan trọng thay thế cho WebDriverWait trong Selenium
            page.wait_for_selector('.example-container', timeout=10000) 
            
            # 3. Lấy nội dung HTML đã được render đầy đủ
            html_content = page.content()
            
            # Đóng trình duyệt
            browser.close()
            
            # 4. Dùng BeautifulSoup (cần cài bs4) để phân tích HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Tiếp tục logic trích xuất dữ liệu như trong code Selenium trước:
            example_container = soup.find('div', class_='example-container')
            if not example_container:
                return results

            example_items = example_container.find_all('div', class_='bg-inverse mb-12')

            for item in example_items:
                # [Logic trích xuất e, p, m y hệt code Selenium trước đó]
                # ...
                # (Tạm thời bỏ qua logic chi tiết để tập trung vào kiến trúc)
                # ...
                
                # Giả định trích xuất thành công:
                results.append({
                    "e": "câu tiếng Trung",
                    "p": "phiên âm",
                    "m": "bản dịch"
                })

            return results

    except Exception as e:
        print(f"Lỗi Playwright: {e}")
        return []

@app.route('/crawl', methods=['GET'])
def crawl_api():
    keyword = request.args.get('keyword')
    if not keyword:
        return jsonify({"error": "Vui lòng cung cấp keyword"}), 400
        
    data = crawl_with_playwright(keyword)
    return jsonify(data)

if __name__ == '__main__':
    # Chỉ dùng cho local test, trên server sẽ dùng Gunicorn/uWSGI
    app.run(debug=True)