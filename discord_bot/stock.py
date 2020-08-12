import asyncio
from typing import Tuple

from asyncache import cached
from cachetools import TTLCache
import httpx
from playwright import async_playwright

# 'python -m playwright install'이 필요하다


@cached(TTLCache(maxsize=1, ttl=60*5))
async def get_finviz_map_capture() -> bytes:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.newPage(viewport={'width': 1280, 'height': 900})
        await page.goto('https://finviz.com/map.ashx')
        await page.screenshot(path='test.png')
        # chart를 감싸는 div#body의 크기가 chart보다 작다.
        # canvas.chart에 margin left,right 가 16이므로 32만큼 더해준다
        # 차트 밑에 info box도 포함할 수 있도록 height도 42만큼 더해준다
        await page.evaluate('''() => {
            var elem = document.querySelector('div#body');
            var clientWidth = elem.clientWidth;
            var clientHeight = elem.clientHeight;
            elem.style.width = clientWidth + 32 + 'px';
            elem.style.height = clientHeight + 42 + 'px';

        }''')
        chart_element = await page.querySelector('div#body')
        # await chart_element.screenshot(path='chart.png')
        screenshot = await chart_element.screenshot(type='png')
        await browser.close()
    return screenshot


async def get_stock_metadata(query: str) -> Tuple[str, str, str, str]:
    url_tmpl = 'https://ac.finance.naver.com/ac?q={query}&q_enc=euc-kr&t_koreng=1&st=111&r_lt=111'  # noqa: E501
    async with httpx.AsyncClient() as client:
        r = await client.get(url_tmpl.format(query=query))
        first_item = r.json()['items'][0][0]
        stock_code, display_name, market, url, reuters_code = first_item
        # NOTE: 모든 값이 list로 감싸져있다
    return (
        reuters_code[0], market[0], display_name[0],
        f'https://m.stock.naver.com{url[0]}'
    )


async def get_stock_info(query: str):
    reuters_code, market, display_name, url = await get_stock_metadata(query)
    pass


# 1일
# https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/day/AAPL.O_end.png?1597143600000
# 일봉
# https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/candle/day/AAPL.O_end.png?1597143600000

def get_stock_graph_day_url(reuters_code: str) -> str:
    url = f'https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/day/{reuters_code}_end.png?1597143600000'  # noqa: E501
    return url


async def get_stock_graph_day(reuters_code: str) -> bytes:
    url = get_stock_graph_day_url(reuters_code)
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        return r.content


async def get_stock_graph_candle(reuters_code: str) -> bytes:
    url = f'https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/candle/day/{reuters_code}_end.png?1597143600000'  # noqa: E501
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        return r.content


async def get_basic_stock_info_world(reuters_code: str):
    basic_info = None
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f'https://api.stock.naver.com/stock/{reuters_code}/basic')
        basic_info = r.json()

    stock_name = basic_info['stockName']
    stock_name_eng = basic_info['stockNameEng']
    close_price = basic_info['closePrice']
    stock_exchange_name = basic_info['stockExchangeType']['name']  # e.g., NYSE
    compare_price = basic_info['compareToPreviousClosePrice']  # 변동값
    compare_ratio = basic_info['fluctuationsRatio'] + '%'  # 변동%
    total_infos = {}
    for total_info in basic_info['stockItemTotalInfos']:
        total_infos[total_info['key']] = total_info['value']
        # code, key, value[,
        #   compareToPreviousPrice[code(2,5), text(상승,하락), name]]
    return (stock_name, stock_name_eng, stock_exchange_name, close_price,
            compare_price, compare_ratio,
            total_infos)


async def get_basic_stock_info_kospi(reuters_code: str):
    # https://m.stock.naver.com/api/item/getOverallHeaderItem.nhn?code=005930
    # json['result']
    # 'lv': 저가
    # 'hv': 고가
    # 'pvc': 전일?
    # 'cr': 변동율%
    # 'cv' 변동값
    # 'nv' 현재가?
    # 시가가 없음 (종합 정보에만 있음)

    # 종합 정보: HTML이라서 파싱해야 함
    # https://m.stock.naver.com/api/html/item/getOverallInfo.nhn?code=091990

    # 일봉
    # https://ssl.pstatic.net/imgfinance/chart/mobile/candle/day/091990_end.png
    # 1일
    # https://ssl.pstatic.net/imgfinance/chart/mobile/day/091990_end.png
    pass
