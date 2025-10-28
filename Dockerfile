# Sử dụng base image Playwright có sẵn Node.js và tất cả các trình duyệt (Chromium, Firefox, WebKit)
FROM mcr.microsoft.com/playwright/python:v1.55.0-noble

ENV PYTHONUNBUFFERED 1

# Thiết lập thư mục làm việc
WORKDIR /app

# 1. CÀI ĐẶT THƯ VIỆN PYTHON
# Image này đã có Python, nên bạn chỉ cần cài đặt các thư viện Flask/gunicorn/bs4
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
# Cài đặt trình duyệt Playwright
RUN playwright install
# 2. SAO CHÉP MÃ NGUỒN VÀ KHỞI ĐỘNG
# Copy file app.py và các file khác
COPY . /app/

# Tăng timeout lên 120 giây để Playwright có đủ thời gian hoàn thành
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app:app"], "--timeout", "120"
#