import urllib.parse
import asyncio
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import List
import time

app = FastAPI()

# Cho phép CORS (giống Flask CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache để tránh crawl lại
cache = {}
cache_expire_seconds = 3600  # 1h cache

# Giới hạn số lượng trình duyệt đồng thời
MAX_CONCURRENCY = 10
semaphore = asyncio.Semaphore(MAX_CONCURRENCY)


async def crawl_hanzii_examples(keyword: str):
    """Crawl ví dụ Hanzii bằng Playwright (async, nhanh, nhẹ)."""
    keyword = keyword.strip()
    if not keyword:
        return []

    # Kiểm tra cache
    if keyword in cache and time.time() - cache[keyword]["time"] < cache_expire_seconds:
        return cache[keyword]["data"]

    async with semaphore:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
            url = f"https://hanzii.net/search/example/{urllib.parse.quote(keyword)}?hl=vi"

            results = []
            try:
                await page.goto(url, timeout=15000)
                await page.wait_for_selector(".example-container", timeout=10000)

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                container = soup.find("div", class_="example-container")
                if not container:
                    await browser.close()
                    return []

                for item in container.find_all("div", class_="bg-inverse mb-12"):
                    # Chinese sentence
                    cn_div = item.find("div", class_="font-18 fw-400 cl-pr-sm")
                    chinese_sentence_wrap = (
                        cn_div.find("span", class_="simple-tradition-wrap") if cn_div else None
                    )
                    sentence_cn = ""
                    if chinese_sentence_wrap:
                        for content in chinese_sentence_wrap.contents:
                            if content.name == "span" and "wrap-convert" in content.get("class", []):
                                break
                            sentence_cn += (
                                content.get_text(strip=True)
                                if content.name == "span"
                                else (content.strip() if content.string else "")
                            )
                        sentence_cn = sentence_cn.strip()

                    # Pinyin
                    pinyin_div = item.find("div", class_="txt-pinyin")
                    sentence_pinyin = pinyin_div.get_text(strip=True) if pinyin_div else ""
                    #replace [ and ] in pinyin
                    sentence_pinyin = sentence_pinyin.replace("[", "").replace("]", "")

                    # Vietnamese translation
                    viet_container = item.find(
                        "div", class_="flex-center space-between font-16 fw-400 cl-pr-sm"
                    )
                    sentence_vi = (
                        viet_container.find("div").get_text(strip=True)
                        if viet_container
                        else ""
                    )

                    if sentence_cn and sentence_pinyin and sentence_vi:
                        results.append({"e": sentence_cn, "p": sentence_pinyin, "m": sentence_vi})

            except Exception as e:
                print(f"[ERROR] {keyword}: {e}")

            finally:
                await browser.close()

            # Lưu cache
            cache[keyword] = {"data": results, "time": time.time()}
            return results


@app.get("/e")
async def crawl_api(k: List[str] = Query(...)):
    """Endpoint crawl nhiều từ song song."""
    if not k:
        return {"error": "Missing query param ?k=keyword"}

    tasks = [crawl_hanzii_examples(keyword) for keyword in k]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    merged = []
    for res in results:
        if isinstance(res, list):
            merged.extend(res)

    return merged


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)
