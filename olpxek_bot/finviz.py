from asyncache import cached
from cachetools import TTLCache
from playwright import async_playwright


# 'python -m playwright install'이 필요하다


@cached(TTLCache(maxsize=1, ttl=60 * 5))
async def get_finviz_map_capture() -> bytes:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.newPage(viewport={"width": 1280, "height": 900})
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
        chart_element = await page.querySelector("div#body")
        # await chart_element.screenshot(path='chart.png')
        screenshot = await chart_element.screenshot(type="png")
        await browser.close()
    return screenshot
