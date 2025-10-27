import json
import urllib.parse
import os # Dùng để kiểm tra biến môi trường
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup

# Thư viện Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

# Sử dụng webdriver_manager để quản lý ChromeDriver
# Lưu ý: Cần cài đặt gói này trong requirements.txt
from webdriver_manager.chrome import ChromeDriverManager 

app = Flask(__name__)

def crawl_with_selenium(keyword):
    """
    Crawls Hanzii.net for examples of a given keyword using Selenium,
    and returns the result in a list of dicts [{e:'..', p:'..', m:'..'}]
    """
    results = []
    if not keyword:
        return results
    
    encoded_keyword = urllib.parse.quote(keyword)
    URL_TO_CRAWL = f"https://hanzii.net/search/example/{encoded_keyword}?hl=vi"
    
    # ----------------------------------------------------------------------
    # CẤU HÌNH HEADLESS CHO MÔI TRƯỜNG SERVER (RẤT QUAN TRỌNG)
    options = Options()
    options.add_argument('--headless')          # Chạy ẩn
    options.add_argument('--no-sandbox')        # Cần thiết trên môi trường Linux/Container
    options.add_argument('--disable-dev-shm-usage') # Giúp tránh lỗi bộ nhớ
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
    
    # [Tùy chọn] Thiết lập đường dẫn nếu webdriver-manager không hoạt động
    # Dùng cho các môi trường có Chromium đã cài đặt sẵn (như Render)
    # options.binary_location = "/usr/bin/chromium-browser" 
    
    driver = None
    try:
        # Sử dụng ChromeDriverManager.install() để tự động tải xuống driver
        # Nếu Chromium không được cài đặt đúng cách, bước này sẽ thất bại
        service = Service(ChromeDriverManager().install()) 
        driver = webdriver.Chrome(service=service, options=options) 
        
        driver.get(URL_TO_CRAWL)
        
        # CHỜ ĐỢI: Chờ cho đến khi phần tử container của ví dụ được tải hoàn chỉnh (15 giây timeout)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'example-container'))
        )
        
        html_content = driver.page_source
        
        # Dùng BeautifulSoup để phân tích cú pháp DOM đã được render
        soup = BeautifulSoup(html_content, 'html.parser')

        example_container = soup.find('div', class_='example-container')
        if not example_container:
            print("Không tìm thấy khối 'example-container' sau khi render.")
            return results

        # Duyệt qua TỪNG VÍ DỤ: mỗi ví dụ là một khối 'div' có class 'bg-inverse mb-12'
        example_items = example_container.find_all('div', class_='bg-inverse mb-12')

        for item in example_items:
            # --- 1. Câu Tiếng Trung (e) ---
            cn_div = item.find('div', class_='font-18 fw-400 cl-pr-sm')
            chinese_sentence_wrap = cn_div.find('span', class_='simple-tradition-wrap') if cn_div else None
            
            sentence_cn = ""
            if chinese_sentence_wrap:
                # Lặp qua các thành phần con để loại bỏ phần phồn thể (wrap-convert)
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
        print(f"Lỗi Selenium (Đảm bảo Chromium được cài đặt và dependencies đủ): {e}")
        return []
    
    finally:
        if driver:
            driver.quit() # Đảm bảo trình duyệt được đóng

@app.route('/crawl', methods=['GET'])
def crawl_api():
    """Endpoint API để gọi hàm crawl, nhận keyword qua query parameter."""
    keyword = request.args.get('keyword')
    
    if not keyword:
        return jsonify({"error": "Vui lòng cung cấp keyword"}), 400
        
    print(f"Bắt đầu crawl (Selenium) cho từ khóa: {keyword}")
    data = crawl_with_selenium(keyword)
    print(f"Hoàn thành crawl, trả về {len(data)} ví dụ.")
    
    # Trả về JSON, tắt ensure_ascii để giữ tiếng Việt và tiếng Trung
    return jsonify(data) 

if __name__ == '__main__':
    # Chạy cục bộ (local)
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))