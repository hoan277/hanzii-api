FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_CHROMIUM_PATH=/ms-playwright/chromium-1107/chrome-linux/chrome
ENV NODE_VERSION 18.12.1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        chromium \
        libnss3 libasound2 libatk-bridge2.0-0 libgconf-2-4 libgbm-dev libxshmfence-dev \
        libgtk-4-1 libgraphene-1.0-0 libgstgl-1.0-0 libgstcodecparsers-1.0-0 libenchant-2-2 libsecret-1-0 libmanette-0.2-0 libgles2 \
        fonts-liberation xdg-utils \
        ca-certificates \
        procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium

COPY . /app/

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]