# Sử dụng base image Python chính thức của Docker
# Chọn phiên bản gần với phiên trường của bạn, ví dụ: 3.11-slim
FROM python:3.11-slim

# Thiết lập biến môi trường để đảm bảo rằng đầu ra của lệnh không bị đệm
ENV PYTHONUNBUFFERED 1

# Tạo thư mục làm việc và di chuyển vào đó
WORKDIR /app

# 1. CÀI ĐẶT CÁC THƯ VIỆN HỆ THỐNG (LINUX DEPENDENCIES)
# Đây là bước quan trọng nhất để giải quyết lỗi "Missing libraries"
# Nó bao gồm các thư viện đồ họa và font cần thiết cho Chromium Headless
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        # Thư viện cơ bản cho Playwright
        libnss3 libasound2 libatk-bridge2.0-0 libgconf-2-4 libgbm-dev libxshmfence-dev \
        # Các thư viện mà log của bạn báo thiếu (libgtk, libgraphene, libgst)
        libgtk-4-1 libgraphene-1.0-0 libgstgl-1.0-0 libgstcodecparsers-1.0-0 libenchant-2-2 libsecret-1-0 libmanette-0.2-0 libgles2 \
        # Font và các công cụ tiện ích khác
        fonts-liberation xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. SAO CHÉP MÃ NGUỒN VÀ YÊU CẦU
# Sao chép file requirements trước để tận dụng caching của Docker
COPY requirements.txt /app/

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# 3. CÀI ĐẶT BROWSER BINARY CỦA PLAYWRIGHT
# Đây là lệnh tải xuống Chromium binary
RUN playwright install chromium

# Sao chép toàn bộ mã nguồn ứng dụng (app.py) vào thư mục làm việc
COPY . /app/

# 4. KHỞI ĐỘNG ỨNG DỤNG
# Sử dụng Gunicorn để chạy ứng dụng Flask
# Gunicorn sẽ lắng nghe trên cổng 10000 (cổng mặc định của Render)
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]