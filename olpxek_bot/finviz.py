from asyncache import cached
from cachetools import TTLCache
from playwright.async_api import async_playwright


# 'python -m playwright install'이 필요하다


@cached(TTLCache(maxsize=1, ttl=60 * 5))
async def get_finviz_map_capture() -> bytes:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",  # noqa: E501
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()
        await page.goto("https://finviz.com/map.ashx")
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
        chart_element = await page.query_selector("div#body")
        # await chart_element.screenshot(path='chart.png')
        screenshot = await chart_element.screenshot(type="png")
        await context.close()
        await browser.close()
    return screenshot
