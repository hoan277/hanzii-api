# SỬ DỤNG BASE IMAGE DEBIAN ỔN ĐỊNH HƠN (buster hoặc bullseye)
FROM python:3.11-buster

ENV PYTHONUNBUFFERED 1

# Cấu hình Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV NODE_VERSION 18.12.1

WORKDIR /app

# 1. CÀI ĐẶT CÁC THƯ VIỆN HỆ THỐNG
# Chúng ta sẽ cài đặt gói Chromium và các dependency chính
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        # Cài đặt gói Chromium chính thức
        chromium \
        # Các dependency quan trọng khác
        libgbm-dev libxshmfence-dev \
        ca-certificates procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. CÀI ĐẶT THƯ VIỆN PYTHON
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 3. CÀI ĐẶT BROWSER BINARY CỦA PLAYWRIGHT
# Playwright sẽ tìm và sử dụng Chromium đã cài đặt ở bước trên
RUN playwright install chromium

# 4. SAO CHÉP MÃ NGUỒN VÀ KHỞI ĐỘNG
COPY . /app/

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]