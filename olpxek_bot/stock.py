from asyncache import cached
from cachetools import TTLCache
import httpx
from playwright import async_playwright

from olpxek_bot.naver_stock_api import (
    NaverStockAPI,
    NaverStockData,
)

# 'python -m playwright install'이 필요하다


@cached(TTLCache(maxsize=1, ttl=60 * 5))
async def get_finviz_map_capture() -> bytes:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.newPage(viewport={"width": 1280, "height": 900})
        await page.goto("https://finviz.com/map.ashx")
        await page.screenshot(path="test.png")
        # chart를 감싸는 div#body의 크기가 chart보다 작다.
        # canvas.chart에 margin left,right 가 16이므로 32만큼 더해준다
        # 차트 밑에 info box도 포함할 수 있도록 height도 42만큼 더해준다
        await page.evaluate(
            """() => {
            var elem = document.querySelector('div#body');
            var clientWidth = elem.clientWidth;
            var clientHeight = elem.clientHeight;
            elem.style.width = clientWidth + 32 + 'px';
            elem.style.height = clientHeight + 42 + 'px';

        }"""
        )
        chart_element = await page.querySelector("div#body")
        # await chart_element.screenshot(path='chart.png')
        screenshot = await chart_element.screenshot(type="png")
        await browser.close()
    return screenshot


async def get_stock_day_graph_png(query: str) -> bytes:
    api = await NaverStockAPI.from_query(query)
    stock_data = await api.get_stock_data()
    url = stock_data.day_graph_url
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        return r.content


async def get_stock_candle_graph_png(query: str) -> bytes:
    api = await NaverStockAPI.from_query(query)
    stock_data = await api.get_stock_data()
    url = stock_data.candle_graph_url
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        return r.content


async def get_stock_data(query: str) -> NaverStockData:
    api = await NaverStockAPI.from_query(query)
    return await api.get_stock_data()
